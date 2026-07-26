# 2.4 — Auth, Roles, Route Protection · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 2 · **Depends on:** 2.1 · **Blocks:** every browser-gated packet from 3.1 onward

> 0.2 shipped an auth stub returning 501. This replaces it. The pattern is ported from
> mis-tutor, which is proven in a live cohort — with one addition it lacks: **section and
> instance scope on the token**, because this simulation is multi-cohort and mis-tutor
> was not.

---

## 0. Spec Basis

**Read in full:**
- `mis-tutor/backend/app/services/auth.py` — bcrypt via passlib, JWT via python-jose,
  `create_access_token(user_id, role)` with `{sub, role, exp}`, `authenticate_user`
  checking `is_active`
- `mis-tutor/backend/app/api/auth.py` — `/login`, `/staff-login` (role-gated to
  instructor/admin/ta), `/me`; `last_active_at` stamped on login
- `mis-tutor/backend/app/api/deps.py` — `HTTPBearer`, `get_current_user`,
  `require_instructor`, `require_instructor_or_ta`
- `backend/app/api/auth.py` @ main — the 501 stub this replaces
- `backend/app/config.py` @ main — `SECRET_KEY`, `ALGORITHM`,
  `ACCESS_TOKEN_EXPIRE_MINUTES` already present
- `handoffs/2.1-hierarchy/spec.md` §5.1 — `Enrollment` binds user to section

**Extraction sufficiency:** covered. All three mis-tutor auth files read in full.

---

## 1. Purpose and scope

**In scope:** `User` model completion; password hashing; JWT issue and decode; `/login`,
`/staff-login`, `/me`; the dependency guards; **section/instance resolution** so a student
request knows which instance it belongs to; applying guards to 2.1's routes.

**Out of scope:**
- Any UI, including a login screen — 3.1
- Password reset, email, SSO
- Rate limiting *(flagged in §10 as a known gap, not built here)*
- Instructor roster management — 5.2
- Changing 2.1's models beyond the `User` fields named in §5.1

---

## 2. Project-specific statements

**Scoring factors touched:** none. It gates access to all of them.
**Casepack keys read:** none.
**Instance scoping:** **this packet resolves it.** `get_current_instance` derives the
caller's instance from their enrollment; every downstream route uses it to construct
2.2's `ScopedRepo`. A student who supplies another instance's id gets 403, not empty
results — invariant I4.
**Business-language check:** `"Invalid credentials"` and `"Instructor access required"`
are acceptable; nothing exposes a stack trace or a field name.

---

## 3. Settled decisions

1. **Port mis-tutor's pattern**: passlib/bcrypt, python-jose JWT, `HTTPBearer`. All four
   dependencies are already pinned in 0.2's `requirements.txt`.
2. **Token payload gains `instance_id`** alongside `sub` and `role`. mis-tutor had no
   instance layer; carrying it avoids a lookup on every request.
3. **Separate `/staff-login`**, as mis-tutor. A staff route that rejects students by role
   is worth the duplication.
4. **Roles:** `student · ta · instructor · admin`.
5. **`get_current_instance` is a dependency, not a query parameter.** A route that takes
   `instance_id` from the client is a route that leaks — I4.
6. **Stub removal is total.** No path returns 501 after this packet.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

```
1  User model: id, student_id UNIQUE, name, email, role, password_hash,
   is_active, last_active_at
2  services/auth.py — ported verbatim from mis-tutor, plus instance_id in the payload
3  api/deps.py:
       get_current_user()        → User        (from bearer token)
       get_current_instance()    → int         (from token, cross-checked against
                                                Enrollment; 403 on mismatch)
       require_instructor()      → User
       require_instructor_or_ta()→ User
4  api/auth.py replaces the 501 stub with /login, /staff-login, /me
5  2.1's routes gain Depends(require_instructor) or Depends(get_current_user)
```

I1 (no 501 remains), I2 (no route accepts a client-supplied instance id), I3 (no plaintext
password anywhere), and I4 (cross-instance access is 403) are all satisfied by this
arrangement — step 3's cross-check is what makes I2 and I4 compatible rather than
contradictory.

---

## 5. Design

### 5.1 `User`

2.1 pre-flight row 4 may already have created a minimal `User`. This packet completes it:
`id · student_id UNIQUE · name · email · role · password_hash · is_active ·
last_active_at · created_at`. If 2.1 created it, **extend, do not recreate.**

### 5.2 Token

```json
{"sub": "<user_id>", "role": "student", "instance_id": 7, "exp": "…"}
```

`instance_id` is null for instructors and admins, who are not bound to one instance.
For a student it is resolved at login from their active `Enrollment`.

### 5.3 Dependencies

```
get_current_user            401 on bad/expired token, or inactive user
get_current_instance        student → token's instance_id, cross-checked against a live
                                      Enrollment; mismatch or missing → 403
                            instructor/admin → resolved from the route's section context
require_instructor          403 unless instructor|admin
require_instructor_or_ta    403 unless instructor|admin|ta
```

### 5.4 Null paths and negative cases

| Case | Expected | Verify |
|---|---|---|
| Unknown `student_id` | 401 `"Invalid credentials"` — same message as wrong password | assert identical response |
| Correct password, `is_active` false | 401, same message | curl |
| Student hits `/staff-login` | 403 `"This login is for instructors and TAs only"` | curl |
| Expired token | 401 `"Invalid token"` | forge a past `exp` |
| Token for a deleted user | 401 | delete, then call `/me` |
| Student enrolled in two sections | Token carries the **active** enrollment; if two are active, 409 naming both | fixture |
| Student with no enrollment | Login succeeds, `instance_id` null; any instance-scoped route → 403 | curl |
| Any request supplying `?instance_id=` | Ignored. Never read | I2 |

Row 1 matters: distinguishing "no such user" from "wrong password" is a user-enumeration
leak.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No 501 stub remains | `grep -rn "501\|Not implemented" backend/app/api/` | zero |
| I2 | No route reads a client-supplied instance id | `grep -rnE "instance_id.*(Query\|Path\|Body)\|request.*instance_id" backend/app/api/` | zero |
| I3 | No plaintext password stored or logged | `grep -rnE "password" backend/app --include=*.py \| grep -viE "password_hash\|hash_password\|verify_password\|LoginRequest\|body.password"` | zero |
| I4 | Cross-instance access is 403 | test: student of instance A requests a route resolving instance B | 403, not 200-with-empty |
| I5 | Same message for unknown user and wrong password | test both | byte-identical bodies |
| I6 | `SECRET_KEY` is not the 0.2 default in any committed env | `grep -rn "dev-secret-key-change-in-production" .env.example backend/` | present **only** in `.env.example` |
| I7 | Auth canary passes | login via browser + one authenticated API call on the same host pair | passes |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.2's auth stub returns 501 on every method | `[V]` | `grep -n "501" backend/app/api/auth.py` | present |
| 2 | `python-jose`, `passlib`, `bcrypt`, `python-multipart` are pinned | `[V]` | `grep -nE "jose\|passlib\|bcrypt\|multipart" backend/requirements.txt` | all four |
| 3 | `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` in config | `[V]` | `grep -n "SECRET_KEY\|ALGORITHM\|ACCESS_TOKEN" backend/app/config.py` | all three |
| 4 | 2.1 merged; `Enrollment` exists | `[V]` | `psql -c "\d enrollment"` | present |
| 5 | Whether 2.1 created a `User` model | `[V]` | `grep -rn "class User" backend/app/models/` | **extend if present, create if not — report which** |
| 6 | **Nothing out of scope depends on the 501 stub's behaviour** *(§4.2)* | `[V]` | `grep -rn "auth/login\|501" backend/ frontend/src --include=*.py --include=*.jsx` | zero outside `api/auth.py` — proves replacing it breaks nothing |
| 7 | No frontend login exists to break | `[V]` | `grep -rn "login\|Login" frontend/src` | zero — 3.1 builds it |

---

## 8. Build steps

1. **`User` model** (extend or create per row 5) + migration. *Verify:* migration
   up/down/up.
2. **Port `services/auth.py`**, adding `instance_id` to the payload. *Verify:* I3; a
   round-trip encode/decode test.
3. **`deps.py`** with the four dependencies incl. `get_current_instance`. *Verify:* I2, I4.
4. **Replace the stub** with `/login`, `/staff-login`, `/me`. *Verify:* I1, I5; every
   §5.4 row, output pasted.
5. **Guard 2.1's routes.** *Verify:* an unauthenticated create-course is 401; a student
   create-course is 403.
6. **Auth canary.** *Verify:* I7 — browser login plus one authenticated call on the same
   app-host/API-host pair (`GOVERNANCE.md §5`).

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. rows 5 and 6 | | |
| Steps 1–6 verified | | |
| I1–I7 | | |
| All eight §5.4 null/negative rows | | |
| **Auth canary** | | **PASS required — this packet is where it becomes real** |
| Instance-isolation canary still passes | | |
| `CONTRACTS.md` — token payload entry added | | |
| Browser canaries | | **N-A** beyond the auth canary; no UI until 3.1 |

---

## 10. Known gaps, deliberately not built

**No rate limiting on `/login`.** Brute force is unmitigated. Acceptable for a cohort
behind institutional network access; **not** acceptable if this is ever exposed publicly.
Record as an accepted risk in `SECURITY.md` with the re-check trigger *"before any
internet-facing deployment."* A builder that adds rate limiting here is out of scope —
report it instead.

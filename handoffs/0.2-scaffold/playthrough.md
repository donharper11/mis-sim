# 0.2 — Playthrough Script

**Authored by:** Claude (design session) · **Date:** 2026-07-26 · **Before any code:** yes
**Spec:** `spec.md` in this folder
**Executed by:** AUDITOR, in a real browser, from a clean checkout.

> **Adaptation note.** 0.2 ships no student screens, so Part B (the negligent path) is
> replaced by a **clean-clone path** — the failure this module actually risks is "works
> on the builder's machine." Everything here starts from `git clone`, not from the
> builder's working tree.

---

## Setup

```
Start from:  a fresh `git clone` of donharper11/mis-sim into a new directory.
             Do NOT use the builder's working tree.
Prereqs:     docker + compose, node ≥18, python ≥3.12
Env:         cp .env.example .env   (no edits)
```

---

## Part A — a developer gets it running

| # | Action | EXPECT | Shot |
|---|---|---|---|
| A1 | `git clone … && cd mis-sim && cp .env.example .env` | `.env.example` exists and needs no editing to boot | ☐ |
| A2 | `docker compose up -d` | api and db both reach healthy. No crash loop | ☐ |
| A3 | `curl -s localhost:8000/api/health` | `{"status":"ok"}` | ☐ |
| A4 | `docker compose exec api alembic current` | baseline revision shown, no error | ☐ |
| A5 | `docker compose exec api alembic upgrade head` | exits 0, idempotent on re-run | ☐ |
| A6 | `cd frontend && npm ci && npm run build` | exits 0, zero errors | ☐ |
| A7 | `npm run dev`, open `http://localhost:3000/_dev/tokens` | Token swatch grid renders. Every swatch labelled with variable name and value | ☐ |
| A8 | Inspect the page — Button, Select, Table | All three are Ant Design components and visibly inherit the theme: **zero border radius**, IBM Plex Sans, BECSR navy primary | ☐ |
| A9 | Open the browser console | **zero errors, zero warnings from our code** | ☐ |
| A10 | Confirm the one `t()`-rendered string displays | English string renders; no raw key like `dev.tokens.title` visible | ☐ |

---

## Part B — clean-clone and degraded paths

| # | Action | EXPECT | Shot |
|---|---|---|---|
| B1 | `docker compose stop db`, then restart api | API **starts**. `/api/health` returns 200 with `{"status":"degraded","db":"unreachable"}`. Process does not crash | ☐ |
| B2 | `docker compose start db`, curl health again | back to `{"status":"ok"}` without an api restart | ☐ |
| B3 | `mv .env .env.bak && docker compose up` | Boots on declared defaults. No stack trace | ☐ |
| B4 | `curl -i localhost:8000/api/auth/login` | HTTP **501**, body `{"detail":"Not implemented — module P4"}` | ☐ |
| B5 | Visit `http://localhost:3000/nonsense` | A plain 404 view. **Not** a blank white screen, not a stack trace | ☐ |
| B6 | Fresh volume (`docker compose down -v && up -d`), curl health before running any migration | `{"status":"ok"}` — health does not depend on schema | ☐ |
| B7 | `git status` after a full boot + build | clean. No generated files, no `.env`, no secrets untracked-but-present | ☐ |

---

## Part C — viewports and states

| # | Check | EXPECT | Shot |
|---|---|---|---|
| C1 | `/_dev/tokens` at 1440 | No overlap, no clipping, no horizontal scroll | ☐ |
| C2 | at 1280 | same | ☐ |
| C3 | at 1024 | same | ☐ |
| C4 | Loading state (throttle to Slow 3G) | No layout jump, no flash of unstyled content | ☐ |
| C5 | Backend down, reload `/_dev/tokens` | Page still renders — it must not depend on the API | ☐ |

---

## Part D — invariants, run by the auditor independently

Do not trust the builder's paste. Run each yourself from the clean clone.

| # | Check | EXPECT |
|---|---|---|
| D1 | `grep -rniE "#[0-9a-f]{3,8}\|font-family" frontend/src --include=*.jsx --include=*.js --include=*.css \| grep -v "styles/theme.css"` | zero hits |
| D2 | `grep -rn "create_all" backend/` | zero hits |
| D3 | `grep -rniE "riverside\|grocer\|casepack" backend/ frontend/src/` | zero hits |
| D4 | Read every file in `backend/alembic/versions/` | one baseline revision, empty upgrade body |
| D5 | `grep -rn "_dev/tokens" frontend/src/ \| grep -v "pages/DevTokens\|App.jsx"` | zero hits — not linked from navigation |
| D6 | `grep -rn "tailwind" frontend/` | zero hits |
| D7 | `git log --all --format=%H -S"password" -- .env` and `git ls-files \| grep -x ".env"` | `.env` not tracked; no secrets in history |

---

## Part E — spec compliance

| # | Check | EXPECT |
|---|---|---|
| E1 | Out-of-scope list in `spec.md §1` | **Nothing built beyond it.** No domain models, no product screens, no component library, no AI services, no casepack code. A helpful extra is a finding |
| E2 | `dod.md` — every row filled | No blank rows. Any `N-A` carries a stated reason |
| E3 | Open decisions O1, O2, O3 | Each resolved, with the choice and rationale recorded in `dod.md` |
| E4 | O1 specifically | If globalstrat's palette was chosen over BECSR's, a `GOVERNANCE.md` amendment with a version bump must accompany it. Palette change without amendment = **Blocking** |
| E5 | Governance docs and `design/` at root | Unmoved, unrenamed, unedited |

---

## Result

```
Run date:            Auditor:
Steps passed:    /            Console errors:
Findings filed:  findings/0.2-YYYY-MM-DD.md
Verdict:  PASS / FAIL
```

A single blocking finding = FAIL. Return to a builder with the findings file.

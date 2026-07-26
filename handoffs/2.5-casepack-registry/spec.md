# 2.5 — Casepack Loader & Registry · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 2 · **Depends on:** 1.1, 1.2, 2.1 · **Blocks:** 5.1, 5.6, 6.1

> 1.1 parses a pack from disk. This makes packs **available to the platform**: registered,
> versioned, validated on registration, and bound to an instance — so two sections can run
> different verticals at once.

---

## 0. Spec Basis

**Read in full:**
- `handoffs/1.1-casepack-schema/spec.md` §5 (pack layout), §8 phase 3 (the loader)
- `handoffs/1.2-validator/spec.md` §5 (severities, exit codes, `--json` mode)
- `handoffs/2.1-hierarchy/spec.md` §5.1 (`simulation_instance.scenario_id`,
  `scenario_version`, `settings`)
- `CONTRACTS.md` — casepack identifiers (`pack_key` stable forever, `pack_version` semver;
  engine never branches on `pack_key`)
- `GOVERNANCE.md` §4.6, §5 (the validator gate)

**Extraction sufficiency:** covered.

---

## 1. Purpose and scope

**In scope:** a `casepack` registry table; a register command that validates before
accepting; an in-process cache so a pack is parsed once per process; binding an instance
to a pack version; the read API 5.1 and 5.6 will call.

**Out of scope:**
- The schema and parser — 1.1
- The validation rules — 1.2 (this *invokes* the validator, it does not reimplement it)
- Authoring any pack content — 1.3, 6.1
- Instructor UI — 5.1, 5.6
- Editing packs through the platform. **Packs are files.** Registration is one-way

---

## 2. Project-specific statements

**Scoring factors touched:** none. It supplies the authored inputs to all of them.
**Casepack keys read:** all — this is the packet that reads them.
**Casepack-identity branching:** none. Registration is generic over `pack_key` — I1. This
is a direct rehearsal of the Phase 6 gate.
**Instance scoping:** `casepack` rows are **platform-level, not instance-scoped** — one
registered pack serves many instances. `simulation_instance.scenario_id` +
`scenario_version` is the binding. Explicit, because it is the one table in Phase 2 that
correctly has no `instance_id`.
**Business-language check:** registration output is instructor-facing; it reports pack
display names, never directory paths.

---

## 3. Settled decisions

1. **Validate on registration, refuse on ERROR.** `GOVERNANCE.md §5`: no pack reaches a
   section until the validator passes clean. WARN registers and is stored.
2. **Registration is immutable per version.** Re-registering the same
   `(pack_key, pack_version)` is refused. Content changes need a version bump — otherwise
   a running cohort's content shifts under it.
3. **An instance binds to `(pack_key, pack_version)`,** never to `pack_key` alone. A
   mid-semester registration of a new version must not affect a running section.
4. **Packs are parsed once per process** and cached by `(key, version)`. Parsing ~2,000
   preference rows on every request is unacceptable.
5. **The registry stores metadata, not content.** Content stays on disk; the DB holds
   identity, version, path, validation result, and registration time. *(Storing parsed
   content in the DB creates a second source of truth that will drift from the files.)*

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

```
1  Migration: casepack(id, pack_key, pack_version, schema_version, display_name,
       vertical, rounds, path, validation_json, registered_at,
       UNIQUE(pack_key, pack_version))
       — no instance_id: platform-level by design

2  register_casepack(path):
       loader = 1.1's loader          → typed Casepack   (raises on parse failure)
       result = 1.2's validator       → severities
       if any ERROR: refuse, print the validator's own output, exit non-zero
       else: INSERT, storing validation_json

3  registry.get(pack_key, pack_version) -> Casepack
       in-process dict cache keyed by (key, version); miss → loader → cache

4  instance_service.bind(instance, pack_key, pack_version)
       refuses if the pack is unregistered
       refuses if the instance has advanced past round 0
```

I1 (no identity branching) holds because every function takes `pack_key` as data. I3
(single source of truth) holds because step 1 stores no content. I4 (immutability) holds
via the unique constraint plus step 2's refusal.

---

## 5. Design

### 5.1 Registry table

```
casepack   id · pack_key · pack_version · schema_version
           display_name · vertical · rounds
           path · validation_json · registered_at · registered_by
           UNIQUE(pack_key, pack_version)
```

### 5.2 Commands and API

```
register_casepack <path>              validate, then register. Non-zero on ERROR
list_casepacks [--json]               registry contents with validation summary
registry.get(key, version)            cached typed Casepack
instance_service.bind(...)            per §4 step 4
```

### 5.3 Null paths and negative cases

| Case | Expected | Verify |
|---|---|---|
| Path is not a pack directory | Refuse, naming what is missing | `register_casepack /tmp/empty` |
| Pack has validator ERRORs | Refuse, print the validator's output verbatim, exit 1 | broken fixture |
| Pack has only WARNs | Register; store warnings; print them | warn fixture |
| Re-register same key+version | Refuse: *"already registered; bump `pack_version`"* | register twice |
| Register a new version of a bound pack | Succeeds. Running instances are unaffected | bind v1, register v2, assert instance still on v1 |
| Bind an unregistered pack | Refuse, naming the pack | curl |
| Bind after the instance has advanced | Refuse: content must not change mid-game | advance, then bind |
| Pack file edited on disk after registration | **Not detected.** Documented, not guarded — see §8 | — |
| Two instances bind the same pack version | Both succeed, share the cache entry | fixture |

### 5.4 Cache invalidation

The cache is per process and keyed by `(pack_key, pack_version)`. Because registration is
immutable per version, **no invalidation is needed** — a version's content never changes
legitimately. Editing a registered pack's files on disk is a deployment error, and §8
covers it.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No branching on pack identity | `grep -rniE "riverside\|grocer\|pack_key *==" backend/app/casepack/registry.py backend/app/services/` | zero |
| I2 | Registration invokes 1.2's validator, does not reimplement it | `grep -n "import\|from" backend/app/casepack/registry.py \| grep -i valid` | imports the validator module |
| I3 | Registry stores no pack content | `psql -c "\d casepack"` | no column holding capabilities/catalog/preferences |
| I4 | `(pack_key, pack_version)` unique | `psql -c "\d casepack"` | unique index present |
| I5 | `casepack` carries no `instance_id` | `psql -c "\d casepack"` | absent — deliberate, per §2 |
| I6 | An ERROR pack cannot be registered | register the broken fixture | non-zero exit, no row inserted |
| I7 | Pack parsed once per process | instrument the loader, call `registry.get` 100× | one parse |
| I8 | Migration reversible | `alembic upgrade head && downgrade -1 && upgrade head` | exits 0 |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 merged; loader parses a pack directory | `[V]` | `python -m app.casepack.loader packs/riverside_grocery` | no exception |
| 2 | 1.2 merged; validator exits non-zero on ERROR | `[V]` | `validate_casepack backend/tests/fixtures/packs/<broken>; echo $?` | 1 |
| 3 | 1.2 exposes `--json` | `[V]` | `validate_casepack --json packs/riverside_grocery \| python -m json.tool` | valid JSON |
| 4 | 2.1 merged; `simulation_instance` has `scenario_id` and `scenario_version` | `[V]` | `psql -c "\d simulation_instance"` | both columns |
| 5 | **Nothing out of scope reads packs from disk directly** *(§4.2)* | `[V]` | `grep -rn "packs/" backend/app --include=*.py \| grep -v "casepack/"` | zero — proves routing all access through the registry breaks nothing |
| 6 | Riverside validates clean | `[V]` | `validate_casepack packs/riverside_grocery; echo $?` | 0 |
| 7 | A second pack exists to test multi-pack | `[A]` | `ls packs/` | **likely only Riverside → build a minimal synthetic second pack as a fixture; report** |

Row 7 matters: a registry tested with one pack is not tested.

---

## 8. Build steps

1. **Migration + model.** *Verify:* I3, I4, I5, I8.
2. **`register_casepack`** invoking 1.2. *Verify:* I2, I6; §5.3 rows 1–4.
3. **Cached `registry.get`.** *Verify:* I7.
4. **`instance_service.bind`.** *Verify:* §5.3 rows 5–9.
5. **Two-pack fixture** (pre-flight row 7) registered simultaneously and bound to 2.1's
   two sections. *Verify:* both resolve independently; the isolation canary still passes.
6. **Document the on-disk-edit gap** in `docs/casepack-operations.md`: registered packs are
   read from disk at parse time; editing a registered pack's files without a version bump
   silently changes content for the next process start. Operational rule: **packs are
   append-only once registered.**

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. row 7 | | |
| Steps 1–6 verified | | |
| I1–I8 | | |
| All nine §5.3 null/negative rows | | |
| Two packs registered and bound to two sections | | |
| Instance-isolation canary still passes | | |
| `docs/casepack-operations.md` incl. the append-only rule | | |
| Auth canary | | required if any route added; **N-A** if command-line only — state which |
| Browser canaries | | **N-A** — no UI |

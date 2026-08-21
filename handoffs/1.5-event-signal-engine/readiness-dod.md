# 1.5 readiness closeout — builder Definition of Done

**Builder branch:** `build/1.5-readiness`
**Input revision:** `1fe81c9405e640605254bcd9967a61a3ed8ec15a`
**Required base:** `cedd61fc378f54c769398d719471e307f9a0959c`

## Pre-flight

| Check | Status | Evidence |
|---|---|---|
| Required main revision | PASS | `git rev-parse --verify main` → `cedd61fc378f54c769398d719471e307f9a0959c` |
| Ten-field pre-closeout model | PASS | `sed -n '/class EventPrecondition/,/class EventOutcome/p' ...` showed the ten existing fields and no `placement` / `other_policy` |
| Flat W08 baseline | PASS | `grep -n W08_MIN_DRAWS ...` showed constant `6` and both consumers |
| Riverside clean baseline | PASS | validator: `0 errors · 0 warnings · exit 0` |

## Verification and DoD

| Item | Status | Evidence |
|---|---|---|
| Both fields load and round-trip | PASS | `PYTHONPATH=. python3 tests/check_event_preconditions.py` — explicit combined round-trips for `placement`+`count` and `policy`+`other_policy` |
| All eleven valid shapes load and validate | PASS | same focused script — canonical-set equality plus table-driven model and exact-shape checks |
| Unknown type rejected | PASS | `broken_E29` fixture raises stable `E29`, exit 1; fixture matrix PASS |
| Missing required field rejected | PASS | focused script removes one required field from each of eleven types; all PASS |
| Field from another type rejected | PASS | focused table adds a foreign field to each of eleven types; all PASS |
| W08 uses `pack.metadata.rounds` | PASS | `PYTHONPATH=. python3 tests/check_w08_rounds.py` — four draws pass and three draws warn with minimum 4 |
| Empty affinity semantics unchanged | PASS | same script — global card counts for W08 and still emits W03 |
| Existing validator contract preserved | PASS | `check_fixture_matrix.py`: all 43 fixtures PASS; I1 38/38 set equality; I5 text/JSON parity PASS |
| Riverside remains clean | PASS | text validator `0 errors · 0 warnings · exit 0`; JSON output `[]` |
| Full backend suite | PASS | `PYTHONPATH=. pytest -q` → `35 passed`; all `tests/check_*.py` scripts PASS |
| Static quality | PASS | `ruff check` on changed Python files; `git diff --check` |
| Scope | PASS | no files under `backend/app/engine/` changed; no signals, events, metrics, blast radius, or seed history implemented |

## Verification ladder

| Rung | Status | Evidence / reason |
|---|---|---|
| 1 — contract | PASS | Inspected the live model, validator producer/catalogue, fixture matrix, schema guide, 1.2 spec, and `CONTRACTS.md` placement vocabulary before editing |
| 2 — implementation | PASS | Ruff, focused checks, 43-fixture matrix, 35-test pytest suite, Riverside text/JSON validation |
| 3 — runtime | N/A | Pure casepack schema/validator prerequisite; no database, seed, service, auth, or runtime state |
| 4 — browser diagnostics | N/A | No browser or user-facing surface |
| 5 — UX/navigation | N/A | No UI or navigation change |
| 6 — audit | PENDING | Requires an independent auditor on the exact candidate commit |

## Gate

Builder work stops after candidate commit. The 1.5 engine remains blocked until this
candidate is independently audited and merged.

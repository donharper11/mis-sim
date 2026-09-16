# Phase 7 operational audit

Date: 2026-09-16

This audit verifies the current build in the declared dependency environment. It is a local
operational rehearsal, not a production deployment approval.

| Check | Result | Evidence |
|---|---|---|
| Declared dependency environment | PASS | Fresh Python 3.12 virtual environment; `pip check` clean. |
| Full backend verification | PASS | `make check`: 689 pytest tests passed and every `check_*.py` guard passed. |
| PostgreSQL migration and persistence | PASS | Disposable PostgreSQL 16.15; Alembic head `20260915_0008`; current 28-table schema; six committed rounds persisted. |
| Backup and restore | PASS | Custom-format dump restored into a second disposable database; `round_result` query returned `6|1|6` for instance 1/team 1. |
| Cohort seed and scheduling | PASS | Two sections, four teams, 16 student accounts, registered packs, and deterministic schedules seeded in PostgreSQL. |
| Instructor advancement on PostgreSQL | PASS | Instructor API returned 200 and advanced both Section A teams from round 2 to round 3. The check also covered reconciliation after scheduled advancement. |
| Cohort request smoke | PASS | 16 concurrent logins plus 48 concurrent dashboard/controls/debrief reads; zero failures. Local p50 2.68s, p95 3.59s, max 3.60s. This is a smoke check, not a capacity limit. |
| Production deployment | OPEN | No production host, credentials, migration window, monitoring, or push/deploy was used. |
| Student manual and observed pilot | OPEN | Phase 7.3 remains to be written and rehearsed with an instructor outside the implementation loop. |

Two defects found during the audit were corrected before the final evidence run:

1. The migration verifier still assumed the pre-M2 19-table schema. It now checks the current
   28-table migration head while keeping the historical 19-table simulation result inventory.
2. PostgreSQL exposed an insert-order defect in `SimulationService.initialize`; the parent run
   is now flushed before its checkpoint and sheet children. The round-control endpoint also
   reconciles a stale instance pointer after scheduler-owned advancement.

Verdict: **Phase 7.1 and 7.2 pass locally. Production launch remains unapproved until a real
deployment rehearsal and the student-manual/pilot acceptance work are complete.** M4 can now
proceed against a verified operational baseline.

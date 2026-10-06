# Independent backend review — host activation and reset

Date: 2026-10-06. Auditor: `/root/backend_review`, fresh implementation reviewer, not builder or contract author. Basis: GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS, accepted `handoffs/readiness-2026-10-06/host-lifecycle-contract.md` (SHA256 `58c240a76024c3d0a9e28f8665a29057c3932af42a48eac2cf893bc0e05ed5ac`), production changes and their transaction/auth/migration consumers. No production edits by this auditor.

**Verdict: backend implementation ACCEPT for the reviewed production hashes, subject to the final combined gate and matching browser audit.** No open implementation defect was found. This does not approve merge, deployment, instructor-start behavior, performance readiness or the separately owned SQLite archive repair. READY-002 can close after the final packet gates pass; this audit alone is not the whole packet gate.

## Reviewed source identity

`host-lifecycle-backend-source-hashes.txt` captures the initial candidate, and `host-lifecycle-backend-final-source-hashes.txt` captures the re-reviewed candidate. All six production hashes remained unchanged during the audit:

| File | SHA256 |
|---|---|
| `backend/app/services/host_lifecycle.py` | `27a51b3847dd9946e5fdcab7f02b8b27f10004ed7168c65788251270b126b0f3` |
| `backend/app/simulation/service.py` | `b58506201e54141fa1d7f6e90f9bf14f9ec8d30a4f6b9137702e7049a4fae075` |
| `backend/app/services/platform.py` | `d741a19ad0481ff848b7a2be2e7641a5555caa3d80a841e17460d7b5501a0103` |
| `backend/app/api/runtime_host_platform.py` | `b701e896984b229a9106025ef7966405051dc7dc74452e15a7b5558a7274ef97` |
| `backend/app/api/runtime_round_control.py` | `90dd7514518f6f1ebf719b104f108f14aa996f6212c8749ef24e2a6c764f8008` |
| `backend/alembic/versions/20261006_0013_host_activation.py` | `741e97118e56a18cb9fe00225159070f9ae138083d8539d87a645d92ebee3e8b` |

The builder corrected two test-fixture defects and extended concurrency/grade coverage while the first suite was running. Those corrections were independently inspected and the affected tests rerun; the historical first-suite failures are retained rather than represented as a clean run.

## Independent verification

All PostgreSQL work used this reviewer's own loopback cluster on port **48183**, databases `mis_sim_verify_host_lifecycle_independent` and `mis_sim_verify_host_lifecycle_probe`. Neither the builder's port44535 database nor any shared application database was touched. Destructive schema fixtures were confined to the two explicitly named disposable audit databases.

Commands ran from `backend`, with `/tmp/mis-sim-readiness-venv/bin/python` and `HOST_LIFECYCLE_POSTGRES_URL=postgresql+asyncpg://audit:audit@127.0.0.1:48183/<dedicated-database>`:

- `-m pytest tests/test_host_lifecycle.py -q`: **13 passed, 3 failed, 455.86s** on the originally collected test snapshot. The three failures were the two reset fixture failures and PostgreSQL generated-ID fixture collision described below; all production behavior reached by the other cases passed. Evidence: `host-lifecycle-backend-pytest.log`.
- Current expanded reset/concurrency cases: `-m pytest tests/test_host_lifecycle.py -q -k 'reset_all_runtime or postgres_host_edit_reset'`: **4 passed, 2 failed, 55.43s** before the reset fixture correction. All concurrency parametrizations passed, including actual PostgreSQL host edit/reset and actual advance/reset. The SQLite concurrency variants return without claiming row-lock evidence. Evidence: `host-lifecycle-backend-reset-rerun.log`.
- Corrected reset tests: `-m pytest tests/test_host_lifecycle.py -q -k reset_all_runtime`: **2 passed, 16 deselected, 21.52s**, both SQLite and PostgreSQL. These now populate grading rows as well as the complete historical/versioned/host/schedule inventory and exercise late rollback, rejection, repeated reset, identity preservation and cross-instance equality. Evidence: `host-lifecycle-backend-reset-fixed.log`.
- Corrected pending-only API tests: `-m pytest tests/test_host_lifecycle.py -q -k pending_only`: **2 passed, 16 deselected, 25 warnings, 40.12s**, after independently reviewing the PostgreSQL fixture sequence correction. Both SQLite and PostgreSQL now pass creation/member authoritative timestamps, pending rename success, active/retired rejection and foreign-parent404. Evidence: `host-lifecycle-backend-pending-fixed.log`.
- `-m pytest tests/test_lifecycle_api.py -q`: **10 passed, 22 warnings, 8.27s**, including reset route, wrong instructor/student authorization, confirmation, archive and cascade isolation. These existing ORM-schema tests do not close the separately known SQLite migration/archive gap. Evidence: `host-lifecycle-backend-api.log`.

The lifecycle suite independently exercised real populated0012→0013 migrations on both engines; exact status-only repair sets, completed/missing runs, null/malformed/future timing and INTEGER extremes; repeated repair and no-op downgrade; activation rollback after injected failure; retry snapshot identity; exact result and checkpoint equality against a no-host control run; final-round pending horizon; manual/scheduler parity; reset between last per-team commit and final reconciliation; and newer authoritative run pointer reconciliation. Browser evidence is deliberately left to the independent browser reviewer.

### Additional independently authored race probe

The auditor additionally executed an independent PostgreSQL probe, separate from the shipped test body. It initialized two scoped runs through the real service, populated grading rows and enrollment sentinels, locked round1 and paused the **actual** `SimulationService.advance` after host promotion but before commit. Reset ran on an independent async connection. The probe queried `pg_stat_activity` by that connection's PID and observed `wait_event_type='Lock'` on the `simulation_run_v1` SELECT before releasing the advancing transaction.

After release, both transactions completed without deadlock. Every target runtime table, including grade rows, was empty; the other scope snapshot and enrollment rows were identical; a subsequent advance returned `not_found` rather than recreating state. Evidence: `host-lifecycle-backend-probe.log`:

```text
RESET_BLOCKED_ON_ACTUAL_ADVANCE_RUN Lock
PASS actual advance holds lock, reset waits, then all runtime including grade rows deleted; other scope and enrollment preserved; later advance refused
```

### Independent falsification

Inspected the isolated-copy harness, then executed an auditor-owned copy: `host-lifecycle-independent-falsify.py`. It copies `app` into disposable directories and invokes the actual acceptance tests with that copied implementation; production source is never mutated. All three plants independently failed at their intended assertions:

- Remove activation: actual active IDs `{17}` versus expected `{1,11,17}`.
- Remove pending-only server guards: API status200 versus expected409.
- Remove host/historical reset cleanup: target runtime emptiness assertion fails.

Evidence: `host-lifecycle-independent-falsify.log` and the three `host-lifecycle-independent-falsify-*.log` files. These checks distinguish predecessor behavior from the implementation under review.

## Closed audit findings

**HLA-BE-001 — Test gate, CLOSED.** The original reset fixture created `RoundSchedule` without mandatory `grace_period_minutes` (`backend/tests/test_host_lifecycle.py`, reset-inventory test constructor). Both engines raised NOT NULL errors at fixture flush, before reset assertions. The builder supplied explicit0; independent rerun passed both engines and exercised the intended reset checks. Original failures and corrected output are retained.

**HLA-BE-002 — Test gate, CLOSED after pending-only rerun.** `seed_parents` supplies explicit historical host/member IDs, leaving PostgreSQL sequences behind those IDs. The PostgreSQL pending-only API test then collided with `host_platform_pkey` on creation. This was a fixture issue, not observed in the production autoincrement path. The lifecycle fixture now advances both serial sequences to the existing maximum immediately after0012. The correction changes no production source or assertion.

No new open backend implementation finding is filed by this review.

## Transaction and scope conclusions

- `services/host_lifecycle.py:8` uses explicit instance/team predicates, pending-only status, positive created round, cast-before-add timing and authoritative current round. `SimulationService.advance:493` invokes it inside the existing locked transaction after setting the run pointer. The immutable retry return occurs earlier at `service.py:443–450`; promotion is not repeated on retry. The injected failure checks actual persisted rollback, not merely exception delivery.
- Host create/member timestamps derive from the locked run. Authorized parent selection precedes pending-only status checks; foreign-parent requests retain404 while locked/uneditable runs can reject earlier with409, as contracted.
- `services/platform.py:427–450` refreshes the instance under PostgreSQL NO KEY UPDATE, locks schedules then runs in deterministic order, and deletes the complete declared runtime inventory with explicit instance predicates. NO KEY UPDATE remains compatible with the FK key-share locks taken by an in-flight host insertion. The observed lock wait and cleanup prove the tested linearization rather than relying on code inspection alone.
- `runtime_round_control.py:165–188` discards stale reads, refreshes the instance under the same lock, reads run fields as scalar rows, requires the exact captured team-ID set and sufficient advancement, refuses mixed active rounds, derives the pointer from current runs, and preserves paused/archived status. Reset completing before this phase is therefore not overwritten by stale manual reconciliation. Initialization racing reset remains explicitly outside the contract.
- Migration0013 changes only eligible host status and has an honest no-op downgrade. It neither rewrites immutable engine evidence nor makes a final-round order active beyond the final current-round horizon.

## Remaining gates

A combined final-tree `make check` with explicit separate PostgreSQL targets, fresh migration verifier and matching independent browser acceptance remain parent-owned gates. Source hashes must still match this review or affected changes need re-review. No merge/deployment claim is made. READY-003 initialization, READY-004 performance and READY-AUD-BE-002 SQLite archive remain separate owners; this packet does not silently resolve them.

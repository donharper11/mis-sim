# M2 packet 2.3 — scheduling DoD

Implementation is bounded by `handoffs/recovery/m2-scheduling-amendment.md` and
`handoffs/recovery/m2-scheduling-dispatch.md`.

| Requirement | Evidence | Status |
|---|---|---|
| UTC-aware schedule and participant tables, persisted grace, restrictive FKs, unique tuple | schema guard | PASS |
| SimulationService boundary with registered pack/digest verification | scheduling tests | PASS |
| Fixed-time tick, lock/advance/grace/idempotency and partial retry | `test_scheduling.py` | PASS |
| CONTRACTS.md records UTC fields, explicit-time API, and DB claim semantics | contract review | PASS |
| Reversible migration and one-clock-read entrypoint | migration/guard tests | PASS |
| Two-instance/different-pack schedule and seed | cohort scheduling probe | PASS |
| Existing instance isolation and full repository gate | existing canary; `make check` | PASS |

Auth/browser canaries are N-A for this packet. The packet does not alter the runner,
simulation service, runtime tables, engine/scoring, auth, frontend, or registry.

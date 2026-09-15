# M3 launch-readiness audit

Date: 2026-09-16

This audit covers the first-playable gate after M3.8. The browser evidence used a disposable
SQLite cohort seeded from the registered Riverside pack, with one student account and the
instructor account. The browser used the production build served by Vite preview; API calls
were sent to the local FastAPI host.

| Gate | Result | Evidence |
|---|---|---|
| Auth and instance scope | PASS | Student login bound to Section A; instructor token authorized round control; no cross-instance access was used. |
| M3 routes | PASS | Strategy, Governance, Security, Services, People, Challenges, Review, and Debrief all rendered through normal routes. |
| Minimum Phase 4 controls | PASS | Each family has a real projection and typed command adapter: `declare_strategy`, `assign`, `set_primary`, `set_policy`/security purchase, service purchase, staffing/communication, and event response. |
| Instructor advancement | PASS | `POST /api/instances/{id}/round-control/advance` locked draft sheets through `SimulationService` and advanced every initialized team. |
| Six-round browser loop | PASS | Instance ended at round 6/completed; two teams ended completed at round 6; 12 immutable `RoundResult` rows were persisted. |
| Debrief evidence | PASS | Student Debrief rendered the latest round as round 6 and exposed the stored report payload. |
| Browser diagnostics | PASS | Clean production-build probe: zero console errors, page errors, or failed network requests across all eight routes. |
| Frontend implementation checks | PASS | `npm run lint` and `npm run build` pass. Vite emits only the existing large-chunk warning. |
| Focused backend checks | PASS | M3.4–M3.8 runtime API matrix remains green; new runtime modules compile and pass import/route registration checks. |
| Repository-wide verification | OPEN | The known environment blockers remain: the sandbox lacks the Alembic executable and PostgreSQL driver required by the full migration/production suite. |
| Production deployment audit | OPEN | No production host, migration dry run, backup/restore rehearsal, cohort load test, or push/deploy has been performed. |

Verdict: **M3 first-playable gate passed locally. Production launch is not yet approved.** The
remaining work is the Phase 7 operational audit: run the declared dependency environment with
PostgreSQL, execute migrations and the full suite, rehearse deployment and recovery, and obtain
an instructor acceptance pass against the six-round script before publishing the build.

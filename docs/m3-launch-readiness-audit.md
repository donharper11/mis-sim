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
| Repository-wide verification | PASS | Fresh declared environment: `pip check` clean, 689 pytest tests passed, and every guard passed. |
| Production deployment audit | OPEN | Local migration, backup/restore, cohort smoke, and instructor API rehearsal pass; no production host, monitoring, deployment, or push has been used. |

Verdict: **M3 first-playable gate passed locally. Production launch is not yet approved.** The
remaining work is the Phase 7 deployment and pilot work: use a real host with monitoring,
complete the student manual, and obtain an instructor acceptance pass outside the implementation
loop before publishing the build. Detailed evidence is in `docs/phase7-operational-audit.md`.

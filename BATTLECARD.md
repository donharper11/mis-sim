# MIS Simulation — current battlecard

Updated 2026-10-07. Pushed checkpoint: `da2ebf8` (2026-10-06), plus current instructor-start work. **Current action queue: [TODO.md](TODO.md).**

**Readiness target (user clarification, October 7):** a usable platform verified through our
own complete rehearsals with seeded demo instructors/students, before inviting live participants.
Recruitment and an observed human teaching pilot follow readiness; they are not readiness gates.
Remaining product features stay in scope. Implementation resumed on October 7: instructor start is complete and independently accepted.

## Product and guardrails

Student teams manage an inherited IT estate across six rounds. The current navigation is
Strategy → IT Infrastructure → Applications → Rollout & Adoption → Review & Budget,
with Dashboard, Challenges and Debrief. Realised value is Technology × Organisation ×
Management; weighted partial evidence and structural hard gates remain in the engine.
AI may explain, role-play and teach; it must not recommend a plan or produce scored values.
All numeric persona claims must come from scoped engine facts.

## What is available

| Area | Evidence and limit |
|---|---|
| Simulation (M0–M2) | Typed decision sheets, state evolution, accounting, atomic progression, scoped persistence, auth, casepack registry and scheduling. Completion recorded in recovery audits. |
| Student loop (M3) | October 6 six-round browser loop passed with persisted debriefs and zero diagnostics; cross-panel controls and host proofs also pass locally. |
| Student coverage (M4) | TCO forecasts, project lifecycle, capital requests, freshness and full modern financial model implemented. Weighted scoring balance accepted September 18. Legacy scoring paths retain their contracts. |
| Instructor operations (M5) | Setup/start with explicit per-team strategy, existing-user enrollment, assignment, round control, monitoring, grading/CSV export, registry, clone/archive/reset implemented. Setup audit closes all five findings October 2; 14 setup and 20 operations browser proofs recorded. CSV roster import/account provisioning remain open. |
| AI | Provider fallback/grounding infrastructure and Riverside persona API implemented (October 3, `a292f8a`, 17 acceptance tests including grounding/advisor probes). Student interview UI, chapter-filtered coach and debrief narration remain open. The September AI audit predates A2 implementation. |
| Content (M6) | Riverside is the substantive pack; `m2_isolation_fixture` is an isolation fixture, not a second industry. Runtime preference/authoring portability gaps remain. |
| Release | Local operational rehearsal passed historically; manual, pilot script and local restore runbook prepared; production deployment, monitoring verification and final seeded rehearsal remain open. Observed human pilot follows readiness. |

## Current verification boundary

October 7 instructor-start evidence: **885 backend tests passed, no skips, all guards green**,
including dedicated PostgreSQL targets; frontend lint and production build pass. Independent
backend/browser/setup-concurrency reviews ACCEPT. [Start report](docs/instructor-start-2026-10-07.md).
The preceding October 6 host-lifecycle gate passed 834 tests. Seventeen browser checks
cover four widths and six-round completion. Host-platform and five additional controls
checks pass; People/Security are reachable, cross-panel saves share revisions, and pending
strategy/ownership/policy decisions persist. PostgreSQL migration and restore checks pass.
See [the readiness report](docs/readiness-2026-10-06.md) for the exact timing and limits:
the full corrected-tree gate and independent browser closing checks passed after review rework.

The user-requested checkpoint was committed/pushed as `da2ebf8`; the user released the pause on October 7.
Continue from [the next-agent note](handoffs/readiness-2026-10-06/NEXT-AGENT.md). Fresh independent backend and frontend corrections reviews passed after six reproduced
defects were fixed and independently retested. Host scope0012 and lifecycle0013 passed independent backend/browser audits and the full gate. Nothing is merged to main or deployed. The ~1.1 MB frontend bundle remains open.

## Next work, in order

1. Host [scope](docs/host-scope-2026-10-06.md) and [activation/reset](docs/host-lifecycle-2026-10-06.md) are independently accepted.
   Instructor start is also accepted ([evidence](docs/instructor-start-2026-10-07.md)). Next close the SQLite archive-migration gap;
   optimize the profiled repair-inclusive read without weakening pack isolation.
2. Verify operations and rehearse the full application ourselves with seeded instructor/student
   accounts using the prepared guides. Hosting details remain needed; human participants do not.
3. Finish M5 teaching support and roster onboarding, retaining scope and grounding checks.
4. Author the selected second vertical, close portability contracts and prove six-round
   operation without case-specific engine branches.
5. Complete dashboard charts, responsive polish and measured bundle improvements.

Use [TODO.md](TODO.md) for owners, acceptance evidence and decisions. Do not start work from
an old OPEN/FAIL headline without checking later commits and the current implementation.

## Navigation for the next agent

- Current status: this file; ordered tasks and handoff: [TODO.md](TODO.md).
- Rules: `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`, `CONTRACTS.md`.
- Design and historical milestones: `design/08-implementation-north-star.md`.
- M4 evidence: `docs/m4-coverage-slice.md`, `docs/m4-strategy-playthrough-audit.md`.
- M5 evidence: `handoffs/m5/instructor-ops-audit.md`; AI source in `backend/app/ai/`
  and `backend/app/api/runtime_persona.py` supersedes missing-A2 claims in the old audit.
- M6 residuals: `handoffs/m6/portability-seam-audit.md`.
- Release evidence: `docs/phase7-operational-audit.md`.

Update this summary and TODO together when a gate changes. Distinguish implemented,
locally verified, independently audited and production accepted. Preserve old audits as
history; never claim an independent audit from builder checks.

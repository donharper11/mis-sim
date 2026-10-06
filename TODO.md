# MIS Simulation — prioritized work and agent handoff

Updated 2026-10-07. Checkpoint branch `build/readiness-2026-10-06`, last pushed checkpoint `da2ebf8`. User resumed implementation on 2026-10-07; READY-003 instructor start is complete and independently accepted. User requested status reconciliation followed
by remaining work in priority order. Preserve pre-existing changes; do not reset the tree.

**Resumed 2026-10-07:** instructor start is closed after independent backend/browser/concurrency acceptance and the 885-test full gate, no skips, all guards green.
[The prior handoff](handoffs/readiness-2026-10-06/NEXT-AGENT.md) preserves the checkpoint basis.

## Readiness target — clarified by the user, 2026-10-07

Launch/production-ready means the platform is usable and technically ready to bring in live
participants afterward. Verify the intended workflows ourselves using seeded demo instructor
and student accounts, real persisted data, and complete browser walkthroughs. Include both
competent and negligent decision paths, scoring/debrief evidence, authorization/isolation,
operational checks and representative simulated cohort load. Demo accounts must exercise the
normal application flows; a seed script must not hide a missing instructor start/onboarding flow.
Recruiting participants, scheduling an observed teaching pilot and obtaining live human
pedagogical acceptance are POST-READINESS activities, not blockers for this target. Keep those
activities visible separately without claiming they have been performed. This clarification
changes acceptance timing, not the remaining product feature scope. Implementation resumed at the user’s request.

Status vocabulary: OPEN, IN PROGRESS, LOCAL PASS, ACCEPTED, EXTERNAL DEPENDENCY.
A local pass is not independent audit or production acceptance.

## P0 — restore a verified working baseline

- [x] **DOC-01:** Reconcile README and battlecard, create this queue with current evidence.
- [x] **QA-01 — LOCAL PASS:** Seven frontend lint errors fixed; lint/build pass.
- [x] **QA-02 — LOCAL PASS:** final instructor-start `make check`: 885 passed, no skips, all guards green,
  including all four dedicated PostgreSQL targets. Previous host-lifecycle gate:834 passed. Frontend lint/build
  and independent browser closing checks pass; see the dated report.
- [ ] **QA-03 — LOCAL FIXES VERIFIED; CONTRACT RESIDUES OPEN:** Review pre-existing rollout metadata/platform modal changes and
  October infrastructure additions; verify scoped reads, actual cost fields, save/reload,
  read-only/locked behavior and cross-team/instance refusal.
- [x] **QA-04 — LOCAL PASS (technical smoke; full competent/negligent seeded rehearsal still open):** Fresh seeded student/instructor browser rehearsal at 1440, 1280,
  1024 and 720 widths; login, all current routes, decisions, review/lock, six advances and
  persisted debrief; zero browser errors; screenshots and exact commands recorded.
- [ ] **QA-05 — REVIEWS COMPLETED; RELEASE GATES OPEN:** Independent review of the resulting candidate before merge.
  Builder verification alone does not close this item. Fresh backend and frontend reviewers accepted the bounded corrections after six reproduced
  defects were fixed and independently retested (one seed defect, five UI defects). Overall
  readiness remains open; see [backend review](findings/readiness-2026-10-06/backend-independent-review.md)
  and [frontend review](findings/readiness-2026-10-06/frontend-independent-review.md).

- [x] **QA-06 — SCOPE/LIFECYCLE/START ACCEPTED:** Host scope, activation/reset and instructor start
  are closed (READY-001–003). Next repair the SQLite archive gap (QA-07), then profile slow
  repair-inclusive requests (QA-08 / READY-004). These precede P2 feature work. Proposed contract:
  [host scope contract](handoffs/readiness-2026-10-06/host-scope-contract.md), independently
  [accepted for dispatch](handoffs/readiness-2026-10-06/contract-independent-review.md).
  Scope migration 0012 and scoped APIs pass both independent audits and the 816-test full gate.
  [Scope evidence](docs/host-scope-2026-10-06.md). Lifecycle/start remain separate contracts;
  [lifecycle contract](handoffs/readiness-2026-10-06/host-lifecycle-contract.md) passed independent
  dispatch review. Activation/reset passed both independent audits and the final 834-test
  gate with no skips and all guards green; [lifecycle evidence](docs/host-lifecycle-2026-10-06.md).
  The [instructor-start contract](handoffs/readiness-2026-10-06/instructor-start-contract.md)
  passed independent dispatch review; implementation and independent backend/browser/concurrency audits now pass. The final full gate passed 885 tests with no skips and all guards green; see [start evidence](docs/instructor-start-2026-10-07.md). It protects
  in-flight writes across restart. New requests from stale tabs still need separately owned
  client generation tokens (READY-START-CLIENT).

- [ ] **QA-07 — OPEN:** Repair SQLite archive migration (READY-AUD-BE-002): fresh migrated
  databases retain an old status CHECK and reject archive. Owner: platform/migrations;
  require a real migrated-database regression and populated upgrade proof. [Preflight](handoffs/readiness-2026-10-06/sqlite-archive-preflight-review.md)
  verifies the exact gap; [contract](handoffs/readiness-2026-10-06/sqlite-archive-contract.md) is independently accepted for implementation after instructor-start closes.

- [ ] **QA-08 — OPEN:** Profile repair-inclusive reads/advance (READY-004), then measure
  representative simulated cohort load before making performance readiness claims.

Current evidence: [instructor start](docs/instructor-start-2026-10-07.md) and
[prior readiness work](docs/readiness-2026-10-06.md).

Initial October 6 evidence (superseded by that report): `npm run build` passes (1,096.16 kB JS / 336.94 kB gzip);
`npm run lint` reports seven errors (unused imports/helpers, unescaped quotes, missing
prop validation). Initial full gate subsequently passed 790 tests, one skipped; explicit PostgreSQL
concurrency passed separately. Full corrected gate passed 795 tests with no skips and all guards green. Seventeen browser checks
passed with six persisted rounds and zero diagnostics. Host and five controls browser checks
also passed, including restored People/Security tabs and draft preservation across saves.

## P1 — seeded rehearsal and operational readiness

- [x] **PILOT-01 — PREPARED:** [Student guide](docs/student-guide.md) matched to current navigation. Use seeded accounts for the readiness walkthrough; live acceptance is post-readiness.
- [x] **PILOT-02 — PREPARED:** [Instructor rehearsal and acceptance form](docs/pilot-rehearsal.md);
  include competent and negligent paths and clear expected causal evidence.
- [x] **OPS-01 — LOCAL PASS:** [Reproduction runbook](docs/readiness-runbook.md), guarded round-one seed, real migration and restore proof;
  verify against a disposable database and capture the actual migration inventory.
- [ ] **OPS-02 — EXTERNAL DEPENDENCY:** Production host/domain, TLS, secrets, monitoring,
  scheduler operation, restore rehearsal and deployed-version verification. Destination
  requested from user; no deployment has been claimed or authorized to an unknown host.
- [ ] **REHEARSAL-01 — OPEN:** After remaining features land, run the complete instructor/student
  rehearsal ourselves with seeded demo accounts through normal UI flows, including setup/start,
  decisions, progression, debrief, grading/export and lifecycle operations. Record real persisted
  results, competent/negligent paths, responsive behavior and browser/network diagnostics.

## P2 — complete M5 teaching and onboarding

- [ ] **AI-01 — OPEN:** Wire scoped persona roster/turns into student interview UI, verify
  grounded responses, authored disabled-provider fallback and read-only behavior.
- [ ] **AI-02 — OPEN:** Chapter-filtered textbook coach using the approved `mis_textbook`
  source; inspect actual retrieval service before implementing. No plan recommendations.
- [ ] **AI-03 — OPEN:** Debrief narration from immutable causal evidence with supported
  chapter links, safe fallback, grounding and advisor-policy checks.
- [ ] **AI-04 — OPEN:** Refresh independent AI acceptance against A2 implementation rather
  than September's obsolete missing-route finding. Live provider availability is separate
  from deterministic injected-provider tests; retain disabled-by-default behavior.
- [ ] **ROSTER-01 — OPEN:** Account provisioning and CSV preview/apply with row-level errors,
  instructor ownership, duplicate/idempotency handling and browser acceptance. Existing
  identity enrollment and grade CSV export do not implement roster CSV import.

## P3 — M6 content portability

- [ ] **PACK-01 — DECISION PENDING:** Select substantive second industry (community bank,
  hospital, logistics or light manufacturing); requested from user October 6.
- [ ] **PACK-02 — OPEN:** Remove hidden Riverside preference cardinality assumptions through
  an explicit reviewed contract; document required runtime supplement and validators.
- [ ] **PACK-03 — OPEN:** Author second vertical and run six rounds plus deterministic
  replay, causal checks, digest/isolation checks with no case-specific engine branches.
- [ ] **PACK-04 — OPEN:** Verify content, causal explanations and calibration through seeded
  six-round rehearsals and independent content review. Retain the authored estimate/calibration
  inventory; live participant pedagogical validation follows readiness.

## P4 — presentation and performance

- [ ] **UX-01 — OPEN:** Dashboard charts from real score/history evidence. Do not invent
  market-share metrics: a competitive-market model is deliberately outside current scope.
- [ ] **UX-02 — OPEN:** Remaining responsive/visual comparison with supplied screenshots.
  Four-width route/overflow rehearsal passed; Barlow now ships locally with OFL license.
  Current Barlow/rounded-card design differs from historical IBM Plex/flat-card wording;
  preserve current design during mechanical fixes and record the documentation mismatch.
- [ ] **PERF-01 — OPEN:** Route-level lazy loading and measured bundle improvement; preserve
  accessible loading/error states and rerun navigation browser proofs.
- [ ] **DOC-02 — OPEN:** Reconcile older north-star/register/frontend docs incrementally as
  each touched behavior is verified; original audit records remain historical.

## After platform readiness — not launch-readiness blockers

- [ ] **PILOT-03 — POST-READINESS:** Recruit instructor/student participants, schedule an
  observed teaching pilot, and collect real-world usability/pedagogical acceptance. Reuse the
  prepared script, but do not confuse seeded technical evidence with observed human feedback.

## Evidence and continuation rules

Use `BATTLECARD.md` for a quick orientation. Consult current source and later audit entries
before interpreting old open findings. `README.md`'s former 11/47 count is obsolete.

For each task record changed paths, exact verification commands/results, remaining limits
and the next action here or in a linked readiness report. Never overwrite original audit
history or represent a backend endpoint as a completed browser workflow.

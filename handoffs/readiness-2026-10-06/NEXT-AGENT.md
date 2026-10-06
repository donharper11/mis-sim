# Paused checkpoint — resume here

User requested: finish the current host lifecycle task, commit/push the work so far, then
**pause for a break**. Do not begin another implementation until the user resumes.
Branch: `build/readiness-2026-10-06`, origin `donharper11/mis-sim` on GitHub.
Original reviewed baseline: `0a535ba`. The checkpoint commit includes existing UI work,
readiness corrections, updated reports, accepted host scope/lifecycle, tests and audit evidence.
Read `git log -1`, `git status`, README, BATTLECARD and TODO before changing anything.

## Current completion boundary

- README/BATTLECARD/TODO reconciled; student guide, pilot script and reproducible local seed/
  operational runbook prepared. Historical packet headlines are not current readiness.
- Readiness backend/frontend corrections independently accepted after six reproduced defects
  were fixed. Includes valid rollout commands/costs, control draft preservation, editable
  guards, no unassigned-team fallback, health503, local fonts and accurate32-model verifier.
- READY-001 host scope accepted: migration0012, member nonnull instance identity/composite
  parent scope, host/team composite FK, ORM cascades and scoped APIs. Historical full816 gate.
- READY-002 host lifecycle implemented, independent backend and browser audits ACCEPT:
  activation atomically follows authoritative run progression; final-round hosts stay pending;
  active/retired edits refused; migration0013 repairs valid overdue statuses; setup reset
  clears all25 scoped runtime tables and timestamps; manual final status write fenced against
  a completed reset. Final gate: 834 passed, no skips, 226 warnings, 1208.74s; all guards green.
  Fresh PostgreSQL head0013 verifier and frontend lint/build also pass.
  See docs/host-lifecycle-2026-10-06.md for evidence.
- No production deployment or main-branch merge. User authorized this checkpoint commit/push.
- No instructor-start implementation yet. Only inspected basis and independently accepted
  contract. Stop here as requested, even though next work is well specified.

## First task on resume: READY-003 instructor start

Read `instructor-start-preflight-review.md`, `instructor-start-contract.md` and
`instructor-start-contract-review.md` in this folder. Accepted contract SHA256:
`a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.
Do not improvise around it; author revisions need independent review if the boundary changes.

Proposed pedagogy was asked asynchronously: instructor selects each team's agreed initial
strategy versus a new student pre-start workflow. No answer received before this checkpoint;
the stated default is explicit instructor selection per team, with no automatic default and
visible switching-cost/disruption notice. If the user later chooses student pre-start selection,
revise the contract before building. Existing engine charges strategy changes even in round1;
never quietly initialize all teams to cost_leadership as a harmless placeholder.

Core implementation: atomic all-team initial state+instance activation; shared section locks
and refreshed setup eligibility; exact roster/strategy/digest/authored-horizon checks; clean
runtime only; duplicate start409 without mutation; ordinary browser start action. Keep scoring
semantics intact. Existing per-team initialize must retain its behavior.

Critical review finding: final HTTP response generation check alone is insufficient. Old
in-flight requests can mutate recreated round1/revision0 runs. Contract requires captured
started_at generation checks INSIDE patch_sheet/lock/reopen/advance transactions under run
lock, propagated by all named runtime API mutations and real scheduler; host metadata gets
equivalent checking. Never add run→instance row-lock inversion. Test barriers before lock,
between lock/advance, later team and after final service commit. READY-START-CLIENT separately
owns NEW requests from stale tabs (no client generation token yet); do not claim that fixed.

After start: SQLite archive CHECK repair READY-AUD-BE-002 (0010 ignored SQLite; add a new
migration, do not rewrite history), then repair-inclusive read performance READY-004. Follow
TODO priority order for remaining teaching/onboarding/content/release work.

## Verification and independent review

Final lifecycle gate/log: `findings/host-lifecycle-2026-10-06/full-check.log`.
Exact commands: sibling `commands.txt`; migration verifier and frontend build logs retained.
Audits: `findings/readiness-2026-10-06/host-lifecycle-backend-review.md` and
`host-lifecycle-browser-review.md`, with source manifests and browser evidence.
Both audits accepted matching six production hashes. Final test fixture hash:
`add13ef303e7b602580b9674cfa34f76a5b331095700a29d86aa63eedeff3542`.

Initial focused failures were two TEST fixture defects: omitted required schedule grace value,
and PostgreSQL explicit seed IDs leaving serial sequences behind. Both fixed and independently
retested; failure logs are retained honestly. Three isolated predecessor-behavior plants fail
at intended assertions (activation, pending-only mutation, full reset cleanup). Production
source was not modified by plants. Do not mistake intentionally failing logs for open defects.

User explicitly authorized independent review by fresh agents. Existing independent reviewers
were contract_review, backend_review and frontend_review; each was separate from root builder.
For future implementation keep builder≠auditor, and use fresh independent spec/audit gates as
GOVERNANCE/QUALITY/SPEC protocols require. Reviews do not authorize production deployment.

## Environment, if still available

- Repo `/home/ubuntu/projects/mis-sim`, Python3.12 venv `/tmp/mis-sim-readiness-venv`.
- Node22 `/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node` (system Node is unsuitable).
- PostgreSQL16 builder cluster `/tmp/mis-sim-readiness-7kx7ly0q`, loopback port44535,
  local test role readiness. Dedicated destructive DBs MUST remain separate:
  `mis_sim_verify_host_scope_build`, `mis_sim_verify_host_lifecycle_build`,
  `mis_sim_verify_concurrency`. Lifecycle verifier DB `mis_sim_verify_host_lifecycle_fresh`
  is retained clean-head0013 with six legacy results; do not use it as destructive fixture.
- Independent auditor cluster port48183/test role audit, separate audit DBs.
- Browser lifecycle fixture `mis_sim_browser_host_lifecycle_review` on builder cluster was
  altered by real advance/reset proofs; it is not a clean starting cohort. Scope/main older
  browser fixtures may be older migration/locked/completed. Always fresh-seed a new allowed
  `mis_sim_browser_*` fixture for start proof; do not reuse an unknown database.
- Temporary services/fixtures may disappear between sessions. Runbook and guarded seed are
  authoritative reproduction instructions. Never point destructive tests at non-disposable DBs.

## Remaining external decisions

Production host/domain and pilot participants/schedule remain unanswered; no deployment claim.
Substantive second vertical selection (bank/hospital/logistics/manufacturing) remains open.
Current fonts/styles preserve user UI refinements; design-document mismatch is recorded rather
than silently reverting visuals. Screenshots under sample_screen_images are user references.

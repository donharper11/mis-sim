# Instructor start — 2026-10-07

Status: ACCEPTED. READY-003 is closed. Independent backend/browser/setup-concurrency reviews
ACCEPT, including the corrected late SQLite reset/start race, and the final full gate passes.
Branch `build/readiness-2026-10-06`, following pushed checkpoint `da2ebf8`. No main merge or deployment.

## Behavior

An instructor can now start an eligible section from Setup. Readiness explains missing
teams, roster problems, invalid case binding/horizon and existing runtime data. The instructor
must explicitly select each team's agreed initial strategy; there is no default. The
confirmation names the section, case, round count and every choice. Submission disables
context changes and duplicate clicks, preserves choices on failure, and opens round controls
for the section just started.

Owner instructors and admins may start; other instructors, TAs and students cannot. The
server rechecks the complete roster and registered case under locks. All teams' run,
checkpoint0 and empty sheet1 plus instance activation commit together. A late failure leaves
all data unchanged. Repeat starts return409 without overwriting the original start or decisions.
Schedules are still an explicit instructor action. Scoring and strategy-change costs are unchanged.

Start and eligibility-changing setup mutations share section→instance locks and refreshed
rows. In-flight simulation writes carry their captured `started_at` generation into the run
transaction; reset/restart cannot make a delayed old request write into a new game with the
same IDs. Scheduler claims/metadata and Review's later schedule publication are fenced too.
PostgreSQL uses row locks; SQLite reserves its writer before the corresponding checks.

This does **not** protect a newly sent request from a stale browser tab: client generation
tokens remain READY-START-CLIENT. Manual multi-team advancement remains separate team
transactions. There is no new migration, score formula, automatic schedule or shortened horizon.

## Verification and independent review

Accepted contract SHA256:
`a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.
[Contract and dispatch review](../handoffs/readiness-2026-10-06/instructor-start-contract-review.md).

- Migrated SQLite/PostgreSQL tests exercise atomic rollback/state parity, eligibility, all 25
  runtime table families, reset recovery, public authorization/body validation and retry refusal.
- Actual HTTP mutation tests cover platform/components/rollout/controls, review, staff lock/
  reopen/advance and host metadata. Manual barriers cover before lock, between lock/advance,
  later team and final publication, with exact replacement database snapshot comparisons.
- Independent [setup concurrency review](../findings/instructor-start-2026-10-07/setup-concurrency-review.md):
  **17 PostgreSQL cases pass** with observed database lock waits, both orderings of seven setup
  mutators, duplicates and reset/start, including retained stale ORM objects.
- Independent [browser review](../findings/instructor-start-2026-10-07/browser-review.md):
  ordinary demo identities only, then UI course/section/binding/two teams/four enrollments/
  assignment/start; student save/lock; instructor advance1→2 and persisted debrief1. Explicit
  choices, stale-team409 draft preservation, pending guards, ownership refusals and 1440/720
  layout verified; zero unexpected diagnostics. Three found UI defects were corrected/retested.
- Independent backend review reproduced scheduler entry capture, metadata publication and
  expired worklist defects, plus Review's post-service publication race. Shared protections
  and permanent scheduler tests address those classes; [final backend verdict is ACCEPT](../findings/instructor-start-2026-10-07/backend-final-review.md).
- Isolated fault plants remove generation checks, atomic transaction ownership, runtime
  inventory checks and account eligibility checks. Each actual regression fails at its intended
  assertion. Independent plants remove scheduler metadata protection and cached-row refresh;
  both are detected. Production source is not edited by these experiments.
- A late adversarial SQLite reset/start probe found that FOR UPDATE alone left reset's setup
  eligibility read unprotected. Reset now reserves SQLite's writer before reading status.
  Two permanent both-order tests observe real writer contention and preserve full snapshots;
  removing that reservation makes the intended lock assertion fail. Independent re-review
  accepted the correction. The earlier full run was stopped and restarted on the final code.
- Frontend lint/build pass; build retains the existing large-bundle warning (~1.11MB JS).
- Final full gate: **885 passed, no skips, 290 warnings, 1587.28s (26m27s); all guards green**.
  All four dedicated PostgreSQL targets were supplied. [Raw log](../findings/instructor-start-2026-10-07/full-check.log)
  and [commands](../findings/instructor-start-2026-10-07/commands.txt) are retained.
  Reviewed backend and browser source hashes match the final implementation.
  Frontend production build: 1108.97kB JS / 341.45kB gzip; existing size warning remains.

## Next work

Repair the SQLite archive CHECK migration, then profile repair-inclusive runtime requests.
Client generation tokens and the remaining product/readiness work stay visible in TODO.
Use seeded demo participants for our own complete acceptance rehearsal; recruitment and an
observed human pilot follow the user's readiness target and are not prerequisites.

## Preflight and definition of done

Preflight verified the inherited initializer owns its own transaction, strategies affect
scored initial state, setup mutations cache ORM rows, and reset uses instance→schedule→run
locks. The independently accepted contract settled each before implementation. Registered
case horizon/digest and25 runtime tables were checked against actual models/migrations;
no UI-only or create_all-only fixture is used to establish start correctness.

| Contract gate | Current evidence / disposition |
|---|---|
| Atomic correct initial state | PASS: `test_atomic_start_state_parity_rollback_retry`, migrated SQLite/PG; second-team failure and planted per-team commit; authored state/digest parity |
| Eligibility/auth/payload | PASS: service eligibility and actual public API tests; independent browser no-team/missing-choice refusals; student/TA/wrong-owner refusal, admin success |
| Runtime residue and retry | PASS: all 25 inventory families, reset recovery, duplicate/current-state refusal and complete unchanged snapshots |
| PostgreSQL serialization | PASS: 17 independently run races, observed blocking PIDs, stale identity maps, duplicate/reset/setup mutation orderings; missing-refresh plant fails |
| Old in-flight mutations | PASS: all named HTTP producers, host metadata, four manual barriers and 14 independent scheduler cases on both databases; publication metadata also checked |
| Predecessor/fault detection | PASS: absent route reproduced by independent browser, per-team commit/generation/inventory/eligibility/scheduler/refresh plants fail intended assertions |
| Browser workflow | PASS: fresh ordinary cohort/users, all-UI setup/start, distinct strategies, student capital/save/lock, instructor advance/debrief,1440/720, zero unexpected diagnostics |
| Independent audits | ACCEPT: backend, browser and setup-concurrency reports; final reviewed production source hashes reconciled |
| Completion gate | PASS: 885 tests, no skips, all guards green; frontend lint/build PASS; fresh PostgreSQL verifier PASS at 0013/all 32 model tables/six committed legacy rounds |

The accepted contract's old-response/manual cases live in `test_instructor_start_api.py`,
and scheduler cases in the additional `test_instructor_start_scheduler.py`; the concurrency
file owns database setup/reset races. This division preserves the specified barriers and
snapshot assertions. The closing report uses the actual completion date October 7 rather
than the contract's proposed October 6 filename.

# Instructor start — proposed dispatch contract

2026-10-06. Author: root readiness agent. PROPOSED, no implementation authorized by this
artifact until independent review and host lifecycle final gate complete. User authorized
remaining work in priority order. READY-003. Heavy: shared initialization and scored state.

## Basis and intent

[V] InstructorSetup currently creates pack binding, teams and existing-user enrollments,
but no start endpoint initializes production runs. Demo seed calls initialize separately.
[V] SimulationService.initialize is a per-team transaction with real checkpoint0/sheet1;
strategy is required. Changing it later has authored reopen costs and organisational shock.
[V] Setup mutators do not all share a lock or refresh cached instance status. Start must
serialize all eligibility changes, not merely its own endpoint. See independent
[instructor-start-preflight-review.md](instructor-start-preflight-review.md) for commands,
paths, verification and the eight decision areas that this proposal settles.
[V] Instance creation accepts a shorter horizon than the pack, while service completion
uses pack.metadata.rounds. This packet rejects mismatched horizons; no silent overwrite.

## Settled behavior

1. Instructor owner or admin starts a bound setup instance. Student, TA and wrong-course
   instructor cannot start (existing auth semantics403). No new student setup surface.
   Instructor explicitly selects each team's agreed initial strategy from validated pack
   keys, with no preselected default. This is genuine initial strategy, not a placeholder.
   UI copy: "Choose each team's agreed starting strategy. Changing strategy later incurs
   the case's switching costs and organisational disruption." Existing scoring and later
   declaration semantics remain unchanged. No case-specific default or engine branch.
   This is the proposed default following the optional user question; a user choice of
   student pre-start selection supersedes this paragraph before implementation.
2. Atomic all-team initialization and instance activation in one database transaction.
   Extract the existing run/checkpoint/sheet construction to a session-owned service method;
   public single-team initialize retains its current transaction/view/error behavior and
   delegates construction. New start uses AsyncSession.run_sync with the same transaction,
   not per-team engines/commits or compensating deletion. No preview needed for start output.
   State/checkpoint digests match direct initialize with the exact chosen strategy.
3. Eligible only when section/course active, instance setup at round0, digest present and
   matching the freshly resolved registered runtime pack, total_rounds==authored rounds,
   at least1 team, team count<=section.max_teams, valid positive min/max sizes. Every active
   student enrollment must reference a team in this instance, and each team's count of
   active student enrollments must be within section min/max. TA enrollments do not count.
   Count only Enrollment.is_active=true, Enrollment.role=student, User.is_active=true and
   User.role=student. An active student enrollment with missing/inactive/nonstudent User is
   a blocking invalid roster, not silently ignored. Inactive enrollments are ignored; active
   TA enrollments are excluded from team counts and strategy selection; instructor Users
   are not valid student enrollments. Cross-scope
   roster is refused. Empty/underfilled teams and unassigned active students give actionable
   blocked reasons.
4. All 25 scoped runtime tables must be empty (schedule, host, versioned simulation, legacy
   round and grading inventories). Any residue, even partial prior initialization, conflicts
   without changing rows. Setup reset is the existing deliberate recovery action. Do not
   adopt or overwrite historical state. Any non-setup or round>0 attempt returns409, including
   exact duplicate start, paused/completed/archived and edited/advanced runs. This explicit
   conflict is harmless; no receipt/idempotent replay claim. started_at is never rewritten
   by retry. Concurrent duplicates produce exactly one success and one409.
5. On success create run/current1/draft/advanced0, checkpoint0 and empty revision0 sheet1 for
   every team; set instance active/current1/started_at=UTC now/completed_at=None. Preserve
   pack key/version/digest, total_rounds, settings, teams and roster. Create no schedules,
   hosts, results or grading rows. Scheduling remains the existing explicit instructor action.
6. Failed pack checks, stale payload, invalid strategy, eligibility or late-team failure
   roll back EVERYTHING, including started_at and every earlier team's rows. Other scopes
   remain byte-equivalent. No missing-table fallback in the new path.

## Shared transaction boundary

Start locks section first, then refreshes/locks instance NO KEY UPDATE. Course/section active
checks and team/enrollment snapshots occur after locks. All setup mutations that can affect
eligibility share the section lock: team create/rename, enrollment create/assignment, pack
binding, section deletion and course deletion. Refresh section/instance ORM rows explicitly
(populate_existing); a cached setup status is never authority after waiting. Course deletion
locks its sections in stable ID order and rechecks instances before deleting. No new policy
restriction on existing setup mutations, only serialization and existing-status enforcement.

PostgreSQL uses existing row locks. SQLite must acquire a write transaction before eligibility
reads; the shared section-lock helper can issue a scoped no-op section update before refreshed
reads (actual stored values unchanged). Do not roll back caller work to obtain this boundary.
A missing section returns existing not-found semantics. One compliant route is a shared helper
used by every named mutator, then session-owned run construction inside start's transaction.

Reset takes its existing instance lock and does not take section locks: if reset wins, start
sees clean setup and can start; if start wins, reset refreshes active status and refuses. No
instance→section lock acquisition is introduced. Existing host edit/schedule run order stays.
To distinguish old progression from a newly started generation after reset, capture
instance.started_at at manual advance and scheduler operation entry. Pass expected_started_at
into SimulationService.patch_sheet, lock, reopen and advance as applicable. Under the acquired scoped run lock, compare a
fresh scalar instance timestamp before ANY mutation (including retry path). This comparison
must not acquire an instance row lock: reset instance→run ordering cannot be inverted. A
sentinel distinguishes omitted legacy internal callers from explicitly expectedNone; production
API and scheduler mutation callers always supply the captured expected value. Runtime
controls/platform/components/rollout patch, review lock, standalone staff lock/reopen, staff
advance and scheduler calls all participate. Host _require_editable performs the equivalent
fresh scalar generation comparison after obtaining its run lock, before metadata mutation.
This protects requests already in flight when reset/start occurs. A stale browser tab that
sends a NEW request after the new start currently supplies no generation token: that separate
client API versioning issue is explicitly deferred, owned by platform/API under READY-START-CLIENT.
Do not claim stale-tab protection or introduce a silent client payload change. Normalize SQLite naive UTC and
PostgreSQL aware UTC timestamps consistently before comparison. Mismatch raises a controlled
SimulationError round_state/generation, mapped409 by manual API; scheduled mutation records
failure without new-generation writes. Scheduler captures once per operation, not after a
wait/reload that could replace the generation. Retain manual final timestamp comparison under
its final instance lock along with the existing run fence. A changed start timestamp yields409 without altering the new
instance. Tests pause before service.lock, between lock and advance, before a later team's
lock, and after final service commit; reset→start→optional new advance, then resume old
request. It cannot lock/advance a new-generation run, even if IDs/round/revision match, or publish
its old result as successful against the new generation. Do not require new schema columns.

## New API and UI contract

GET `/instructor/instances/{id}/start-readiness` (same `/api` prefix as existing routes):
`{instance_id,status,pack_digest:string|null,total_rounds,ready,blocked_reasons:[string],
strategies:[{key,label}],teams:[{team_id,name,student_count}]}`.
Registered strategy labels use authored labels.strategies, with formatted-key fallback; no synthetic strategy. This is
read-only advisory state; POST revalidates under locks. Missing/invalid registry/digest or
horizon disagreement return ready=false with meaningful reasons, not a plausible fallback.
Unauthorized/not-found retain existing403/404. Strategy list may be empty when pack invalid.

POST `/instructor/instances/{id}/start` body:
`{confirm_instance_id:int,expected_pack_digest:string,team_strategies:[{team_id:int,strategy_key:string}]}`.
One exact entry per current team, no duplicates, unknown strategies or extra teams. Structural
invalid input and invalid strategy422; mismatched confirm422; stale digest/team set or runtime/
status/eligibility conflicts409. No silent defaults/coercion of missing strategy. Success200:
`{instance_id,status:"active",current_round:1,started_at,team_ids:[int]}`. Keys frozen for v1.

Instructor Setup adds a "Start simulation" card after team/roster setup, using existing
setup-card/form styles (reference frontend/src/pages/InstructorSetup.jsx). In setup, show
readiness reasons and one required strategy selector per team. Disabled until readiness and
all choices; no automatic selections. Start button opens confirmation showing section, pack,
round count and chosen strategies. Pending request disables submit/close/backdrop/navigation
that would change section selection until completion; errors preserve choices. Success text
"Simulation started. Round 1 is open." and link "Open round controls". After refresh an
active/paused/completed/archived instance shows status and round-controls link, no start form.
No raw JSON/digests or implementation instructions as primary product copy.

## Files, verification and exclusions

Allow instructor API/setup page, shared platform services, simulation initialization helper,
manual advance and scheduler generation fences, runtime_controls/platform/components/
rollout/review and host API generation propagation, focused tests, fixture inventories when truly necessary,
client helper if useful, docs/CONTRACTS/findings. No migration, scoring rule change, shortening
horizon, roster provisioning/CSV, student pre-start page, automatic scheduling, AI or archive.

| Gate | Evidence / deliberate failure |
|---|---|
| Atomic correct initial state | Actual migrated SQLite/PG, multiple teams with different strategies; checkpoint0/digest and sheet1 equal direct initialize. Inject second-team failure after first writes, require entire snapshot unchanged; no perteam commit |
| Eligibility/auth/payload | Every rule above, wrong instructor/TA/student, missing pack/mismatch/horizon, empty/underfilled/unassigned/invalid roster, stale teams/digest/duplicate/missing/unknown strategies; exact unchanged target/foreign snapshots |
| Existing residue/retry | Each runtime-table sentinel blocks start; reset then start succeeds. Double-click/active/paused/completed/edited/advanced retry refuses and preserves timestamp/state |
| PostgreSQL races | Dedicated guarded target prefix mis_sim_verify_instructor_start_: duplicate start, reset both orders, stale-identity team/create and enrollment mutation, binding/delete; observe locks with barriers, prove exactly the documented outcomes and no deadlock |
| Old progression | Before-lock, between-lock/advance, later-team and final-response barriers; reset/start matching IDs+revision, optionally advance new run, resume old manual/scheduler operation; controlled conflict and exact new generation snapshot unchanged |
| Predecessor failure | New start route/browser action absent on predecessor; atomicity test fails with a planted per-team commit; stale-status mutation test fails without refresh/section lock |
| Browser | Fresh ordinary instructor setup, explicit team strategies, start through UI, refresh, assigned student login sees intended strategy/capital, save/lock, actual staff advance and debrief result; blocked and duplicate paths; diagnostics/screenshots at wide+narrow widths |
| Completion | Full make check all required PG targets/no skips, frontend lint/build, independent backend/browser audit and hashes; README/BATTLECARD/TODO current |

## Executable evidence homes and documentation delta

New `backend/tests/test_instructor_start.py`: atomic initialization, failure, eligibility,
strategy parity, runtime inventory and replay; real migrationsSQLite/guarded PG fixtures.
New `backend/tests/test_instructor_start_api.py`: real HTTP auth/readiness/start/invalid body.
New `backend/tests/test_instructor_start_concurrency.py`: PostgreSQL barrier scenarios with
observed lock waits, including all four old-manual boundaries and real scheduler generation. Parametrized HTTP
barriers cover all named in-flight student/staff writes, plus direct mismatched-generation
patch/lock/reopen/advance checks. Snapshot equality, not only HTTP409, is required.
`frontend/tests/instructor-start-proof.mjs`: seeded identities/binding only; browser creates/
assigns teams and starts, then student/round-control playthrough and console/network evidence.
Existing service/scheduling fixtures can accept optional expected generation kwargs without
weakening assertions; add coverage proving each real production caller passes it.

Run from backend: `SECRET_KEY=test PYTHONPATH=. python3 -m pytest -q
 tests/test_instructor_start.py tests/test_instructor_start_api.py
 tests/test_instructor_start_concurrency.py`; provide dedicated
`INSTRUCTOR_START_POSTGRES_URL=postgresql+asyncpg://USER:PASS@127.0.0.1:PORT/mis_sim_verify_instructor_start_build`.
Final root `make check` also supplies HOST_SCOPE_POSTGRES_URL, HOST_LIFECYCLE_POSTGRES_URL and
M5_POSTGRES_URL to separate local disposable targets. Frontend `npm run lint`, `npm run build`,
then `node tests/instructor-start-proof.mjs` against the recorded fresh seed/API/UI targets.
Closing report `docs/instructor-start-2026-10-06.md` maps every table row above to PASS/FAIL and
raw commands, logs/screenshots; no declaration of completion before both independent audits.

Exact CONTRACTS addition, Instructor start v1: "Instructor owner/admin starts only a clean,
eligible setup instance, using one explicit authored initial strategy per team. All run1,
checkpoint0, sheet1 and active-instance writes share one transaction. Strategies are genuine
initial state; subsequent changes retain authored costs/disruption. Nonsetup repeats409 and
preserve evidence. Setup mutations serialize on a refreshed section boundary; generation-aware
manual/scheduled lock and advance reject stale started_at within the run transaction; all in-flight versioned sheet/host writes also carry captured generation. New requests from stale browser tabs are not generation-token protected in v1. Start
preserves pack/settings/roster and creates no schedules. Instance horizon must equal authored
pack horizon. Verification: test_instructor_start*, instructor-start-proof.mjs and dated audits."

No implementation yet. Independent dispatch review must close this proposed contract first.

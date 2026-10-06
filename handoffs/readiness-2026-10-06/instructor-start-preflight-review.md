# Instructor start — independent preflight review

2026-10-06 · Reviewer `/root/contract_review`. Read-only preparation for the author; this is
not a dispatch specification or an implementation approval. No application changes made.

The missing start workflow is not just a route wrapper. It must settle initial strategy,
transaction ownership, setup mutation concurrency and repeat-start behavior before dispatch.

## Verified boundaries and required decisions

1. **Initial strategy is already a scored decision.** `simulation/estate.py:39–68` requires
   a valid pack strategy and stores `strategy_declared_round=0`. There is no neutral/absent
   strategy in this state contract. `simulation/organisation.py:318–331,486–487` treats a
   different round-one declaration as a strategy change: it charges the selected strategy's
   reopen cost and adds authored resistance shock. In Riverside these are80000 and0.1
   (`packs/riverside_grocery/strategies.yaml:49,84,117,148`; `runtime.yaml:688`). Declaring the
   same key leaves declared_round0. The student Strategy panel requires an initialized sheet
   (`api/runtime_controls.py:218–227`; `frontend/src/pages/Controls.jsx:35–63`), so it cannot
   supply a pre-initialization choice today. The seed hardcodes cost_leadership
   (`scripts/seed_readiness_demo.py:70–78`); this is demo policy, not an approved default.
   **Author must choose:** an explicitly inherited company strategy with disclosed switching
   consequences, instructor-supplied per-team choices, a pre-start student declaration flow,
   or a separately reviewed change to first-declaration scoring. Never silently choose the
   first catalog strategy or copy the seed's hardcoded value. Legacy `pack.yaml` initial_state
   describes existing seeded context and is not automatically the Simulation v1 initial rule.

2. **Atomic start cannot loop over today's public initialize method.**
   `SimulationService.initialize` owns a new connection/transaction per team, rejects existing
   legacy/runtime rows, writes run/checkpoint0/sheet1 and computes a full preview before commit
   (`simulation/service.py:131–168,261–297`). It does not lock/activate the parent instance or
   validate its pinned digest against the supplied pack. A late team failure leaves earlier
   teams committed if called repeatedly. Holding a separate async write transaction while
   invoking it is also incompatible with SQLite's single writer. **Author must settle:** one
   batch transaction versus explicit resumable partial start, status/round/timestamps on each
   outcome, supported retry behavior, and the service refactor/transaction boundary permitted.
   Avoid an HTTP timeout/retry being interpreted as permission to recreate or clear runs.
   Initialization's full `_view` invokes `_quote` (`:242–246`), so define the start response
   without assuming full previews are cheap while setup locks are held.

3. **Start must join the existing reset/final-reconciliation instance fence.**
   Reset now refreshes `SimulationInstance` with NO KEY UPDATE, locks schedules then runs,
   deletes scoped runtime and retains its lock through caller commit (`services/platform.py:
   426–450`). Manual final reconciliation refreshes the same instance and scalar run evidence
   before publishing status (`api/runtime_round_control.py:167–185`). A new start must not
   recreate a run between reset and reconciliation or publish active after a later reset.
   **Required:** a documented lock order, fresh status/binding reads, tests of start/start,
   start/reset and start/manual reconciliation, and controlled behavior when reset wins.
   A run-row lock alone cannot serialize the initially empty instance.

4. **Instance locking alone does not freeze the roster or binding.** Team creation locks
   Section but reads instance first; rename reads instance without a lock. Enrollment creation
   checks setup without a shared parent lock; assignment locks Section then reads instance
   (`services/platform.py:175–211,234–317`). Pack binding checks setup/round and then flushes
   without a locking refresh (`:147–158`). Consequently a request that observed setup before
   start may commit a new team, move a student, or change pack binding after start's eligibility
   snapshot. Some requests already carry an identity-mapped instance from dependencies.
   **Required:** author the common serialization/refresh protocol for all participating
   setup mutations, not just start; freeze a deadlock-safe Section/Instance ordering and
   test both orderings of team creation, assignment, enrollment creation and rebinding.
   Do not fix only the newer instructor routes: legacy `/instances/.../teams` and
   `/sections/.../enrollments` still call the same services (`api/platform.py:252–276`).

5. **Eligibility has no current start rule.** Existing team counts count active enrollments
   without filtering enrollment role or active student user (`api/instructor.py:152–159`);
   they are display counts, not proof of eligible students. **Author must define:** whether
   every team is required, zero teams, empty/under-minimum/over-maximum teams, active unassigned
   students, inactive users/enrollments and staff enrollments. Freeze the participating team
   set atomically and reject/diagnose unsupported residue without silent omission. Scheduler
   already requires the Team-ID and initialized Run-ID sets to match
   (`scheduling/service.py:111–118`), so excluding an empty team has a downstream consequence.

6. **Pack identity and horizon must agree.** Registry resolution verifies the registry's
   identity/digest (`casepack/registry.py:105–152`); `_runtime_pack` does not compare the
   instance's pin (`api/runtime_platform.py:180–184`). Start needs the same explicit instance
   digest check that Scheduler already performs. `create_instance` currently permits
   total_rounds less than authored pack rounds (`api/platform.py:211–225`), while service
   completion uses `pack.casepack.metadata.rounds` (`simulation/service.py` final advance
   branch). **Author must resolve:** reject such setup configurations, support shorter runs
   through a separately specified horizon change, or another explicit rule. Do not overwrite
   total_rounds silently. Missing/invalid/unregistered/digest-mismatched packs leave all teams
   and the instance unchanged; preserve casepack agnosticism.

7. **Retry and historical residue need explicit classification.** Current initialize refuses
   every existing legacy row and any versioned run/sheet/checkpoint in its scope. It does not
   inspect host/schedule/grading rows. **Author must define:** pristine setup; partial prior
   initialization; exact repeat after success; repeat after student draft edits/lock/advance;
   repeat while paused/completed/archived; legacy or malformed runtime residue. A retry must
   never overwrite checkpoint0, drafts, results, current status or started_at. If the selected
   strategy changes between repeat requests, state whether this is a conflict and what
   immutable evidence proves original start intent. No persisted start receipt exists today.

8. **Instructor authorization and browser completion are separate from seeding.** The
   instructor helper `_instance_for_instructor` checks course ownership; `require_instructor`
   admits instructor/admin, whereas round-control admits assigned TAs too (`api/deps.py:
   110–120`; `api/instructor.py:218–230`). Choose and test who can start, including wrong-course
   instructor, TA, student and foreign instance. `InstructorSetup.jsx` exposes setup and
   lifecycle controls but no production start action. Freeze its eligibility/blocked/loading/
   started copy and next action; decide explicitly whether start also creates schedules or
   leaves existing manual scheduling as a separate action. No out-of-band seed may substitute
   for browser start acceptance.

## Minimum evidence for the eventual contract

- Disposable migrated PostgreSQL and SQLite, two differently bound instances, multiple teams;
  derive checkpoint0/sheet1 from actual validated runtime content and compare to direct
  initialization for each explicitly chosen strategy.
- Inject a late-team failure and verify the authored atomic/partial rule by complete persisted
  snapshots. Duplicate requests and retries preserve drafts, checkpoints, status and timestamps.
- Barrier-driven PostgreSQL races for start/reset, duplicate start, binding/team/roster mutation
  and stale identity maps; use isolated targets and verify the losing operation's response.
- Digest mismatch, invalid strategy, every eligibility class and existing-runtime class; no
  accidental casepack default, cross-instance writes or partially published active state.
- Instructor browser starts through normal navigation; assigned student logs in, sees the
  correct initial strategy and capital, saves a choice, locks, and reaches a real first result
  via instructor advance. Refresh/retry is harmless. Independent backend/browser audit and
  current full checks remain gates.

These are requirements/open decisions for root authorship, not a replacement contract. The
strategy and concurrency choices may broaden the packet beyond instructor plumbing; retain
Heavy classification wherever scored initial state or shared persistence semantics change.

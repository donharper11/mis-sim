# Instructor-start backend early review — 2026-10-07

Reviewer `/root/backend_review` is independent of implementation and contract authorship. This is an early challenge pass while the builder is still adding tests/UI, not final acceptance. Contract: `handoffs/readiness-2026-10-06/instructor-start-contract.md`. Only disposable local SQLite/PostgreSQL fixtures are authorized for the probes. No production implementation edits by this reviewer.

**Historical early verdict: NOT ACCEPTED YET.** Final candidate/tests/browser/full gate are pending. The two verified scheduler generation findings below must close before acceptance. Owner for both: instructor-start builder. Launch scope is seeded demos and our own rehearsal; live human participants are not a gate.

## START-BE-001 — Blocking correctness, original reproduction confirmed; re-review pending

Original `Scheduler.lock_now`/`advance_now` captured `SimulationInstance.started_at` only after selecting the schedule, while `tick` captured it in a later loop after collecting schedules. That permitted an in-flight operation to adopt a new generation after reset/start.

Independent executable: `PYTHONPATH=backend:backend/tests SECRET_KEY=independent-start-audit /tmp/mis-sim-readiness-venv/bin/python findings/instructor-start-2026-10-07/scheduler-entry-probe.py`. It creates a unique disposable SQLite database, migrates it, starts via the real new start service, and pauses an old `lock_now` between schedule selection and timestamp selection. Reset/start/recreate naturally reuses SQLite schedule ID1. On the original candidate, the resumed old request returned locked with no failures and locked the new generation's sheet at revision0.

Evidence in `scheduler-entry-probe.log`:

```text
schedule ids 1 1
old_operation_result {'instance_id': 1, 'round_number': 1, 'state': 'locked', 'failures': []}
new_generation_run locked locked_revision 0
```

The two logged start timestamps differ. The builder moved generation capture earlier during this audit; the companion metadata probe verifies that change now refuses the run write, but full operation coverage/re-review remains pending. A closing test must assert a controlled stale-generation outcome and exact unchanged new-generation state, not just a failed run mutation.

## START-BE-002 — Functional correctness, OPEN on intermediate capture-fixed candidate

`backend/app/scheduling/service.py:305–317` writes `schedule.lock_reason` before the service generation check, and `lock_now:358–367` commits even when the service reports a stale-generation failure. The `_service`/participant queries can autoflush that ORM mutation into a replacement schedule with the same SQLite ID. An early timestamp capture alone therefore does not satisfy the contract's "without new-generation writes" requirement.

Independent executable: `PYTHONPATH=backend:backend/tests SECRET_KEY=independent-start-audit /tmp/mis-sim-readiness-venv/bin/python findings/instructor-start-2026-10-07/scheduler-metadata-probe.py`. This pauses after entry timestamp capture and before schedule lookup, resets/starts/recreates the schedule, then resumes. The new run stays draft, but its newly created schedule changes from `lock_reason=None` to `instructor_locked`.

Evidence in `scheduler-metadata-probe.log`:

```text
old_operation_result {'instance_id': 1, 'round_number': 1, 'state': 'failed', 'failures': [{'team_id': 1, 'error': 'round_state: generation'}]}
new_schedule_reason instructor_locked
new_generation_run draft locked_revision None
```

Closure must fence schedule and participant metadata as well as scored-run mutations across every scheduler entrypoint and post-service publication boundary. The closing assertion is exact before/after equality for the new generation, including schedule/participant rows, after resuming the obsolete operation.

## Initial inspection positives and limits

The session-owned initializer preserves existing construction, explicit initial strategy and digests without per-team commits; start validates the scoped25-table inventory before construction. Shared section locking and refreshed instance reads are present for the named setup mutators. Manual/student service calls propagate captured generation, and service checks occur under the run lock before mutation/retry. These are code observations, not a final concurrency or atomicity acceptance.

Current source identity is captured in `early-backend-source-hashes.txt`; the builder is actively changing the candidate. No full make check or browser acceptance is claimed by this report.

## Intermediate re-review — same session

Contract SHA256 verified: `a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.

- The builder added entry timestamp capture and schedule/participant metadata generation fencing under the schedule row lock, with a SQLite writer reservation and no autoflush before checking. The original stale-entry/metadata scenario now returns failed `round_state: generation`; the replacement run stays draft, schedule lock reason stays null, and its entire SQL dump is unchanged (`scheduler-metadata-recheck.py/log`).
- An additional independent after-service probe completes the old service lock, then resets/starts/recreates the schedule before old participant publication resumes. The resumed old operation fails generation and the whole replacement SQL dump remains unchanged (`scheduler-post-service-probe.py/log`).
- **START-BE-003 — Functional, corrected reproducer; class regression pending.** A multi-schedule `tick` initially raised unhandled `ObjectDeletedError`: failure of the first schedule expired all ORM rows, and the loop accessed a removed second schedule outside its per-item exception boundary. The builder freezes every collected schedule's scalar identity before processing. Independent recheck returns two failed records rather than crashing, with new-generation data unchanged. Original and corrected evidence: `scheduler-multi-tick-probe.log` and `scheduler-multi-tick-recheck.log`. Owner: instructor-start builder.

All three original reproductions are now corrected by the shared implementation. Findings remain under review until permanent class-wide scheduler regression coverage and the final source snapshot are audited; this is not an instance-only closure or final packet acceptance.

Additional independent evidence:

- `start-atomicity-probe.py/log`: two real teams with different explicit strategies; second-team injected failure preserves exact full SQL dump; success creates exactly the six intended initial rows and matching state/digests; duplicate preserves exact dump/timestamp.
- `postgres-duplicate-probe.py/log`: two overlapping starts on this reviewer's dedicated PostgreSQL database, with `pg_stat_activity` confirming the duplicate waits on the section lock. Exactly one succeeds and the other conflicts, with two initialized teams and the first timestamp preserved.
- Current `tests/test_instructor_start.py` independently ran against SQLite and this reviewer's PostgreSQL target: **6 passed, 1 warning, 34.73s**. Source is still under construction; these are the initial three test families, not a claim about all required contract cases. Log: `early-service-tests.log`.

## START-BE-004 — Blocking correctness, OPEN (post-service Review publication)

`backend/app/api/runtime_review.py:169–180` writes schedule/participant lock metadata after the independently committed `SimulationService.lock`, without fencing that later publication against the captured generation. The new service argument protects the sheet transaction, but does not protect these subsequent API writes.

Independent executable `review-lock-publication-probe.py` invokes the real `lock_review` route function and real service on a migrated disposable SQLite fixture. It pauses after `lock_run` returns, performs reset→start→new schedule, then resumes the old route. Result:

```text
response_status draft
new sheet None
new schedule True new participant 0
exact_new_generation_unchanged False
```

The new generation's sheet remains unlocked, yet its schedule claims decisions are locked and its participant is stamped with the old revision. The full replacement SQL dump changed. Evidence: `review-lock-publication-probe.log`. This is not a read-only stale response; it persists contradictory new-generation state. Owner: instructor-start builder. Closing check must replay this after-service boundary and require controlled409 plus exact new-generation snapshot equality, including schedule/participants. No instance→run inversion should be introduced to fence the metadata phase.

Supplementary existing tests independently run: `test_scheduling.py` and `test_instructor_setup_api.py` yielded **12 passed, 1 skipped, 29 warnings, 8.28s**. The optional PostgreSQL test in that existing module was not enabled in this invocation; no PG concurrency claim rests on the skip. Log: `existing-scheduler-setup-tests.log`.

## Corrected publication and PostgreSQL unlock re-review

START-BE-004's real route/service replay now returns controlled HTTP409 (`round_state/generation`) and preserves the exact replacement database dump. The new schedule remains unlocked, participant revision remains null and sheet remains unlocked. Evidence: `review-lock-publication-recheck.py/log`. The metadata phase closes stale reads, then takes the lifecycle instance lock and compares generation before publication; SQLite first reserves its writer with a scoped no-op instance update. No service run lock is held during this phase.

The new permanent scheduler suite initially returned **13 passed, 1 failed, 116.46s** (`scheduler-class-regressions.log`). It exposed a START-BE-003 class residue in PostgreSQL `unlock`: after reopen/reset/start, accessing expired `schedule.id` before the guard raised uncontrolled `ObjectDeletedError`. The builder froze schedule identity and the entire participant/team/revision worklist before any commit; exception formatting also uses frozen team identity. The failing PostgreSQL node independently re-ran **1 passed, 16.90s** (`scheduler-unlock-recheck.log`). Full current-candidate scheduler run remains in progress.

A deliberate isolated mutation removes only `_guard_generation` and runs the actual permanent stale-entry regression. After correcting the harness's pack symlink, it fails at the intended `assert snapshot(db) == replacement` assertion. `falsify-scheduler-metadata.py/log` is valid detection evidence; earlier fixture RegistryError attempts were not accepted as falsification. Production source was not mutated.

Final bounded backend acceptance and exact source hashes are recorded in `backend-final-review.md` / `backend-final-source-hashes.txt`. Complete scheduler rerun14passed and final selected HTTP tests6passed on both engines. This supersedes the early open statuses without deleting their evidence.

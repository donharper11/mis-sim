# Instructor start — independent setup concurrency review

Date:2026-10-07 · Reviewer `/root/contract_review` · Application builder:root agent.
Reviewed accepted contract SHA `a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.
Scope:setup-mutator/start and duplicate-start serialization, cached ORM status, reset ordering.
No production code edited. Permanent independent regression tests added in
`backend/tests/test_instructor_start_concurrency.py`, importing the requested migrated
`database`, `start` and `snapshot` helpers from `test_instructor_start.py`.

## Verdict

**ACCEPT this assigned setup/start concurrency boundary. No open finding.** This is one
part of implementation review, not whole-packet or release approval. Scheduler/generation,
full API/eligibility, browser and full-gate checks remain with their assigned reviewers.
Reviewed source/test hashes are in `setup-concurrency/source-sha256.txt`.

## Independent execution

Own target: `mis_sim_verify_instructor_start_review` on local PostgreSQL port44535. It was
created for this audit, never shared with root's build target. Fixture guards require an
explicit loopback `mis_sim_verify_instructor_start_*` database; each case resets only that
fixture database's schema and migrates the real history before seeding.

```bash
SECRET_KEY=test PYTHONPATH=backend \
INSTRUCTOR_START_POSTGRES_URL=postgresql+asyncpg://readiness@127.0.0.1:44535/mis_sim_verify_instructor_start_review \
/tmp/mis-sim-readiness-venv/bin/python -m pytest -q \
  backend/tests/test_instructor_start_concurrency.py
```

**17 passed, zero skips, 40.73s**; only the existing passlib crypt deprecation warning.
`setup-concurrency/instructor-start-concurrency-review.log` preserves the result.

Each race uses separate real database sessions, retains strong references to preloaded
setup Course/Section/Instance/Team/Enrollment objects, records backend PIDs and waits for
PostgreSQL `wait_event_type=Lock` with the expected blocker in `pg_blocking_pids` before
releasing the winning transaction. A contender completing without blocking fails the test;
sleep duration is never the evidence of serialization. Bounded waits/cancellation prevent
leaked workers on failed probes.

Coverage:

- Concurrent duplicate start:one uncommitted successful start blocks the stale contender;
  after commit,the contender refuses without changing any persisted row or timestamp.
- Start wins against team create/rename,enrollment create/assignment,pack rebinding,section
  deletion and course deletion:each blocked stale setup request refreshes committed active
  state and refuses; complete snapshots remain equal to the winner's committed state.
- Each of those seven setup operations wins first:waiting start sees newly committed team,
  roster,binding or deletion evidence and refuses when eligibility/context changed. A team
  rename remains eligible and start succeeds,preserving the newly committed name and all
  unrelated rows. This verifies both conflict and legal success outcomes after a lock wait.
- Both reset/start orderings:start-first makes reset refresh active state and refuse;
  reset-first clears stale round3/timestamp/grading residue,then waiting start refreshes the
  now-clean round0 instance and succeeds. Retry remains a conflict,with exact state retained.

## Observed failing plant and restoration

An audit-only script replaced `platform.setup_instance` in memory with the same locking
query **without** `populate_existing`. It did not edit a production file or remove locks.
The enrollment-assignment race then failed with:

```text
Failed: DID NOT RAISE <class 'app.services.platform.PlatformConflict'>
1 failed,16 deselected
PASS falsification: removing refresh caused the expected concurrency regression
```

The script restores the original function in `finally`. A fresh process reran the same
selected test against unchanged production code: **1 passed,16 deselected,3.52s**.
Both logs and the reproducing mutation script are retained under `setup-concurrency/`.
This demonstrates that the regression detects the original stale-identity-map defect even
when the competing calls still acquire PostgreSQL locks.

No change to the accepted start behavior or new contract decision was needed. The tests
verify existing shared section/instance ordering and intentionally do not claim SQLite row
locks or generation-token protection for new requests sent from stale browser tabs.

# M2 packet 2.3 amendment — deterministic round scheduling

Date: 2026-09-15  
Authority: supervisor, following the M2 reconciliation and independent scheduling review  
Base: `774952d` (M2.4 auth/login accepted and pushed)

This amendment is binding on the historical `handoffs/2.3-round-scheduling/spec.md`.
It resolves the legacy `RoundRunner` versus production `SimulationService` ambiguity,
per-team participation, schedule state, fixed-time entrypoint, and partial-failure rules.

## Production boundary

The scheduler calls the M1 `SimulationService` boundary. It resolves the registered
`RuntimePackV1` for the `SimulationInstance` tuple `(pack_key, pack_version)` through the
M2.5 registry and verifies `simulation_instance.pack_digest` before any team operation.
The legacy `RoundRunner` lock/advance API remains an audited 1.6 path and is not called by
2.3. No changes to `backend/app/round/runner.py` or `backend/app/simulation/service.py`
are permitted.

For each initialized team in deterministic ascending `team_id` order, the scheduler reads
the current production run, calls `SimulationService.lock(instance_id, team_id, round,
expected_revision)`, records the returned `locked_revision`, and after the grace threshold
calls `SimulationService.advance(instance_id, team_id, round, locked_revision)`. A matching
already-advanced result is an idempotent success; pack mismatch, revision mismatch, missing
run, or invalid round is a failed team operation.

## Schedule schema and participant snapshot

The migration adds:

```text
round_schedule
  id, instance_id FK → simulation_instance.instance_id NOT NULL,
  round_number >= 1, start_at timestamptz NOT NULL, deadline timestamptz NOT NULL,
  auto_advance boolean NOT NULL, grace_period_minutes integer NOT NULL,
  decisions_locked boolean NOT NULL default false,
  lock_reason nullable, locked_at nullable timestamptz,
  advanced_at nullable timestamptz,
  claim_token nullable, claim_until nullable timestamptz,
  UNIQUE(instance_id, round_number),
  UNIQUE(id, instance_id)

round_schedule_team
  schedule_id, instance_id NOT NULL, team_id,
  FK(schedule_id, instance_id) → round_schedule(id, instance_id),
  FK(team_id, instance_id) → team(id, instance_id),
  locked_revision nullable integer, locked_at nullable timestamptz,
  advanced_at nullable timestamptz,
  PRIMARY KEY(schedule_id, team_id),
  ON DELETE CASCADE from schedule, ON DELETE RESTRICT from team
```

All timestamps are timezone-aware and normalized to UTC. Naive timestamps, `deadline <=
start_at`, nonpositive duration, rounds outside `1..total_rounds`, and rounds beyond the
registered pack's authored count are rejected. `lock_reason` is only `deadline_expired` or
`instructor_locked`; advancement is represented by `advanced_at` and never overwrites the
original lock cause. The `team(id, instance_id)` uniqueness target is created by the
reversible migration so a participant row cannot cross instance boundaries.

Creating a schedule snapshots exactly the initialized production participants for that
instance: `simulation_run_v1` rows joined to platform `team` rows on both `team.id` and
`team.instance_id`. A schedule is rejected if either side has an unmatched row; legacy
`TeamStateRow` and `RoundRunner` rows are never participant sources. A team created later is
not a participant in an existing schedule;
the schedule may be replaced only by an explicit future packet. A schedule with no
initialized teams is rejected. This makes participant membership and retry behaviour
deterministic without modifying platform team creation.

## Timing and resumable idempotency

The service entrypoint is:

```text
Scheduler.tick(now: aware UTC datetime)
```

It never reads the clock. The only clock-reading boundary is
`python -m app.scheduling.entrypoint`; `--at 2026-09-15T12:00:00Z` bypasses clock access
for reproducible evidence. Due rows are processed by `(instance_id, round_number)`.

- before `start_at`: no-op;
- at or after `deadline`: lock all snapshot participants;
- at or after `deadline + grace_period`: advance only when `auto_advance` is true;
- zero grace permits lock and advance in one tick;
- manual lock before the deadline sets `instructor_locked`, and a deadline never overwrites it;
- `auto_advance = false` remains locked;
- repeated ticks do not duplicate locks or results;
- a team failure leaves completed participant rows intact, leaves the schedule incomplete,
  and returns a deterministic failure report; a retry resumes from the first incomplete team;
- `round_schedule.decisions_locked` becomes true only after every participant is locked;
- `round_schedule.advanced_at` becomes non-null only after every participant advances;
- unlock/reopen is allowed only before any participant advances and resets the schedule and
  participant lock state; after any advancement it is refused.

`tick` serializes workers with a database claim, not an in-memory mutex. A due schedule is
claimed by one conditional update that sets a unique `claim_token` and a fixed 60-second
`claim_until`,
then commits before participant work begins. A second worker whose update affects zero rows
returns a deterministic busy/no-op result. A worker may reclaim an expired claim; every
participant mutation is conditional on the current claim token. The worker clears its lease
only with `UPDATE round_schedule SET claim_token=NULL, claim_until=NULL WHERE id=:schedule_id
AND claim_token=:worker_token`; a stale worker therefore cannot clear a newer claim. An
expired claim is the recovery path for process failure. Before invoking the separately
transactional `SimulationService.lock` or `.advance`, the worker must conditionally verify
ownership of the current claim token; a lost claim records `schedule claim lost` and does
not invoke the production service.

Instance settings provide defaults only: positive `default_round_duration_hours`, boolean
`auto_advance_on_deadline`, nonnegative `grace_period_minutes`, and nonnegative
`lock_warning_minutes`. Schedule creation copies the selected grace value into
`round_schedule.grace_period_minutes`; once a row exists, its persisted values are
authoritative even if instance settings later change.

## Service surface and seed

Implement `set_schedule`, `bulk_schedule`, `lock_now`, `advance_now`, `unlock`, `status`,
and `tick`. `lock_now(instance_id, round_number, at)` and
`advance_now(instance_id, round_number, at)` require an explicit aware UTC `at` value and
never read the clock. `bulk_schedule` creates rounds `1..total_rounds`, sets each deadline from the
positive duration, and starts the next round at the prior deadline plus grace. Duplicate
rows are refused. Completed rounds are reported deterministically when skipped.

Extend the deterministic local demo with `--cohort --schedule`: it creates schedules for
the two accepted registry-bound instances, then demonstrates a fixed-time deadline lock,
one grace-period auto-advance, and no auto-advance for the disabled instance. Auth/browser
canaries are N-A; 2.4 is already accepted.

## Required evidence

- fresh migration upgrade → downgrade → upgrade and schema guard;
- fixed-time tests before deadline, at deadline, grace boundary, zero grace, no schedule,
  past deadline, manual lock, unlock refusal, completed rounds, and duplicate refusal;
- 50 repeated identical ticks with one canonical state hash;
- two instances with different registered packs and at least two production teams each;
- resumable partial-team failure and concurrent tick idempotency;
- registry digest mismatch refusal and pack-resolution proof;
- fixed-time `--at` entrypoint with one clock read at the boundary;
- deterministic `--cohort --schedule` evidence and the existing instance-isolation canary;
- full `make check`.

The packet does not edit `RoundRunner`, `SimulationService`, runtime tables, engine/scoring,
auth, frontend, or casepack registry implementation.

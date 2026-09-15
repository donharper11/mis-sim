# Round scheduling operations

M2.3 schedules are persisted per simulation instance. Create them through
`Scheduler.set_schedule` or `bulk_schedule`; `grace_period_minutes` is copied onto
each row and remains authoritative if instance settings change. `start_at`, `deadline`,
and manual `at` values must include a UTC offset.

The fixed-time command is deterministic and is suitable for cron or a deployment job:

```bash
python -m app.scheduling.entrypoint --instance 12 --at 2026-09-15T12:00:00Z
```

With no `--at`, the command reads the clock once at the CLI boundary. The scheduler
itself never reads a clock. It locks initialized teams in ascending team ID order and
calls the production `SimulationService` after resolving and digest-checking the
registered runtime pack.

Workers claim due rows with a database lease lasting 60 seconds. A busy claim is a
deterministic no-op; an expired claim can be reclaimed. Participant writes and lease
clearing are conditional on the worker token. A failed team leaves earlier successful
team rows intact, so the next tick resumes from the first incomplete participant.

Useful manual controls are `lock_now(instance_id, round_number, at)`,
`advance_now(instance_id, round_number, at)`, `unlock`, and `status`. Reopening is
allowed only before any participant advances.

The historical `BECSR/async-round-deadlines.md` source is unavailable in this checkout;
the M2.3 amendment and dispatch are the binding contract.

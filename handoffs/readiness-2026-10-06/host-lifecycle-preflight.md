# Host lifecycle follow-up — inspected boundary, not dispatch approval

Date: 2026-10-06. Scope implementation is in independent audit. This note records the
next investigation so a successor does not treat lifecycle as a one-line status update.
No lifecycle implementation or new scoring decision has been made here.

Verified production paths:

- `SimulationService.advance` owns the locked run transaction and immutable result/checkpoint
  commit. Both instructor round-control and `SchedulingService._advance` call it.
- After a non-final advance run.current_round becomes n+1. At final advance it remains the
  final round and run.status becomes completed. The instance display pointer can lag the
  run under scheduler advancement; host creation/member assignment currently use that pointer.
- `_require_editable` already locks the team's run, but returns no authoritative round.
  Returning the run permits creation/assignment stamps to use the actual current round.
- UI permits only pending-host additions; server update/add/remove currently lacks a
  pending-status guard. A lifecycle transition requires that guard as well as presentation.
- `reset_instance` only permits setup status. It deletes modern simulation, scheduling,
  grading and RoundResult rows, but omits host/member and other historical round tables.
  Modern initialization creates no legacy estate rows; however it explicitly refuses any
  legacy rows, so historical reset cleanup is a separately relevant correctness boundary.

Required author decisions before next dispatch:

1. Specify pending→active timing using actual run progression, including final-round-created
   hosts whose activated_round is beyond the game horizon. Keep metadata out of scoring.
2. Put manual and scheduled activation in one transaction with progression, and define
   idempotent retry/failed advance behavior. Do not add two independent post-commit updates.
3. Decide how already-overdue historical pending hosts are reconciled, including completed
   games. A new transition alone does not repair historical pending metadata automatically.
4. Define reset's full inventory, round/timestamp postconditions and serialization with
   advancement; preserve roster, course, team, settings and pack bindings.
5. Enumerate minimal harness schemas affected by adding host-table access to SimulationService:
   test_simulation_service.py, test_simulation_games.py, test_simulation_portability.py and
   test_round_control_api.py have explicit table lists. Do not silently weaken production
   behavior by swallowing a missing-table error or checking for schema existence each round.
6. Freeze negative tests for pending-only writes, stale instance pointer, failed/retried
   advancement, scheduler/manual parity, other teams/instances and reset remnants. Preserve
   exact checkpoint/result payloads and existing deterministic game evidence.

The approved scope migration does not settle these lifecycle decisions. Owner: next host
lifecycle contract author; future independent reviewer must gate dispatch before changes to
shared progression/persistence. Instructor start/initial strategy and SQLite archive repair
remain separate tasks in TODO, not hidden additions to this packet.

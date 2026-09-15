# Frontend dashboard

M3.3 replaces the M3.2 shell placeholder with the first live student read surface. The root
route still loads the authenticated identity, instance and schedule through the shell, then
reads `GET /api/instances/{instance_id}/dashboard` for the team view.

The dashboard response is a projection of persisted runtime records:

- `RoundResult.payload.scorecard` is the source for the four Balanced Scorecard tiles.
- `RoundResult.payload.signals.open`, or the persisted `signal` rows when the payload has no
  open bucket, is the source for open signals.
- `team_state`, `deployment_org_state`, `arch_node`, and `org_unit` provide the unit-response
  chain, including running assets, training, process, adoption, people, and capabilities served.
- The versioned `simulation_run_v1` and `simulation_checkpoint_v1` records are supported as a
  read fallback while the platform carries both runtime persistence paths.

The route is scoped by `get_current_instance`. Students receive only their active enrollment's
team; staff may receive the teams visible in the authorized instance. The route never calls the
scoring engine and never writes a decision, checkpoint, or result. Missing runtime records remain
nullable or render as an honest empty state.

The page follows the approved hierarchy: attention first, unit-response chain as the centrepiece,
then the scorecard and open-signal context. It does not copy static mockup values into runtime.

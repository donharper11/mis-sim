# Frontend Rollout

M3.6 adds the Rollout route at `/rollout` and the scoped endpoint
`GET /api/instances/{instance_id}/rollout`. The deployment table projects active catalog
assets with their people, training coverage, process choice, communication choice, adoption,
and status. Registered casepack training and process options are exposed alongside the
runtime people communication options.

The deployment detail surface sends `train`, `set_process`, and `communicate` commands as
typed category patches through `SimulationService.patch_sheet`. Revision conflicts, locked
rounds, uninitialized runtimes, affordability, and invalid references remain backend
outcomes. Communication choices in the current sheet are reflected immediately; the
checkpoint remains authoritative for advanced rollout state.


## October 6 readiness corrections

The current deployment tabs display local-font slider cards. Selected options determine
cost; unsupported arbitrary budget inputs have been removed. `RolloutTeamOut.selected_commands`
returns the scoped current sheet so the UI can restore saved choices and preserve other
assets when replacing a category. Communication remains per business unit. Checkpoint
training/adoption describe advanced state, while selected commands describe the draft.

Deployment cost metadata reads `CatalogItem.deployment_modes[placement]`; a deployment-specific
host assignment takes precedence over a catalog fallback. The platform detail link receives
the real platform projection and is read-only. Closed rounds reject both simulation patches
and host-platform metadata writes. No scoring formula was changed by these corrections.

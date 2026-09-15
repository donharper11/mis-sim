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

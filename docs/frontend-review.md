# Frontend Review & Lock

M3.7 adds the Review route at `/review` and the scoped runtime endpoint
`GET /api/instances/{instance_id}/review`. The decision sheet groups the current typed
commands by category and reads capital spend, remaining capital, operating run-rate, and
warnings from the engine preview. It does not recalculate those values in the browser.

`POST /api/instances/{instance_id}/review/lock` calls `SimulationService.lock` with the
current sheet revision. The response becomes locked only after the service transaction
accepts the revision; schedule participant state is then updated when a schedule exists.
Stale revisions, unavailable packs, uninitialized runs, and already-locked rounds remain
explicit errors.

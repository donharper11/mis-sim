# Frontend Platform

M3.4 adds the Platform route at `/platform`. It uses the authenticated shell and reads
`GET /api/instances/{instance_id}/platform` for the selected team. The response is a projection
of the versioned runtime checkpoint and current decision sheet:

- active service assets are grouped by cloud and on-premises placement;
- capacity and utilisation are shown only when persisted records supply them;
- pending projects, connections, and unprovisioned registered services remain visible;
- pack labels are read from the registered casepack label map;
- an absent split rule is shown as unavailable rather than filled with mockup prose.

When a team has an initialized, unlocked `SimulationRunV1`, the add-service form sends a typed
`platform_service` patch through `PATCH /api/instances/{instance_id}/platform`. The backend
validates the command with `SheetPatchV1` and delegates the mutation to `SimulationService`,
including its revision and affordability checks. Uninitialized, locked, unregistered, or
unavailable runtimes remain read-only with an explicit explanation.

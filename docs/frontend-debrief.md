# Frontend Debrief

M3.8 adds the Debrief route at `/debrief` and the read-only endpoint
`GET /api/instances/{instance_id}/debrief`. It projects immutable `RoundResult` payloads;
the browser never recomputes scores, costs, events, or causal factors. The latest round
shows the balanced scorecard, firm score, capability throttle, state changes, events,
financial result, and technical debt. Earlier persisted rounds remain available in the
same report.

`GET /api/instances/{instance_id}/debrief/download` returns a plain-text business status
report with an attachment disposition. A team with no advanced result receives an honest
empty state instead of invented initial results.

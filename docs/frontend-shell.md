# Frontend shell

The authenticated root route loads identity from `/api/auth/me`, then reads the selected
instance, current schedule, and dashboard projection through the M2-scoped API boundary. It
renders the approved sidebar groups, top bar, round context, and capital/status strip. Capital
and run-rate values come from persisted team runtime state when available; missing values remain
visibly unavailable and no fixture value is substituted.

The body is the M3.3 dashboard read surface. Route protection clears the session token and
returns to `/login` on 401/403 responses. The schedule response is nullable, so setup instances
without a published round remain usable and show an open/unavailable state. Dashboard runtime
records are likewise nullable and render explicit empty states.

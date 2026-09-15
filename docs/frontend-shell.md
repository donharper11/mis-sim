# Frontend shell

The authenticated root route loads identity from `/api/auth/me`, then reads the selected
instance and current schedule through the M2-scoped API boundary. It renders the approved
sidebar groups, top bar, round context, and capital/status strip. Missing capital and estate
values remain visibly unavailable until their production producers are exposed by later M3
packets; no fixture value is substituted.

The current body is a placeholder for packet 3.3's dashboard. Route protection clears the
session token and returns to `/login` on 401/403 responses. The schedule response is nullable,
so setup instances without a published round remain usable and show an open/unavailable state.

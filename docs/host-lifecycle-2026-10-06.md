# Host activation and reset — 2026-10-06

Status: ACCEPTED. READY-002 closed. Branch `build/readiness-2026-10-06`, checkpointed at user request.
No merge to main or deployment. This successor to accepted host scope0012 owns READY-002.

## Contract and changes

The [independently accepted contract](../handoffs/readiness-2026-10-06/host-lifecycle-contract.md)
fixes lifecycle behavior without changing scoring. Valid due pending hosts become active in
SimulationService.advance's transaction, shared by manual and scheduled progression. The
last round does not open another round. Host creation and member assignment derive their
round from the locked team run; active/retired host edits are refused.

Migration0013 repairs valid overdue pending statuses using scoped runs. It changes status
only; downgrade preserves that repair because prior statuses cannot be reconstructed.
Timing arithmetic widens to BIGINT before addition, including malformed INTEGER extremes.

Setup reset clears all 25 runtime tables, resets the display round and timestamps, and
preserves pack binding, settings, teams, roster and identities. PostgreSQL locks serialize
reset against host edits and advancement. Manual advancement refreshes runs under a final
instance lock, so a delayed request cannot restore the instance after a committed reset.
A multi-team manual advance remains a sequence of team transactions; it is not all-or-nothing.

## Verification

- Independent specification review caught a late manual status-write/reset race and integer
  overflow exposure before implementation; both contract findings were resolved.
- Existing focused service/round-control/lifecycle regression: 25 passed, 44 warnings.
- New SQLite/PostgreSQL lifecycle tests cover timing, exact status repair, immutable result
  parity, rollback, final horizon, pending-only writes, reset inventory and concurrency.
  Final full gate: **834 passed, no skips, 226 warnings, 1208.74s; all guards green**.
  Initial fixture defects omitted required schedule grace minutes
  and left PostgreSQL serial sequences behind explicit historical IDs. Both corrected and
  independently retested; neither required a production change.
- Independent [browser/API audit](../findings/readiness-2026-10-06/host-lifecycle-browser-review.md)
  passes: student pending→active, denied active writes, scheduler round stamps, authorized
  setup reset scope/identity preservation and active reset refusal. No browser diagnostics.
- [Isolated predecessor-behavior plants](../findings/host-lifecycle-2026-10-06/falsify.py)
  made the timing, pending-only write and reset-inventory acceptance assertions fail.
  Production source remained untouched by the plants.

Independent [backend audit](../findings/readiness-2026-10-06/host-lifecycle-backend-review.md)
accepts the implementation, including observed PostgreSQL lock waits and late-failure rollback.
Fresh PostgreSQL verifier passes head0013, all32 model tables and six committed legacy rounds.
Frontend lint and production build pass (bundle1105.24kB /340.52kB gzip; size warning remains).
Backend and browser reviewed source hashes still match. READY-002 is closed after the
full gate passed with dedicated, separate PostgreSQL scope/lifecycle/concurrency targets. Exact [commands](../findings/host-lifecycle-2026-10-06/commands.txt)
and raw logs are retained. Instructor initialization, SQLite archive CHECK repair,
read performance and pilot/production acceptance remain separate open tasks.

User requested a pause after this checkpoint. [Resume instructions](../handoffs/readiness-2026-10-06/NEXT-AGENT.md)
identify the next accepted contract; no instructor-start implementation has begun.

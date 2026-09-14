# Review and integration-authority ruling

Date: 2026-09-14. Normative spec candidate: `0716eb9e49f9dbe38d0505dca81f42a8c3ee3ca8`.
Independent reviewer `report_auditor`: **PASS**, all five SPEC_PROTOCOL §11 checks.
The initial return and both reproduced corrections are recorded in
[`../../../findings/recovery-scorecard-spec-2026-09-14.md`](../../../findings/recovery-scorecard-spec-2026-09-14.md).

The supervising integration agent **accepts R1–R4 as the frozen implementation contract**
under the user's authorization to establish the plan and control agent implementation:

1. Event integers are points on a 100-point scorecard; divide by 100 for runtime fractions.
2. Sum this round's fired-event points, convert once, add to the engine base, clamp once
   and round to six decimals. Invalid inputs fail; raw evidence remains inspectable.
3. Preserve the four-number scorecard map and add versioned evidence carrying the existing
   partial-financial flag. Historical unversioned payloads stay untouched.
4. Require strict integers and the four declared dimensions, preserving valid pack bytes
   and schema version 1 while explicitly tightening formerly permissive input acceptance.
   Numeric diagnostic refinement remains OS-D1/M2; unknown dimensions use E18.

These are numerical and compatibility rulings, not a strategy-balance judgment, a full
financial model, or permission to change Tech/Org/Mgmt or authored pack numbers.

**Status: reviewed contract, implementation not dispatched in this first wave.** At the
next dispatch the supervisor supplies the exact integrated base and an isolated worktree,
the five-file implementation allowlist from §4, and PF6's disposable PostgreSQL recipe.
The audited runtime/report prerequisites are integrated at `4adafd8` and `94b85e7`;
`docs/backend-development.md` is the actual runtime recipe. Create a new disposable
cluster/database; the first-wave cluster has been removed. The reachable supervisor
interpreter currently is `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`; recheck it at
dispatch rather than treating a temporary path as permanent infrastructure.

The builder must re-run all preflight rows on that exact base. Living-document deltas
in §7 land with the eventual audited implementation, so no LIVE scorecard contract is
claimed today. A different builder and an author-independent build auditor remain required.

# Scorecard implementation dispatch

Date: 2026-09-14. The user authorized continuing the controlled implementation plan.
Builder: `scorecard_builder`; worktree `/tmp/mis-sim-scorecard-build`;
branch `build/recovery-scorecard`; exact base
`c7283dc27eb0d0bf5178765d81274e5bf66ad546`.

R1–R4 are approved in `review.md`; the Heavy spec passed independent review at `0716eb9`.
The only builder files are §4's five-file allowlist: EventOutcome model, runner scorecard
boundary, the named existing event-once test, new contract tests, and the new DoD. Shared
living-document deltas in §7 and register/status changes belong to the supervisor.
No engine, pack, seed, dependency, migration, UI, state-transition or adjacent work is
authorized in this packet. Undefined semantics return to the supervisor. No subdelegation,
push, deployment or main merge. A fresh author-independent build auditor follows.

PF6 prerequisites were verified at dispatch: runtime integration `4adafd8`, report
integration `94b85e7`, and installed declared-dependency interpreter
`/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python` (Python 3.12.3, `pip check` clean).
The actual PostgreSQL command is the isolated-cluster recipe in
`docs/backend-development.md`, using `/usr/lib/postgresql/16/bin`, followed by:

```bash
python backend/scripts/check_postgres_runtime.py --database-url "$runtime_database_url"
```

The URL must identify the newly created private loopback `mis_sim_verify_*` database,
never an application default. Create another fresh database for post-build verification.
The builder owns its temporary cluster; keep it for audit, then coordinate scoped cleanup.
Never put its password in committed reports or tool output.

The builder reported all PF1–PF6 PASS before implementation: original digest and 24
payloads saved, eight invalid input probes rejected, 251 shipped event rows compatible,
14 protected pins pass, and real PostgreSQL migrations/16 scoped tables/six committed
rounds verified. The old acceptance probe fails as expected. The supervisor independently
captured all 24 persisted baseline results, engine bases and protected-file hashes at
`/tmp/mis-sim-scorecard-supervisor-evidence/before.json` before any product edits.

The deliverable is an audited implementation of this contract, including all N1–N8
evidence and living deltas. M0 can close only after that acceptance; M1 remains separate.
In parallel, `decision_inventory` has documentation-only permission for one new inventory
file in its isolated worktree. It may map M1 gaps but may not design formulas or build them.

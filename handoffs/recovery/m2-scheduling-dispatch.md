# M2 packet 2.3 dispatch — round scheduling

Date: 2026-09-15  
Base: `774952d`  
Binding contract: [`m2-scheduling-amendment.md`](m2-scheduling-amendment.md) and the historical
[`../../2.3-round-scheduling/spec.md`](../../2.3-round-scheduling/spec.md), with the amendment taking precedence.

The builder may edit only these paths:

```text
backend/alembic/versions/<new-round-schedule-revision>.py
backend/alembic/env.py
backend/app/models/platform.py
backend/app/models/scheduling.py
backend/app/scheduling/__init__.py
backend/app/scheduling/service.py
backend/app/scheduling/entrypoint.py
backend/app/seed/demo.py
backend/tests/test_scheduling.py
backend/tests/check_scheduling_invariants.py
docs/scheduling-operations.md
CONTRACTS.md
handoffs/2.3-round-scheduling/spec.md
handoffs/2.3-round-scheduling/dod.md
```

No frontend, auth, registry implementation, runtime model, engine/scoring, round-runner,
simulation-service, or unrelated migration changes. Do not add dependencies. Do not push,
merge, deploy, or edit shared status/register files. Do not subdelegate. Return unresolved
semantics to the supervisor.

Before editing, record the historical preflight results and the amendment decisions. Return
an exact candidate SHA, clean worktree, migration/test/entrypoint evidence, and any
out-of-scope observation. A fresh auditor will inspect the exact SHA, run the fixed-time
and isolation probes, and run the full repository gate before acceptance.

Preflight must record that `BECSR/async-round-deadlines.md` is unavailable in this checkout;
the amendment is the binding replacement for its adopted scheduling decisions.

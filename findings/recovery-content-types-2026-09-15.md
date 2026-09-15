# M1 P1 content/types final audit — PASS

Date: 2026-09-15
Auditor: `/root/m1_p1_content_auditor`
Candidate: `e4f4757df920a6a6cf2be87ae30f3997f5f7d164`
Audit tree: `/tmp/mis-sim-m1-p1-content-v4`
Exact base: `5d6cbc62a6a5cf6bfadfca035c71c362384474ba`

## Decision

**PASS.** The candidate closes all previously reported checkpoint DTO, numeric/key/enum,
unpriced-shape, join/edge-semantics, inventory, and TCO-identity findings.

## Scope

The exact diff contains only the six permitted additions:

```text
backend/app/simulation/__init__.py
backend/app/simulation/content.py
backend/app/simulation/types.py
backend/packs/riverside_grocery/runtime.yaml
backend/tests/test_simulation_content.py
handoffs/recovery/decision-evolution/content-types/dod.md
```

`git diff --check` passed and the candidate worktree was clean before and after all audit
commands. No candidate or root files were modified.

## Independent evidence

Environment: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`, `PYTHONPATH=backend`.

- Focused P1/P0/legacy pins: **321 passed**.
- Supervisor `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend make check`:
  **618 passed**, all guards green, all 44 fixtures green.
- Riverside validator: **0 errors, 0 warnings**, exit 0.
- Runtime smoke: **14 catalogs, 11 services, 10 preference rules, 131 dispositions,
  33 preference views, 13 response dispositions, 10 drivers, 11 people units**.
  Dispositions: `live_v1=73`, `context_m4=58`, `no_preference=0`.
- Exact TCO estimator map and all 13 response dispositions passed; preference source-leaf
  inventory and pointer checks passed without broad view fanout.
- Direct malformed probes rejected bool/string/nonfinite/negative numeric values, long and
  malformed machine keys, bad enums, malformed `UnpricedSignalExposureV1`, duplicate
  topology, self/unknown connection endpoints, invalid network/integration edge metadata,
  unknown staff-order joins, service rollouts, duplicate primary assignments, and duplicate
  TCO rows for one asset.
- Digest/immutability checks passed: reordered YAML preserved semantic digest, a semantic
  driver change changed it, and mutating a returned runtime view did not mutate the bound
  pack. Digest: `522a8f2bb68675d84e8baf197eadb8d4462ea79d8399896957117f4d56943540`.
- Disposable strict-config and metric-kind guard mutations each failed the focused tests.
  The unmodified candidate P1 suite passed after restoration: **14 passed**.

No open P1 content/types findings remain on this exact candidate.

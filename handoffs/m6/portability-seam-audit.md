# M6 portability seam audit

Date: 2026-09-18  
Parent: `34efa48`  
Corrections audited: `c1f8715fa8ba44821ab695411ee85b4aeb363c21`, `4362b9884794e4fc5011e5f0b944bc9e989d7e4c`

## Verdict

**PASS for the corrected capability-validation and production binding seams; FAIL for the M6 portability gate.** `c1f8715` makes unbound `CheckpointStateV1` validation reject a capability outside the legacy fallback vocabulary and makes `RuntimePackV1.validate_state()` accept the currently bound pack vocabulary. `4362b98` propagates that bound helper through initialize, transition, checkpoint/read, and service paths, with a synthetic pack-bound end-to-end test. M6 still lacks a substantive second vertical and retains runtime-preference/documentation blockers.

## Final correction re-audit: `4362b98`

The prior direct-call residual is closed. `rg` now shows all production state reconstruction paths using `pack.validate_state(...)` or `self.runtime_pack.validate_state(...)`; only the deliberate direct DTO tests and the helper implementation call `CheckpointStateV1.model_validate(...)` directly.

The new `test_bound_pack_initializes_and_transitions_non_riverside_capability_state` passes a synthetic casepack whose renamed capability is `banking_operations`, then verifies all three boundaries:

- `initialize_state(pack, ...)` returns a state containing `banking_operations`.
- `resolve_transition(pack, initial, [], 1)` preserves the capability.
- `SimulationService.initialize(...)` and `service.read(...)` both return the bound capability from persisted state.

This closes the previously reported production validation blocker. It remains a seam test using a transformed Riverside pack, not evidence of a substantive second vertical.

## Required seam verification

The direct probe used a state whose `governance` and `primary` maps contain only `banking_operations`:

```text
direct unknown REJECT ValidationError
direct supplied allowed ACCEPT {'banking_operations': None}
bound pack allowed {'banking_operations': None}
```

This confirms the intended split:

- `CheckpointStateV1.model_validate(base)` rejects the unknown capability.
- `CheckpointStateV1.model_validate(base, context={"capabilities": ("banking_operations",)})` accepts it.
- A `RuntimePackV1` whose casepack exposes `banking_operations` accepts the same state through `bound.validate_state(base)`.

The correction also keeps explicit rejection of a capability not in the supplied context. The test added at `backend/tests/test_simulation_portability.py:83` covers both direct and bound paths.

## Test evidence

All commands ran with `SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=.` from `backend` unless stated otherwise:

```text
python3 -m pytest -q tests/test_simulation_portability.py
4 passed in 14.65s

python3 -m pytest -q tests/test_simulation_content.py tests/test_simulation_consequences.py tests/test_simulation_service.py
34 passed in 148.94s

python3 -m pytest -q tests/test_engine_production_inputs.py tests/test_instance_isolation.py
199 passed in 2.55s
```

Riverside and the existing isolation fixture both validate and load:

```text
PYTHONPATH=backend python3 backend/bin/validate_casepack backend/packs/riverside_grocery
  0 errors · 0 warnings · exit 0

PYTHONPATH=backend python3 backend/bin/validate_casepack backend/packs/m2_isolation_fixture
  0 errors · 0 warnings · exit 0

riverside_grocery loaded 7 caps 10 initial_assets a62dcdb0c62d
m2_isolation_fixture loaded 7 caps 10 initial_assets 15b571243057
```

`test_runtime_accepts_pack_authored_non_riverside_initial_estate` passes a synthetic estate with `bank_*` asset IDs and `next_gen_firewall` as a catalog source. The source-reference negative control also passes: an unknown initial source raises `SimulationError(code="invalid_reference")`.

## Residual M6 blockers

1. **No substantive second vertical exists.** The only non-Riverside evidence is a synthetic initial-estate mutation while copying the Riverside pack; even its `bank_*` assets point to existing Riverside sources (`next_gen_firewall` and `client_network`). `m2_isolation_fixture` has the same grocery vertical and the same authored inventory shape; it is isolation evidence, not M6 second-vertical evidence. There is no hospital or community-bank casepack validated and run through the production engine.

2. **Runtime preferences retain Riverside-shaped cardinality and vocabulary.** `backend/app/simulation/content.py` requires exactly 131 preference disposition leaves, hardcodes ten stakeholder rules, and keeps a closed metric/categorical vocabulary. `_validate_against_casepack()` also requires the exact TCO estimator map and exact hiring/communication option keys. A second authored vertical cannot establish its own preference/runtime contract through the documented casepack schema without conforming to these hidden assumptions.

3. **The runtime supplement remains outside the documented casepack contract.** `load_runtime_pack()` requires `runtime.yaml`, while `docs/casepack-schema.md` documents the casepack files without documenting that required production supplement or its validation boundary.

4. **Riverside-specific fallback helpers remain.** `_default_runtime()` still contains Riverside catalog keys, drivers, estate, and preference views, and `RESPONSE_EXPLANATIONS` maps only Riverside event keys. The helper is not used by the current loader path, but it remains a future portability trap and would fail for a new event set if reused.

5. **No full zero-engine-change proof.** The corrections now prove initialize/transition/read against a synthetic bound pack, but there is no new vertical, six-round playthrough, deterministic replay, pack-digest comparison, causal-trace check, or clean production-engine run demonstrating the M6 acceptance path.

## Commands used for direct verification

```text
PYTHONPATH=backend python3 - <<'PY'
from pathlib import Path
from app.simulation import load_runtime_pack
from app.simulation.types import CheckpointStateV1, RuntimePackV1
# construct base with banking_operations in governance/primary,
# call direct model_validate, context-bound model_validate, and
# RuntimePackV1.validate_state with a synthetic bound casepack
PY

rg -n "runtime_pack\\.validate_state|CheckpointStateV1\\.model_validate" backend/app/simulation
```

The latter now produces `pack.validate_state(...)` in estate/consequences and `self.runtime_pack.validate_state(...)` in service, plus the direct DTO calls inside the helper and tests. No unbound service/consequence state reconstruction remains.

M6 remains **NOT READY**. The final correction closes the targeted M6-002 production binding seam, but a substantive second vertical and the runtime preference/documentation contract are still required before claiming portability.

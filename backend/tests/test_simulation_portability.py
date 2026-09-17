"""Bounded M6 runtime portability probes.

These tests exercise the runtime boundary with a deliberately different
initial estate while keeping the Riverside casepack as the source catalogue.
The later M6 pack will replace the source content; this seam proves that the
loader is no longer coupled to Riverside's initial source keys and IDs.
"""

from copy import deepcopy
from pathlib import Path
import shutil
import tempfile

import pytest
import yaml

from app.simulation import load_runtime_pack
from app.simulation.types import CheckpointStateV1, SimulationError


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


def _runtime_with_authored_non_riverside_estate(raw: dict) -> dict:
    result = deepcopy(raw)
    result["initial"]["assets"] = []
    for index in range(10):
        if index % 2 == 0:
            result["initial"]["assets"].append({
                "id": f"bank_secure_gateway_{index}",
                "source_kind": "catalog",
                "source_key": "next_gen_firewall",
                "placement": "cloud",
                "config": "core",
                "units": 2,
                "installed_round": 0,
            })
        else:
            result["initial"]["assets"].append({
                "id": f"bank_shared_network_{index}",
                "source_kind": "service",
                "source_key": "client_network",
                "placement": "cloud",
                "config": None,
                "units": 2,
                "installed_round": 0,
            })
    result["initial"]["connections"] = []
    result["initial"]["primary"] = {key: None for key in result["initial"]["primary"]}
    return result


def test_runtime_accepts_pack_authored_non_riverside_initial_estate():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "pack"
        shutil.copytree(PACK, target)
        runtime_path = target / "runtime.yaml"
        raw = yaml.safe_load(runtime_path.read_text())
        runtime_path.write_text(yaml.safe_dump(_runtime_with_authored_non_riverside_estate(raw), sort_keys=False))

        loaded = load_runtime_pack(target)

    assert len(loaded.runtime.initial.assets) == 10
    assert all(asset.id.startswith("bank_") for asset in loaded.runtime.initial.assets)
    assert loaded.runtime.initial.primary["order_fulfilment"] is None


def test_runtime_still_rejects_unknown_initial_source_reference():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "pack"
        shutil.copytree(PACK, target)
        runtime_path = target / "runtime.yaml"
        raw = yaml.safe_load(runtime_path.read_text())
        raw["initial"]["assets"][0]["source_key"] = "bank_unknown_system"
        runtime_path.write_text(yaml.safe_dump(raw, sort_keys=False))

        with pytest.raises(SimulationError) as exc:
            load_runtime_pack(target)

    assert exc.value.code == "invalid_reference"


def test_checkpoint_capability_references_bind_to_supplied_pack_vocabulary():
    base = {
        "strategy": "bank_focus", "strategy_declared_round": 0,
        "assets": {}, "connections": {}, "projects": {}, "hiring_orders": {}, "staff_hires": [],
        "support": {"tier": None, "covered_assets": []}, "rollouts": {}, "unit_resistance": {},
        "governance": {"banking_operations": {"owner": None, "sponsor": None}},
        "primary": {"banking_operations": None}, "policies": {}, "capital_balance": 0, "operating_reserve": 0,
        "cost_ledger": [], "technical_debt": [], "signal_ledger": [], "action_history": [],
        "available_funds_by_round": [], "event_history": [], "response_history": [], "tco_forecasts": [],
        "repair_assessment_history": [], "unpriced_signal_exposures": [],
    }

    state = CheckpointStateV1.model_validate(base, context={"capabilities": ("banking_operations",)})
    assert state.primary == {"banking_operations": None}
    with pytest.raises(ValueError):
        CheckpointStateV1.model_validate(base, context={"capabilities": ("customer_operations",)})

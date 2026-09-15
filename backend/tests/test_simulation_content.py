"""Focused P1 contract tests: strict DTOs, content binding and checkpoints."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil
import tempfile

import yaml

import pytest

from app.simulation import load_runtime_pack, normalize_patch
from app.simulation.types import (
    CheckpointStateV1, CommandV1, SheetPatchV1, SimulationError, UnitV1, ServiceRuntimeV1, CatalogRuntimeV1,
)


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


def test_strict_twelve_command_categories_and_no_coercion():
    command = CommandV1.model_validate({"key": "hire_it", "op": "hire", "option": "it_generalist"})
    assert command.op == "hire"
    with pytest.raises(ValueError):
        CommandV1.model_validate({"key": "hire_it", "op": "hire", "option": "it_generalist", "price": 1})
    with pytest.raises(ValueError):
        CommandV1.model_validate({"key": "hire_it", "op": "hire", "option": "it_generalist", "units": True})
    with pytest.raises(ValueError):
        CommandV1.model_validate({"key": "bad", "op": "request_capital", "amount": 1, "reason": ""})


def test_patch_categories_merge_and_empty_clear():
    old = (CommandV1(key="hire_it", op="hire", option="it_generalist"),)
    patch = SheetPatchV1(version=1, replace_categories={"training": []})
    assert [x.key for x in normalize_patch(old, patch)] == ["hire_it"]
    patch = SheetPatchV1(version=1, replace_categories={"staffing": []})
    assert normalize_patch(old, patch) == ()


def test_runtime_content_is_complete_and_semantically_bound():
    pack = load_runtime_pack(PACK)
    assert len(pack.runtime.catalog) == 14
    assert len(pack.runtime.services) == 11
    assert len(pack.runtime.response_disposition) == 13
    assert set(pack.runtime.initial.primary) == {
        "order_fulfilment", "store_operations", "financial_reporting",
        "customer_insight", "marketing_sales", "service", "firm_infrastructure",
    }
    assert len(pack.pack_digest) == 64
    original = pack.pack_digest
    pack.casepack.metadata.display_name = "changed only in detached copy"
    assert original == pack.pack_digest


def test_runtime_missing_file_refuses_initialization(tmp_path):
    with pytest.raises(SimulationError) as exc:
        load_runtime_pack(tmp_path)
    assert exc.value.code == "unsupported_operation"


def test_checkpoint_shape_rejects_unknown_fields_and_bad_join():
    base = {
        "strategy": "cost_leadership", "strategy_declared_round": 0,
        "assets": {}, "connections": {}, "projects": {}, "hiring_orders": {}, "staff_hires": [],
        "support": {"tier": None, "covered_assets": []}, "rollouts": {}, "unit_resistance": {},
        "governance": {}, "primary": {}, "policies": {}, "capital_balance": 0, "operating_reserve": 0,
        "cost_ledger": [], "technical_debt": [], "signal_ledger": [], "action_history": [],
        "available_funds_by_round": [], "event_history": [], "response_history": [], "tco_forecasts": [],
        "repair_assessment_history": [], "unpriced_signal_exposures": [],
    }
    assert isinstance(CheckpointStateV1.model_validate(base), CheckpointStateV1)
    unknown = deepcopy(base); unknown["surprise"] = 1
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(unknown)
    bad = deepcopy(base); bad["primary"] = {"order_fulfilment": "foreign_asset"}
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)
    bad = deepcopy(base); bad["staff_hires"] = [{"unknown": 1}]
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)
    bad = deepcopy(base); bad["cost_ledger"] = [{"arbitrary": "x"}]
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)
    bad = deepcopy(base); bad["strategy"] = ""
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)
    bad = deepcopy(base); bad["strategy_declared_round"] = -1
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)


def test_operation_specific_nullability_and_strict_runtime_numbers():
    for op, fields in [
        ("replace_application", {"asset": None, "placement": "cloud", "config": "core"}),
        ("replace_service", {"asset": None, "placement": "cloud", "units": 1}),
        ("train", {"asset": None, "option": "full"}),
        ("set_process", {"asset": None, "choice": "partial"}),
    ]:
        with pytest.raises(ValueError): CommandV1.model_validate({"key": "bad_null", "op": op, **fields})


def test_runtime_negative_cross_reference_and_registry_probes():
    def run_mutation(mutator):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pack"
            shutil.copytree(PACK, target)
            runtime_path = target / "runtime.yaml"
            raw = yaml.safe_load(runtime_path.read_text())
            mutator(raw)
            runtime_path.write_text(yaml.safe_dump(raw, sort_keys=False))
            with pytest.raises(SimulationError): load_runtime_pack(target)

    def missing_capacity(raw):
        raw["catalog"]["pos_system_2011"]["capacity_by_capability"].pop("store_operations")
        raw["provenance"].pop("/catalog/pos_system_2011/capacity_by_capability/store_operations")
        raw["units"].pop("/catalog/pos_system_2011/capacity_by_capability/store_operations")
    run_mutation(missing_capacity)
    run_mutation(lambda raw: raw["units"].update({"/does/not/exist": "fraction"}))
    run_mutation(lambda raw: raw.update({"generated_defaults": False}))


def test_runtime_strict_numbers_and_exact_tco_map():
    with pytest.raises(ValueError): UnitV1(label="unit", initial_resistance=True)
    with pytest.raises(ValueError): UnitV1(label="unit", initial_resistance="0.2")
    with pytest.raises(ValueError): ServiceRuntimeV1(
        serves=[], availability=True, service_life_rounds=1,
        capacity_by_capability={}, supply_by_placement={}, max_units=1,
    )
    # This StrictInt assertion is the planted guard for accidental removal of
    # StrictModel's strict configuration: bool would otherwise coerce to 1.
    with pytest.raises(ValueError): ServiceRuntimeV1(
        serves=[], availability=0.9, service_life_rounds=True,
        capacity_by_capability={}, supply_by_placement={}, max_units=1,
    )
    with pytest.raises(ValueError): ServiceRuntimeV1(
        serves=[], availability=float("nan"), service_life_rounds=1,
        capacity_by_capability={}, supply_by_placement={}, max_units=1,
    )

    def mutate_estimator(raw, change):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pack"
            shutil.copytree(PACK, target)
            data = yaml.safe_load((target / "runtime.yaml").read_text())
            change(data["accounting"]["tco_estimators"])
            (target / "runtime.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
            with pytest.raises(SimulationError): load_runtime_pack(target)
    mutate_estimator(None, lambda m: m.update({"unexpected": "one_round_opex"}))
    mutate_estimator(None, lambda m: m.pop("training"))
    mutate_estimator(None, lambda m: m.update({"training": "one_round_opex"}))


def test_strict_model_configuration_mutation_guard():
    """A plain numeric field catches removal of StrictModel strict=True."""
    with pytest.raises(ValueError):
        CatalogRuntimeV1(
            purchasable_placements=[], capacity_by_capability={"x": True},
            capacity_multiplier_by_config={}, opex_multiplier_by_config={},
        )


def test_checkpoint_nested_evidence_and_map_identity_are_strict():
    base = {
        "strategy": "cost_leadership", "strategy_declared_round": 0,
        "assets": {}, "connections": {}, "projects": {}, "hiring_orders": {}, "staff_hires": [],
        "support": {"tier": None, "covered_assets": []}, "rollouts": {}, "unit_resistance": {},
        "governance": {}, "primary": {}, "policies": {}, "capital_balance": 0, "operating_reserve": 0,
        "cost_ledger": [], "technical_debt": [], "signal_ledger": [], "action_history": [],
        "available_funds_by_round": [], "event_history": [], "response_history": [], "tco_forecasts": [],
        "repair_assessment_history": [], "unpriced_signal_exposures": [],
    }
    bad = deepcopy(base)
    bad["event_history"] = [{"round": 0, "fired": [{"arbitrary": 1}], "suppressed": [], "prevented": []}]
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)
    bad = deepcopy(base)
    bad["connections"] = {"wrong_key": {"id": "connection", "src": "a", "dst": "b", "kind": "network", "entity": None, "tier": None, "created_round": 0, "retired_round": None}}
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad)


def test_bound_pack_views_and_digest_are_immutable():
    pack = load_runtime_pack(PACK)
    digest = pack.pack_digest
    pack.runtime.catalog["forged"] = pack.runtime.catalog["pos_system_2011"]
    pack.casepack.catalog.append(pack.casepack.catalog[0])
    assert len(pack.runtime.catalog) == 14
    assert len(pack.casepack.catalog) == 14
    assert pack.pack_digest == digest
    with pytest.raises(Exception): pack.pack_digest = "a" * 64

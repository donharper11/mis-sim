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
    AssetV1, CheckpointStateV1, CommandV1, DebtV1, GovernanceStateV1, HiringOrderV1,
    OperatingForecastV1, PolicyStateV1, RepairWitnessV1, ResponseV1, RolloutV1, SheetPatchV1,
    SignalV1, SimulationError, SupportV1, TcoV1, UnpricedSignalExposureV1, UnitV1, ServiceRuntimeV1, CatalogRuntimeV1,
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
    bad_strategy = deepcopy(base)
    bad_strategy["strategy"] = "x" * 65
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad_strategy)


def test_checkpoint_nested_numbers_and_key_lengths_are_bounded():
    with pytest.raises(ValueError): RolloutV1(trained_count=0, adoption=float("nan"), process="partial", ever_trained=False, lifecycle="active")
    with pytest.raises(ValueError): RolloutV1(trained_count=0, adoption=-1.0, process="partial", ever_trained=False, lifecycle="active")
    signal = {
        "key": "signal", "episode_id": 0, "capability": "service", "metric": "metric", "metric_kind": "threshold",
        "value": float("nan"), "severity": "warning", "status": "open", "first_shown_round": 0,
        "cleared_round": None, "fire_round": None, "cleared_by": [], "was_actionable": False,
        "cheapest_fix_when_raised": None,
    }
    with pytest.raises(ValueError): SignalV1.model_validate(signal)
    with pytest.raises(ValueError): DebtV1(signal="signal", episode_id=0, capability="service", opened_round=0, amount=-1, settled_round=None)
    with pytest.raises(ValueError): ResponseV1(round=0, key="response", event="event", option="option", rationale_tag="tag", cost=-1, effect="none")
    with pytest.raises(ValueError): TcoV1(asset_id="asset", ordered_round=0, selected_categories=[], forecast=-1, forecast_horizon_round=0, estimates={})
    long_id = "a" * 65
    with pytest.raises(ValueError): AssetV1(id=long_id, source_kind="catalog", source_key="catalog", placement="on_prem", config="core", units=1, installed_round=0, retired_round=None)
    bad_map = {
        "strategy": "cost_leadership", "strategy_declared_round": 0, "assets": {long_id: {}}, "connections": {}, "projects": {}, "hiring_orders": {}, "staff_hires": [],
        "support": {"tier": None, "covered_assets": []}, "rollouts": {}, "unit_resistance": {}, "governance": {}, "primary": {}, "policies": {},
        "capital_balance": 0, "operating_reserve": 0, "cost_ledger": [], "technical_debt": [], "signal_ledger": [], "action_history": [],
        "available_funds_by_round": [], "event_history": [], "response_history": [], "tco_forecasts": [], "repair_assessment_history": [], "unpriced_signal_exposures": [],
    }
    with pytest.raises(ValueError): CheckpointStateV1.model_validate(bad_map)


def test_repair_and_checkpoint_machine_keys_are_strictly_bounded():
    with pytest.raises(ValueError): OperatingForecastV1(round=-1, opening=0, allowance=0, recurring=0, closing=0)
    witness = {
        "candidate_key": "a" * 64, "commands": [], "capital_cost": 0, "effective_round": 0,
        "affordable": True, "operating_forecast": [], "baseline_metric": float("nan"),
        "candidate_metric": 0.5, "emitted_action_ids": [], "credit_eligible": True,
        "assumptions": "empty_future_decisions",
    }
    with pytest.raises(ValueError): RepairWitnessV1.model_validate(witness)
    witness["baseline_metric"] = 0.5; witness["capital_cost"] = -1
    with pytest.raises(ValueError): RepairWitnessV1.model_validate(witness)
    witness["capital_cost"] = 0; witness["effective_round"] = -1
    with pytest.raises(ValueError): RepairWitnessV1.model_validate(witness)
    with pytest.raises(ValueError): GovernanceStateV1(owner="x" * 65, sponsor=None)
    with pytest.raises(ValueError): PolicyStateV1(selected="x" * 65, actively_decided=False)
    with pytest.raises(ValueError): SupportV1(tier="x" * 65, covered_assets=[])
    with pytest.raises(ValueError): SupportV1(tier=None, covered_assets=["x" * 65])
    with pytest.raises(ValueError): HiringOrderV1(id="order", option="x" * 65, ordered_round=0, remaining_lead=0, status="pending", arrival_round=None)
    with pytest.raises(ValueError): DebtV1(signal="x" * 65, episode_id=0, capability="capability", opened_round=0, amount=0, settled_round=None)
    with pytest.raises(ValueError): UnpricedSignalExposureV1(signal="signal", episode_id=0, capability="x" * 65, reason="unpriced")
def test_bound_pack_views_and_digest_are_immutable():
    pack = load_runtime_pack(PACK)
    digest = pack.pack_digest
    pack.runtime.catalog["forged"] = pack.runtime.catalog["pos_system_2011"]
    pack.casepack.catalog.append(pack.casepack.catalog[0])
    assert len(pack.runtime.catalog) == 14
    assert len(pack.casepack.catalog) == 14
    assert pack.pack_digest == digest
    with pytest.raises(Exception): pack.pack_digest = "a" * 64

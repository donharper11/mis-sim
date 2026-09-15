"""Direct P3 organisation reducer contract checks."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.engine.state import StaffPool
from app.simulation.content import load_runtime_pack
from app.simulation.estate import initialize_state, reduce_estate
from app.simulation.organisation import PROCESS_FIT, _round_valid, reduce_organisation
from app.simulation.types import CheckpointStateV1, CommandV1, SimulationError


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


def _pack():
    return load_runtime_pack(PACK)


def _org_estate(state, rollouts=None, *, arrived_ids=()):
    return SimpleNamespace(
        assets=state.assets, connections=state.connections,
        rollouts=rollouts if rollouts is not None else state.rollouts,
        primary=state.primary, hiring_orders=state.hiring_orders,
        staff_hires=state.staff_hires, arrived_ids=list(arrived_ids),
    )


def _apply_org(state, delta):
    payload = state.model_dump(mode="python")
    for key in ("rollouts", "unit_resistance", "governance", "primary", "policies", "support"):
        payload[key] = getattr(delta, key)
    payload["strategy"] = delta.strategy
    payload["strategy_declared_round"] = delta.strategy_declared_round
    return CheckpointStateV1.model_validate(payload)


def test_training_decay_coverage_process_and_noop_bounds():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    train = CommandV1(key="order_training", op="train", asset="initial_order_mgmt_v42", option="basic")
    delta = reduce_organisation(pack, state, state, [train], 1)
    assert delta.rollouts["initial_order_mgmt_v42"].trained_count == 84
    assert delta.charge_entries[0].capital_delta == -12000
    assert delta.effect_candidates[0].action_type == "add_training"
    round2 = _apply_org(state, delta)
    decayed = reduce_organisation(pack, round2, _org_estate(round2, delta.rollouts), [], 2)
    assert decayed.rollouts["initial_order_mgmt_v42"].trained_count == 75
    none = reduce_organisation(pack, state, state, [CommandV1(key="none", op="train", asset="initial_order_mgmt_v42", option="none")], 1)
    assert not none.charge_entries and not none.effect_candidates
    with pytest.raises(SimulationError):
        reduce_organisation(pack, state, state, [CommandV1(key="bad", op="train", asset="initial_compute_pool", option="full")], 1)


def test_process_prices_fit_and_repeated_state_are_deterministic():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    assert PROCESS_FIT == {"redesigned": 1.0, "partial": 0.5, "unchanged": 0.25}
    redesigned = reduce_organisation(pack, state, state, [CommandV1(key="redesign", op="set_process", asset="initial_pos_system_2011", choice="redesigned")], 1)
    assert redesigned.rollouts["initial_pos_system_2011"].process == "redesigned"
    assert redesigned.charge_entries[0].capital_delta == -12000
    repeated = reduce_organisation(pack, _apply_org(state, redesigned), _org_estate(_apply_org(state, redesigned), redesigned.rollouts), [CommandV1(key="repeat", op="set_process", asset="initial_pos_system_2011", choice="redesigned")], 2)
    assert not repeated.charge_entries and not repeated.effect_candidates


def test_service_arrival_has_no_end_user_shock_and_communication_is_scoped():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    service = CommandV1(key="pool", op="buy_service", service="compute_pool", placement="cloud", units=1)
    estate = reduce_estate(pack, state, [service], 1)
    delta = reduce_organisation(pack, state, estate, [CommandV1(key="comm", op="communicate", org_unit="warehouse", option="change_champions")], 1)
    assert delta.unit_resistance["warehouse"] < state.unit_resistance["warehouse"]
    assert delta.unit_resistance["it"] == pytest.approx(state.unit_resistance["it"] * 0.9)
    assert "warehouse" in delta.communication and "it" not in delta.communication


def test_staff_support_governance_primary_and_strategy_change():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    hire = reduce_organisation(pack, state, state, [CommandV1(key="hire", op="hire", option="it_generalist")], 1)
    assert hire.staff.capacity == 2.0 and hire.staff.load == 3.7
    support = reduce_organisation(pack, state, state, [CommandV1(key="support", op="set_support", tier="basic", covered_assets=["initial_pos_system_2011"])], 1)
    assert support.support.tier == "basic" and support.staff.capacity > 2.0
    assigned = reduce_organisation(pack, state, state, [
        CommandV1(key="assign", op="assign", capability="store_operations", owner="operations", sponsor="senior_management"),
        CommandV1(key="primary", op="set_primary", capability="store_operations", asset="initial_pos_system_2011"),
        CommandV1(key="strategy", op="declare_strategy", strategy="focus_strategy"),
    ], 1)
    assert assigned.governance["store_operations"].owner == "operations"
    assert assigned.governance["store_operations"].sponsor == "senior_management"
    assert assigned.primary["store_operations"] == "initial_pos_system_2011"
    assert assigned.strategy == "focus_strategy" and assigned.charge_entries[-1].capital_delta == -80000
    with pytest.raises(SimulationError):
        reduce_organisation(pack, state, state, [CommandV1(key="bad", op="assign", capability="store_operations", owner="vendor", sponsor=None)], 1)


def test_policy_activity_and_preference_views_are_authored_and_bounded():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    command = CommandV1(key="audit", op="set_policy", policy="access_logging", selected="full_audit_trail")
    selected = reduce_organisation(pack, state, state, [command], 1)
    assert selected.policies["access_logging"].selected == "full_audit_trail"
    assert selected.policies["access_logging"].actively_decided is True
    assert selected.charge_entries[0].capital_delta == -30000
    assert len(selected.stakeholder_alignments) == 10
    assert sum(len(item.views) for item in pack.runtime.preferences.rules) == 33
    held = reduce_organisation(pack, _apply_org(state, selected), _org_estate(_apply_org(state, selected), selected.rollouts), [], 2)
    assert held.policies["access_logging"].selected == "full_audit_trail"
    assert held.policies["access_logging"].actively_decided is False
    with pytest.raises(SimulationError):
        reduce_organisation(pack, state, state, [CommandV1(key="bad", op="set_policy", policy="access_logging", selected="unknown")], 1)


def test_strict_round_and_mutation_boundary():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    for bad_round in (True, 1.0, 0):
        with pytest.raises(SimulationError): _round_valid(pack.casepack, bad_round)
        with pytest.raises(SimulationError): reduce_organisation(pack, state, state, [], bad_round)

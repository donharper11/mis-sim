"""P2 estate, resource and physical projection contract tests."""

from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path

import pytest

from app.engine.state import StaffPool
from app.simulation.content import load_runtime_pack
from app.simulation.estate import initialize_state, reduce_estate
from app.simulation.projection import project_team_state
from app.simulation.resources import _round6, resource_projection
from app.simulation.types import CheckpointStateV1, CommandV1, SimulationError


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


def _pack():
    return load_runtime_pack(PACK)


def _apply(state, delta):
    payload = state.model_dump(mode="python")
    for key in ("assets", "connections", "projects", "hiring_orders", "staff_hires", "rollouts", "primary"):
        payload[key] = getattr(delta, key)
    return CheckpointStateV1.model_validate(payload)


def test_initial_estate_is_authored_once_and_has_no_seed_history():
    pack = _pack()
    state = initialize_state(pack, "cost_leadership")
    assert len(state.assets) == 10
    assert len(state.connections) == 11
    assert len(state.projects) == 10
    assert set(state.rollouts) == {key for key, asset in state.assets.items() if asset.source_kind == "catalog"}
    assert not state.hiring_orders and not state.staff_hires
    assert not state.signal_ledger and not state.action_history and not state.cost_ledger
    assert all(value is None for value in state.primary.values() if value not in {"initial_order_mgmt_v42", "initial_pos_system_2011", "initial_accounting_package"})
    with pytest.raises(SimulationError): initialize_state(pack, "unknown_strategy")


def test_lead_time_arrival_and_cancellation_are_terminal_and_sunk():
    pack = _pack(); prior = initialize_state(pack, "cost_leadership")
    buy = CommandV1(key="warehouse", op="buy_application", catalog="centraline_im7", placement="saas", config="core", primary_for=None, tco_categories=[])
    pending = reduce_estate(pack, prior, [buy], 1)
    assert pending.arrived_ids == [] and pending.projects["r1_warehouse"].status == "pending"
    assert "r1_warehouse" not in pending.hiring_orders
    arrived = reduce_estate(pack, _apply(prior, pending), [], 2)
    assert "r1_warehouse" in arrived.arrived_ids
    assert _apply(_apply(prior, pending), arrived).assets["r1_warehouse"].installed_round == 2
    cancelled = reduce_estate(pack, _apply(prior, pending), [CommandV1(key="cancel", op="cancel_order", order="r1_warehouse")], 2)
    assert cancelled.projects["r1_warehouse"].status == "cancelled"
    assert cancelled.projects["r1_warehouse"].paid_capex == 0


def test_connections_require_live_joined_endpoints_and_exact_integration_shape():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    with pytest.raises(SimulationError):
        reduce_estate(pack, state, [CommandV1(key="bad", op="connect", src="missing", dst="initial_order_mgmt_v42", kind="network", entity=None, tier=None)], 1)
    with pytest.raises(SimulationError):
        reduce_estate(pack, state, [CommandV1(key="bad", op="connect", src="initial_pos_system_2011", dst="initial_order_mgmt_v42", kind="integration", entity=None, tier="basic")], 1)
    with pytest.raises(SimulationError):
        reduce_estate(pack, state, [CommandV1(key="bad", op="connect", src="initial_pos_system_2011", dst="initial_order_mgmt_v42", kind="integration", entity="product", tier="basic")], 1)


def test_resource_projection_rounds_and_zero_supply_are_finite():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    view = resource_projection(pack, state.assets, state.connections, state.policies, 1)
    assert view.total_opex == 16200
    assert round(view.total_load, 6) == 3.7
    for row in view.by_placement.values():
        assert 0 <= row["factor"] <= 1
        assert all(math.isfinite(value) and value >= 0 for value in row.values())
    assert view.by_asset["initial_pos_system_2011"]["capacity_by_capability"]["store_operations"] == 6000.0
    no_pools = {key: value for key, value in state.assets.items() if value.source_key not in {"compute_pool", "storage_pool"}}
    zero_supply = resource_projection(pack, no_pools, state.connections, state.policies, 1)
    assert zero_supply.by_placement["on_prem"]["factor"] == 0.0
    assert all(math.isfinite(value) for row in zero_supply.by_placement.values() for value in row.values())


def test_physical_projection_preserves_one_node_identity_and_entity_access():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    view = resource_projection(pack, state.assets, state.connections, state.policies, 1)
    projected = project_team_state(pack, state, 1, view, StaffPool(1.0, 0.0))
    assert len(projected.nodes) == 10 and len({node.key for node in projected.nodes}) == 10
    assert len(projected.edges) == 11
    assert {grant.entity for grant in projected.entity_access} == {"product", "order"}
    assert all(grant.source != grant.receiver for grant in projected.entity_access)


def test_resource_strictness_mutation_guard():
    """No NaN/Inf or negative resource factor may cross the P2 boundary."""
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    view = resource_projection(pack, state.assets, state.connections, state.policies, 1)
    assert all(math.isfinite(row["factor"]) and 0 <= row["factor"] <= 1 for row in view.by_placement.values())
    with pytest.raises(SimulationError): _round6(float("nan"))
    with pytest.raises(SimulationError): _round6(-1.0)


def test_pending_cancel_never_materializes_or_projects():
    pack = _pack(); prior = initialize_state(pack, "cost_leadership")
    buy = CommandV1(key="warehouse", op="buy_application", catalog="centraline_im7", placement="saas", config="core", primary_for=None, tco_categories=[])
    pending = reduce_estate(pack, prior, [buy], 1)
    pending_state = _apply(prior, pending)
    assert "r1_warehouse" not in {node.key for node in project_team_state(pack, pending_state, 1, resource_projection(pack, pending_state.assets, pending_state.connections, pending_state.policies, 1), StaffPool(1.0, 0.0)).nodes}
    cancelled = reduce_estate(pack, pending_state, [CommandV1(key="cancel", op="cancel_order", order="r1_warehouse")], 2)
    assert "r1_warehouse" not in cancelled.assets
    assert "r1_warehouse" not in resource_projection(pack, cancelled.assets, cancelled.connections, prior.policies, 2).by_asset


def test_replacement_noop_preserves_rollout_and_blocks_retirement_until_cancelled():
    pack = _pack(); prior = initialize_state(pack, "cost_leadership")
    noop = CommandV1(key="same", op="replace_application", asset="initial_pos_system_2011", placement="on_prem", config="core")
    no_change = reduce_estate(pack, prior, [noop], 1)
    assert not no_change.charge_entries and "r1_same" not in no_change.projects
    replace = CommandV1(key="upgrade", op="replace_application", asset="initial_pos_system_2011", placement="cloud", config="core")
    pending = reduce_estate(pack, prior, [replace], 1)
    pending_state = _apply(prior, pending)
    with pytest.raises(SimulationError):
        reduce_estate(pack, pending_state, [CommandV1(key="retire", op="retire_asset", asset="initial_pos_system_2011")], 1)
    arrived = reduce_estate(pack, pending_state, [], 2)
    assert arrived.rollouts["initial_pos_system_2011"] == prior.rollouts["initial_pos_system_2011"]


def test_policy_load_and_retirement_take_effect_at_their_round():
    pack = _pack(); prior = initialize_state(pack, "cost_leadership")
    policies = dict(prior.policies); policies["access_logging"] = policies["access_logging"].model_copy(update={"selected": "full_audit_trail"})
    view = resource_projection(pack, prior.assets, prior.connections, policies, 1)
    assert view.policy_load == 0.08 and round(view.total_load, 6) == 3.78
    retired = reduce_estate(pack, prior, [CommandV1(key="retire", op="retire_asset", asset="initial_pos_system_2011")], 2)
    before = resource_projection(pack, retired.assets, retired.connections, prior.policies, 1)
    after = resource_projection(pack, retired.assets, retired.connections, prior.policies, 2)
    assert "initial_pos_system_2011" in before.by_asset and "initial_pos_system_2011" not in after.by_asset
    assert before.integration_load >= after.integration_load


def test_projection_round_identity_and_acquisition_validation_are_closed():
    pack = _pack(); state = initialize_state(pack, "cost_leadership")
    view = resource_projection(pack, state.assets, state.connections, state.policies, 1)
    for bad_round in (True, 1.0):
        with pytest.raises(SimulationError): project_team_state(pack, state, bad_round, view, StaffPool(1.0, 0.0))
    projected = project_team_state(pack, state, 1, view, StaffPool(1.0, 0.0))
    assert {grant.connection for grant in projected.entity_access} <= set(state.connections)
    with pytest.raises(SimulationError):
        reduce_estate(pack, state, [CommandV1(key="bad", op="buy_application", catalog="missing", placement="saas", config="core", primary_for=None, tco_categories=[])], 1)
    with pytest.raises(SimulationError):
        reduce_estate(pack, state, [CommandV1(key="too_many", op="buy_service", service="compute_pool", placement="cloud", units=9)], 1)

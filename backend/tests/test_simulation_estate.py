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

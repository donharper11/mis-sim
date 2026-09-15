"""Pure P2 estate initialization and lifecycle reducer."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.casepack.models import Casepack
from app.engine.state import ArchEdge, ArchNode, EntityAccess, TeamState
from .types import (
    AssetV1, CheckpointStateV1, CommandV1, ConnectionV1, CostEntryV1,
    EffectCandidateV1, EstateDeltaV1, GovernanceStateV1, HiringOrderV1,
    ProjectV1, RolloutV1, RuntimePackV1, SimulationError, StaffHireV1,
)


def _parts(pack: RuntimePackV1) -> tuple[Casepack, Any]:
    return pack.casepack, pack.runtime


def _money(value: float | int) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _source_maps(casepack: Casepack) -> tuple[dict[str, Any], dict[str, Any]]:
    return ({x.key: x for x in casepack.catalog}, {x.key: x for x in casepack.platform.services})


def _initial_project(asset: AssetV1) -> ProjectV1:
    return ProjectV1(
        id=asset.id, asset_id=asset.id, source_kind=asset.source_kind,
        source_key=asset.source_key, placement=asset.placement, config=asset.config,
        units=asset.units, ordered_round=0, paid_capex=0, remaining_lead=0,
        status="arrived", replacement_target=None, tco_categories=[],
    )


def initialize_state(pack: RuntimePackV1, strategy_key: str) -> CheckpointStateV1:
    """Create exactly one authored Riverside initial estate, with no R3 seed state."""
    casepack, runtime = _parts(pack)
    if strategy_key not in {x.key for x in casepack.strategies}:
        raise SimulationError("invalid_reference", "strategy", {"strategy": strategy_key})
    assets = {x.id: AssetV1.model_validate({**x.model_dump(), "retired_round": None}) for x in runtime.initial.assets}
    connections = {
        x.id: ConnectionV1(**x.model_dump(), created_round=0, retired_round=None)
        for x in runtime.initial.connections
    }
    projects = {key: _initial_project(asset) for key, asset in assets.items()}
    catalogs, _services = _source_maps(casepack)
    rollouts: dict[str, RolloutV1] = {}
    for asset in assets.values():
        if asset.source_kind != "catalog":
            continue
        source = catalogs[asset.source_key]
        trained = int(runtime.initial.training_fraction * source.people_affected.count)
        rollouts[asset.id] = RolloutV1(
            trained_count=trained, adoption=runtime.initial.adoption,
            process="partial" if source.process_option is not None else "unchanged",
            ever_trained=trained > 0, lifecycle="active",
        )
    policies = {
        policy.key: {"selected": policy.default, "actively_decided": False}
        for policy in casepack.policies
    }
    governance = {key: GovernanceStateV1(owner=value.owner, sponsor=value.sponsor) for key, value in runtime.initial.governance.items()}
    return CheckpointStateV1(
        strategy=strategy_key, strategy_declared_round=0,
        assets=assets, connections=connections, projects=projects, hiring_orders={},
        staff_hires=[], support={"tier": None, "covered_assets": []}, rollouts=rollouts,
        unit_resistance={unit: runtime.people.units[unit].initial_resistance for unit in runtime.people.units},
        governance=governance, primary=dict(runtime.initial.primary), policies=policies,
        capital_balance=runtime.accounting.opening_capital,
        operating_reserve=runtime.accounting.opening_operating,
        cost_ledger=[], technical_debt=[], signal_ledger=[], action_history=[],
        available_funds_by_round=[], event_history=[], response_history=[], tco_forecasts=[],
        repair_assessment_history=[], unpriced_signal_exposures=[],
    )


def _price(casepack: Casepack, source_key: str, placement: str, config: str | None, units: int) -> tuple[int, int]:
    catalogs, services = _source_maps(casepack)
    source = catalogs.get(source_key) or services.get(source_key)
    if source is None:
        raise SimulationError("invalid_reference", "source", {"source": source_key})
    modes = source.deployment_modes if source_key in catalogs else source.placement_options
    mode = next((value for key, value in modes.items() if key.value == placement), None)
    if mode is None:
        raise SimulationError("invalid_reference", "placement", {"source": source_key, "placement": placement})
    if source_key in catalogs:
        if config is None or config not in source.config_tiers:
            raise SimulationError("invalid_reference", "config", {"source": source_key, "config": config})
        multiplier = source.config_tiers[config].capex_multiplier
    else:
        if config is not None:
            raise SimulationError("invalid_input", "config", {"source": source_key})
        multiplier = 1.0
    return _money(mode.capex * multiplier * units), mode.lead_time_rounds


def _asset_source(pack: RuntimePackV1, asset: AssetV1) -> Any:
    catalogs, services = _source_maps(pack.casepack)
    source = catalogs.get(asset.source_key) or services.get(asset.source_key)
    if asset.source_kind == "service" and source is not None:
        # Platform service economics/roles come from the casepack; runtime
        # carries the capability projection used by estate effects.
        return (source, pack.runtime.services[asset.source_key])
    return source


def _serves(pack: RuntimePackV1, source_key: str, source: Any) -> list[str]:
    return list(source.serves) if hasattr(source, "serves") else list(pack.runtime.services[source_key].serves)


def _copy_state(prior: CheckpointStateV1) -> dict[str, Any]:
    return deepcopy(prior.model_dump(mode="python"))


def _find_project(state: dict[str, Any], order_id: str) -> tuple[str, dict[str, Any]]:
    project = state["projects"].get(order_id)
    if project is None:
        raise SimulationError("invalid_reference", "order", {"order": order_id})
    return order_id, project


def _remove_unmaterialized_asset(state: dict[str, Any], project: dict[str, Any]) -> None:
    """Cancellation/abandonment is sunk, but a pending new asset never existed."""
    if project.get("replacement_target") is None:
        asset_id = project["asset_id"]
        state["assets"].pop(asset_id, None)
        state["rollouts"].pop(asset_id, None)
        for capability, selected in state["primary"].items():
            if selected == asset_id:
                state["primary"][capability] = None


def reduce_estate(pack: RuntimePackV1, prior: CheckpointStateV1, commands: tuple[CommandV1, ...] | list[CommandV1], round: int) -> EstateDeltaV1:
    """Apply only estate commands; organisation, accounting and persistence remain separate packets."""
    casepack, runtime = _parts(pack)
    if not isinstance(round, int) or isinstance(round, bool) or round < 1 or round > casepack.metadata.rounds:
        raise SimulationError("round_state", "round")
    state = _copy_state(prior)
    commands = tuple(commands)
    arrived: list[str] = []
    retired: list[str] = []
    expired: list[str] = []
    charges: list[CostEntryV1] = []
    effects: list[EffectCandidateV1] = []
    by_key = {command.key: command for command in commands}

    # Resolve lifecycle controls before due arrivals.  A paused order is frozen;
    # a pending order advances exactly once per round.
    lifecycle = {c.order: c for c in commands if c.op == "project"}
    for order, command in lifecycle.items():
        _key, project = _find_project(state, order)
        if project["status"] in {"cancelled", "abandoned", "arrived"} and command.choice == "continue":
            raise SimulationError("invalid_input", f"project/{order}")
        if command.choice == "pause":
            if project["status"] != "pending" or project["remaining_lead"] <= 0:
                raise SimulationError("invalid_input", f"project/{order}")
            project["status"] = "paused"
        elif command.choice == "continue" and project["status"] == "paused":
            project["status"] = "pending"
        elif command.choice == "kill":
            if project["status"] not in {"pending", "paused"}:
                raise SimulationError("invalid_input", f"project/{order}")
            project["status"] = "abandoned"; expired.append(project["asset_id"])
            _remove_unmaterialized_asset(state, project)
    for order, command in ((c.order, c) for c in commands if c.op == "cancel_order"):
        _key, project = _find_project(state, order)
        order_row = state["hiring_orders"].get(order)
        if project["status"] not in {"pending", "paused"}:
            raise SimulationError("invalid_input", f"order/{order}")
        project["status"] = "cancelled"
        if order_row is not None: order_row["status"] = "cancelled"
        _remove_unmaterialized_asset(state, project)
    for project_id, project in list(state["projects"].items()):
        if project["status"] == "paused" and round >= casepack.metadata.rounds - project["remaining_lead"] + 1 and project_id not in lifecycle:
            project["status"] = "abandoned"; expired.append(project["asset_id"])
            _remove_unmaterialized_asset(state, project)
        if project["status"] != "pending": continue
        # An order created in this round is not advanced until the next round.
        if project["ordered_round"] >= round: continue
        if project_id in lifecycle and lifecycle[project_id].choice == "continue":
            pass
        if project["remaining_lead"] > 0:
            project["remaining_lead"] -= 1
        if project["remaining_lead"] == 0:
            project["status"] = "arrived"; arrived.append(project["asset_id"])
            asset_id = project["asset_id"]
            if asset_id in state["assets"]:
                state["assets"][asset_id].update(placement=project["placement"], config=project["config"], units=project["units"], installed_round=round, retired_round=None)
            else:
                state["assets"][asset_id] = {
                    "id": asset_id, "source_kind": project["source_kind"], "source_key": project["source_key"],
                    "placement": project["placement"], "config": project["config"], "units": project["units"], "installed_round": round, "retired_round": None,
                }
            source = _asset_source(pack, AssetV1.model_validate(state["assets"][asset_id]))
            source_model = source[0] if isinstance(source, tuple) else source
            source_key = state["assets"][asset_id]["source_key"]
            if project["source_kind"] == "catalog":
                # A replacement keeps the physical asset's rollout continuity.  New
                # acquisitions begin at zero and are trained by the later organisation
                # packet.
                if project["replacement_target"] is None:
                    state["rollouts"][asset_id] = {"trained_count": 0, "adoption": 0.0, "process": "unchanged", "ever_trained": False, "lifecycle": "active"}
                effects.append(EffectCandidateV1(effect_kind="replacement" if project["replacement_target"] else "arrival", source_round=project["ordered_round"], source_command=project_id.split("_", 1)[-1], effect_round=round, asset_id=asset_id, target_key=asset_id, capabilities=_serves(pack, source_key, source_model), cost=project["paid_capex"], action_type="scale_node" if project["replacement_target"] else "add_node"))

    # New acquisitions and replacements are committed after lifecycle resolution.
    for command in commands:
        if command.op not in {"buy_application", "buy_service", "replace_application", "replace_service"}: continue
        if command.op.startswith("replace"):
            target = state["assets"].get(command.asset)
            if target is None or target.get("retired_round") is not None: raise SimulationError("invalid_reference", "asset", {"asset": command.asset})
            if any(project.get("replacement_target") == target["id"] and project.get("status") in {"pending", "paused"} for project in state["projects"].values()):
                raise SimulationError("conflicting_commands", "replacement", {"asset": target["id"]})
            source_key = target["source_key"]; source_kind = target["source_kind"]; asset_id = target["id"]; replacement_target = asset_id
            placement = command.placement; config = command.config if source_kind == "catalog" else None; units = command.units or target["units"]
            if placement == target["placement"] and config == target.get("config") and units == target["units"]:
                continue
        elif command.op == "buy_application":
            source_key = command.catalog; source_kind = "catalog"; asset_id = f"r{round}_{command.key}"; replacement_target = None; placement = command.placement; config = command.config; units = 1
        else:
            source_key = command.service; source_kind = "service"; asset_id = f"r{round}_{command.key}"; replacement_target = None; placement = command.placement; config = None; units = command.units
        catalogs, services = _source_maps(casepack)
        source = catalogs.get(source_key) if source_kind == "catalog" else services.get(source_key)
        if source is None:
            raise SimulationError("invalid_reference", "source", {"source": source_key})
        if source_kind == "catalog":
            if placement not in {key.value for key in source.deployment_modes}:
                raise SimulationError("invalid_reference", "placement", {"source": source_key, "placement": placement})
            if config not in source.config_tiers:
                raise SimulationError("invalid_reference", "config", {"source": source_key, "config": config})
        else:
            if placement not in {key.value for key in source.placement_options}:
                raise SimulationError("invalid_reference", "placement", {"source": source_key, "placement": placement})
            max_units = runtime.services[source_key].max_units
            if units > max_units:
                raise SimulationError("invalid_input", "units", {"source": source_key, "max_units": max_units})
        if source_kind == "catalog" and source_key in {a["source_key"] for a in state["assets"].values() if a.get("retired_round") is None and a["id"] != replacement_target}:
            raise SimulationError("conflicting_commands", "source", {"source": source_key})
        price, lead = _price(casepack, source_key, placement, config, units)
        if round + lead > casepack.metadata.rounds: raise SimulationError("arrival_after_game_end", "order", {"order": command.key})
        if command.op == "buy_application" and command.primary_for is not None and lead != 0:
            raise SimulationError("arrival_after_game_end", "primary_for", {"asset": asset_id})
        if command.op == "buy_application" and command.primary_for is not None and command.primary_for not in {x.key for x in casepack.capabilities}:
            raise SimulationError("invalid_reference", "primary_for", {"capability": command.primary_for})
        project_id = f"r{round}_{command.key}"
        if project_id in state["projects"]: raise SimulationError("conflicting_commands", "order", {"order": project_id})
        project = {"id": project_id, "asset_id": asset_id, "source_kind": source_kind, "source_key": source_key, "placement": placement, "config": config, "units": units, "ordered_round": round, "paid_capex": price, "remaining_lead": lead, "status": "arrived" if lead == 0 else "pending", "replacement_target": replacement_target, "tco_categories": command.tco_categories or []}
        state["projects"][project_id] = project
        if asset_id not in state["assets"]:
            state["assets"][asset_id] = {"id": asset_id, "source_kind": source_kind, "source_key": source_key, "placement": placement, "config": config, "units": units, "installed_round": round + lead, "retired_round": None}
        charges.append(CostEntryV1(round=round, kind="acquisition", source=command.key, asset=asset_id, capital_delta=-price, operating_delta=0, category="replacement" if replacement_target else "capacity"))
        if lead == 0:
            # Materialize through the same path as due orders on this round.
            state["projects"][project_id]["remaining_lead"] = 0
            if asset_id in state["assets"]: state["assets"][asset_id].update(placement=placement, config=config, units=units, installed_round=round, retired_round=None)
            else: state["assets"][asset_id] = {"id": asset_id, "source_kind": source_kind, "source_key": source_key, "placement": placement, "config": config, "units": units, "installed_round": round, "retired_round": None}
            if source_kind == "catalog": state["rollouts"][asset_id] = {"trained_count": 0, "adoption": 0.0, "process": "unchanged", "ever_trained": False, "lifecycle": "active"}
            if command.op == "buy_application" and command.primary_for is not None: state["primary"][command.primary_for] = asset_id
            arrived.append(asset_id)
    for command in commands:
        if command.op == "retire_asset":
            asset = state["assets"].get(command.asset)
            if asset is None or asset.get("retired_round") is not None: raise SimulationError("invalid_reference", "asset", {"asset": command.asset})
            if asset.get("installed_round", 0) > round:
                raise SimulationError("invalid_input", "asset", {"reason": "pending asset"})
            if any(project.get("replacement_target") == command.asset and project.get("status") in {"pending", "paused"} for project in state["projects"].values()):
                raise SimulationError("conflicting_commands", "replacement", {"asset": command.asset})
            asset["retired_round"] = round; retired.append(command.asset)
            for connection in state["connections"].values():
                if connection["src"] in {command.asset} or connection["dst"] == command.asset: connection["retired_round"] = round
            for capability, selected in state["primary"].items():
                if selected == command.asset: state["primary"][capability] = None
            if command.asset in state["rollouts"]: state["rollouts"][command.asset]["lifecycle"] = "retired"
    # Connections are live physical edges; disconnect removes the edge from the projection.
    for command in commands:
        if command.op == "disconnect":
            if command.connection not in state["connections"]: raise SimulationError("invalid_reference", "connection", {"connection": command.connection})
            del state["connections"][command.connection]
        elif command.op == "connect":
            src = state["assets"].get(command.src); dst = state["assets"].get(command.dst)
            if src is None or dst is None or src.get("retired_round") is not None or dst.get("retired_round") is not None or command.src == command.dst: raise SimulationError("invalid_reference", "connection")
            if command.kind in {"network", "failover"} and (command.entity is not None or command.tier is not None): raise SimulationError("invalid_input", "connection")
            if command.kind == "integration" and (command.entity is None or command.tier is None): raise SimulationError("invalid_input", "connection")
            edge_key = f"r{round}_{command.key}"
            shape = (min(command.src, command.dst), max(command.src, command.dst), command.kind, command.entity)
            if any((min(e["src"], e["dst"]), max(e["src"], e["dst"]), e["kind"], e["entity"]) == shape for e in state["connections"].values()): raise SimulationError("conflicting_commands", "connection")
            if command.kind == "failover":
                sources, _ = _source_maps(casepack)
                if not any("failover" in (_source_maps(casepack)[0].get(a["source_key"], _source_maps(casepack)[1].get(a["source_key"])).roles_filled) for a in (src, dst)): raise SimulationError("invalid_reference", "connection")
            if command.kind == "integration":
                catalogs, services = _source_maps(casepack); source = catalogs.get(src["source_key"]) or services.get(src["source_key"]); receiver = catalogs.get(dst["source_key"])
                if receiver is None or not any(x.entity == command.entity for x in source.owns_entities) or not any(x.entity == command.entity and (x.from_capability is None or x.from_capability in source.serves) for x in receiver.must_be_fed_by): raise SimulationError("invalid_reference", "connection")
            state["connections"][edge_key] = {"id": edge_key, "src": command.src, "dst": command.dst, "kind": command.kind, "entity": command.entity, "tier": command.tier, "created_round": round, "retired_round": None}
            if command.kind == "integration":
                target_source = catalogs.get(dst["source_key"]) or services.get(dst["source_key"])
                effects.append(EffectCandidateV1(effect_kind="integration", source_round=round, source_command=command.key, effect_round=round, asset_id=command.dst, target_key=edge_key, capabilities=_serves(pack, dst["source_key"], target_source), cost=0, action_type="add_service_tier"))
    return EstateDeltaV1(
        assets=state["assets"], connections=state["connections"], projects=state["projects"],
        hiring_orders=state["hiring_orders"], staff_hires=state["staff_hires"],
        rollouts=state["rollouts"], primary=state["primary"], charge_entries=charges,
        arrived_ids=sorted(set(arrived)), retired_ids=sorted(set(retired)), expired_ids=sorted(set(expired)),
        effect_candidates=effects,
    )

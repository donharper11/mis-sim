"""Pure P3 organisation reducer.

The reducer owns the human and governance consequences of an estate transition.  It
does not persist state or settle money; the returned typed delta is consumed by the
later transition/accounting packet.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any

from app.casepack.models import Casepack
from .resources import resource_projection
from .types import (
    AssetV1, CheckpointStateV1, CommandV1, CostEntryV1, EffectCandidateV1,
    GovernanceStateV1, HiringOrderV1, OrgDeltaV1, PolicyStateV1, RolloutV1, RuntimePackV1,
    SimulationError, StaffPoolV1, StaffHireV1, StakeholderDecisionAlignmentV1,
    SupportV1,
)


PROCESS_FIT = {"redesigned": 1.0, "partial": 0.5, "unchanged": 0.25}
PLACEMENTS = {"on_prem", "cloud", "saas"}


def _parts(pack: RuntimePackV1) -> tuple[Casepack, Any]:
    return pack.casepack, pack.runtime


def _money(value: float | int) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _r6(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SimulationError("invalid_output", field)
    return round(float(value), 6)


def _round_clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return _r6(min(high, max(low, value)), "organisation.value")


def _round_up_count(population: int, coverage: float) -> int:
    return min(population, int(Decimal(str(population * coverage)).to_integral_value(rounding="ROUND_CEILING")))


def _dump(value: Any) -> dict[str, Any]:
    return value.model_dump(mode="python") if hasattr(value, "model_dump") else deepcopy(value)


def _round_valid(casepack: Casepack, round: int) -> None:
    if not isinstance(round, int) or isinstance(round, bool) or round < 1 or round > casepack.metadata.rounds:
        raise SimulationError("round_state", "round")


def _active(asset: dict[str, Any], round: int) -> bool:
    retired = asset.get("retired_round")
    return asset.get("installed_round", 0) <= round and (retired is None or retired > round)


def _catalogs(casepack: Casepack) -> dict[str, Any]:
    return {item.key: item for item in casepack.catalog}


def _services(casepack: Casepack) -> dict[str, Any]:
    return {item.key: item for item in casepack.platform.services}


def _asset_source(casepack: Casepack, asset: dict[str, Any]) -> Any:
    source = (_catalogs(casepack) if asset["source_kind"] == "catalog" else _services(casepack)).get(asset["source_key"])
    if source is None:
        raise SimulationError("invalid_reference", "asset.source_key", {"asset": asset["id"]})
    return source


def _cost(round: int, kind: str, source: str, amount: int = 0, *, asset: str | None = None,
          capability: str | None = None, category: str | None = None,
          operating_amount: int = 0) -> CostEntryV1:
    return CostEntryV1(
        round=round, kind=kind, source=source, asset=asset, capability=capability,
        category=category, capital_delta=-int(amount), operating_delta=-int(operating_amount),
    )


def _wage(round: int, order_id: str, amount: int) -> CostEntryV1:
    return CostEntryV1(round=round, kind="wages", source=order_id, category="wages",
                       capital_delta=0, operating_delta=-int(amount))


def _effect(kind: str, command: CommandV1, round: int, asset_id: str | None,
            target_key: str | None, capabilities: list[str], cost: int, action_type: str) -> EffectCandidateV1:
    return EffectCandidateV1(
        effect_kind=kind, source_round=round, source_command=command.key,
        effect_round=round, asset_id=asset_id, target_key=target_key,
        capabilities=sorted(set(capabilities)), cost=cost, action_type=action_type,
    )


def _staffing_factor(capacity: float, load: float) -> float:
    if load <= 0:
        return 1.0
    return _round_clamp(capacity / load)


def _stakeholder_maps(casepack: Casepack) -> dict[str, Any]:
    return {item.key: item for item in casepack.stakeholders}


def _active_catalog_rows(casepack: Casepack, assets: dict[str, dict[str, Any]], round: int):
    catalogs = _catalogs(casepack)
    for asset in assets.values():
        if asset["source_kind"] == "catalog" and _active(asset, round):
            source = catalogs.get(asset["source_key"])
            if source is None:
                raise SimulationError("invalid_reference", "asset.source_key", {"asset": asset["id"]})
            yield asset, source


def _preference_alignments(
    pack: RuntimePackV1,
    assets: dict[str, dict[str, Any]],
    rollouts: dict[str, dict[str, Any]],
    unit_resistance: dict[str, float],
    communication: dict[str, str],
    support: SupportV1,
    staff: StaffPoolV1,
    connections: dict[str, Any],
    round: int,
) -> list[StakeholderDecisionAlignmentV1]:
    casepack, _runtime = _parts(pack)
    catalogs = _catalogs(casepack)
    services = _services(casepack)
    active_catalog = list(_active_catalog_rows(casepack, assets, round))
    active_services = [a for a in assets.values() if a["source_kind"] == "service" and _active(a, round)]

    def relevant(rows, cares):
        return [(asset, source) for asset, source in rows if set(source.serves).intersection(cares)]

    def actual(metric: str, cares: set[str], ideal: Any) -> Any:
        rows = relevant(active_catalog, cares)
        if metric == "training_coverage":
            values = [rollouts[a["id"]]["trained_count"] / source.people_affected.count for a, source in rows if a["id"] in rollouts]
            return sum(values) / len(values) if values else 0.0
        if metric == "asset_reliability":
            values = [source.availability for _asset, source in rows]
            return sum(values) / len(values) if values else 0.0
        if metric == "process_fit":
            values = [PROCESS_FIT[rollouts[a["id"]]["process"]] for a, _source in rows if a["id"] in rollouts]
            return sum(values) / len(values) if values else 0.0
        if metric == "cost_posture":
            values = []
            for asset, source in rows:
                modes = list(source.deployment_modes.values())
                selected = next((mode.capex for key, mode in source.deployment_modes.items() if key.value == asset["placement"]), 0)
                maximum = max((mode.capex for mode in modes), default=0)
                values.append(selected / maximum if maximum else 0.0)
            return sum(values) / len(values) if values else 0.0
        if metric == "staff_load_ratio":
            return min(1.0, staff.load / max(staff.capacity, 0.001))
        if metric == "communication":
            units = {source.people_affected.org_unit for _asset, source in rows}
            reductions = []
            for unit in units:
                option = communication.get(unit, "none")
                reductions.append(_runtime.people.communication_options[option].resistance_reduction if option != "none" else 0.0)
            return min(1.0, (sum(reductions) / len(reductions)) / 0.10) if reductions else 0.0
        if metric == "platform_placement":
            return [asset["placement"] for asset in active_services]
        if metric == "support_tier":
            return support.tier
        if metric == "integration_tier":
            return [(_dump(edge).get("tier")) for edge in connections.values() if _dump(edge).get("kind") == "integration" and (_dump(edge).get("retired_round") is None or _dump(edge).get("retired_round") > round)]
        raise SimulationError("invalid_input", "preference.metric", {"metric": metric})

    results: list[StakeholderDecisionAlignmentV1] = []
    for rule in pack.runtime.preferences.rules:
        cares = set(rule.cares_about)
        scores: list[tuple[float, float]] = []
        for view in rule.views:
            value = actual(view.metric, cares, view.ideal)
            if isinstance(view.ideal, str):
                values = value if isinstance(value, list) else [value]
                score = sum(item == view.ideal for item in values) / len(values) if values else (1.0 if value == view.ideal else 0.0)
            else:
                numeric = float(value) if not isinstance(value, list) and value is not None else 0.0
                score = _round_clamp(1.0 - abs(numeric - float(view.ideal)))
            scores.append((score, float(view.weight)))
        weight = sum(weight for _score, weight in scores)
        alignment = sum(score * weight for score, weight in scores) / weight if weight else 1.0
        results.append(StakeholderDecisionAlignmentV1(stakeholder=rule.stakeholder, value=_round_clamp(alignment), cares_about=list(rule.cares_about)))
    return results


def reduce_organisation(
    pack: RuntimePackV1,
    prior: CheckpointStateV1,
    estate: Any,
    commands: tuple[CommandV1, ...] | list[CommandV1],
    round: int,
) -> OrgDeltaV1:
    """Apply training, process, staffing, governance, policy and preference choices."""
    casepack, runtime = _parts(pack)
    _round_valid(casepack, round)
    commands = tuple(commands)
    state = deepcopy(prior.model_dump(mode="python"))
    estate_data = {key: deepcopy(getattr(estate, key)) for key in ("assets", "connections", "rollouts", "primary", "hiring_orders", "staff_hires", "arrived_ids") if hasattr(estate, key)}
    assets = {key: _dump(value) for key, value in estate_data.get("assets", state["assets"]).items()}
    connections = {key: _dump(value) for key, value in estate_data.get("connections", state["connections"]).items()}
    rollouts = {key: _dump(value) for key, value in estate_data.get("rollouts", state["rollouts"]).items()}
    primary = deepcopy(estate_data.get("primary", state["primary"]))
    active_arrivals = set(estate_data.get("arrived_ids", []))
    governance = {key: _dump(value) for key, value in state["governance"].items()}
    policies = {key: _dump(value) for key, value in state["policies"].items()}
    support = _dump(state["support"])
    unit_resistance = deepcopy(state["unit_resistance"])
    communication: dict[str, str] = {}
    charge_entries: list[CostEntryV1] = []
    effects: list[EffectCandidateV1] = []

    catalogs = _catalogs(casepack)
    services = _services(casepack)
    capabilities = {cap.key for cap in casepack.capabilities}
    stakeholders = _stakeholder_maps(casepack)
    units = set(runtime.people.units)

    # Existing rollouts decay before any positive training selection.  Pending and
    # service assets have no rollout and therefore cannot receive a prepaid effect.
    for asset_id, rollout in list(rollouts.items()):
        asset = assets.get(asset_id)
        source = catalogs.get(asset.get("source_key")) if asset else None
        if asset is None or source is None or not _active(asset, round):
            continue
        if asset_id not in active_arrivals:
            rollout["trained_count"] = int(math.floor(rollout["trained_count"] * runtime.people.training_retention))
        rollout["ever_trained"] = bool(rollout["ever_trained"] or rollout["trained_count"] > 0)

    # Apply incoming hiring orders independently of estate lifecycle orders.
    hiring_orders = {key: _dump(value) for key, value in estate_data.get("hiring_orders", state["hiring_orders"]).items()}
    staff_hires = [_dump(value) for value in estate_data.get("staff_hires", state["staff_hires"])]
    for order in hiring_orders.values():
        if order["status"] == "pending" and order["ordered_round"] < round:
            order["remaining_lead"] = max(0, order["remaining_lead"] - 1)
            if order["remaining_lead"] == 0:
                order["status"] = "arrived"; order["arrival_round"] = round
                staff_hires.append({"order_id": order["id"], "option": order["option"], "arrival_round": round})
    for command in commands:
        if command.op != "cancel_order" or command.order not in hiring_orders:
            continue
        order = hiring_orders[command.order]
        if order["status"] != "pending":
            raise SimulationError("invalid_input", "order", {"order": command.order})
        order["status"] = "cancelled"

    for command in commands:
        if command.op != "hire":
            continue
        option = runtime.people.hiring_options.get(command.option)
        if option is None:
            raise SimulationError("invalid_reference", "option", {"option": command.option})
        order_id = f"r{round}_{command.key}"
        if order_id in hiring_orders:
            raise SimulationError("conflicting_commands", "order", {"order": order_id})
        if round + option.lead_time_rounds > casepack.metadata.rounds:
            raise SimulationError("arrival_after_game_end", "order", {"order": order_id})
        if option.lead_time_rounds == 0:
            hiring_orders[order_id] = {"id": order_id, "option": command.option, "ordered_round": round, "remaining_lead": 0, "status": "arrived", "arrival_round": round}
            staff_hires.append({"order_id": order_id, "option": command.option, "arrival_round": round})
        else:
            hiring_orders[order_id] = {"id": order_id, "option": command.option, "ordered_round": round, "remaining_lead": option.lead_time_rounds, "status": "pending", "arrival_round": round + option.lead_time_rounds}

    # Each arrived hire creates a real recurring operating liability.  P4 can
    # reconcile the entry by its stable order identity and round.
    for hire in staff_hires:
        if hire["arrival_round"] <= round:
            option = runtime.people.hiring_options.get(hire["option"])
            if option is None:
                raise SimulationError("invalid_reference", "option", {"option": hire["option"]})
            charge_entries.append(_wage(round, hire["order_id"], option.wage_per_round))

    # Support is held until explicitly changed.  Coverage survives only while its
    # assets remain live; an empty scope receives no capacity credit.
    support_commands = [command for command in commands if command.op == "set_support"]
    if len(support_commands) > 1:
        raise SimulationError("conflicting_commands", "support")
    if support_commands:
        command = support_commands[0]
        tier = command.tier
        if tier is not None and tier not in {item.key for item in casepack.platform.support_tiers}:
            raise SimulationError("invalid_reference", "tier", {"tier": tier})
        covered = list(command.covered_assets or [])
        if len(covered) != len(set(covered)):
            raise SimulationError("conflicting_commands", "covered_assets")
        if tier is None and covered:
            raise SimulationError("invalid_input", "covered_assets")
        for asset_id in covered:
            if asset_id not in assets or not _active(assets[asset_id], round):
                raise SimulationError("invalid_reference", "covered_assets", {"asset": asset_id})
        support = {"tier": tier, "covered_assets": sorted(covered)}
        if tier is not None:
            tier_row = next(item for item in casepack.platform.support_tiers if item.key == tier)
            charge_entries.append(_cost(round, "support", command.key, category="support", operating_amount=tier_row.cost))
            support_caps: list[str] = []
            for asset_id in covered:
                support_caps.extend(_asset_source(casepack, assets[asset_id]).serves)
            effects.append(_effect("support", command, round, None, tier, support_caps, tier_row.cost, "add_service_tier"))
    else:
        support["covered_assets"] = [asset_id for asset_id in support.get("covered_assets", []) if asset_id in assets and _active(assets[asset_id], round)]

    # Strategy, governance and primary selections are applied before resistance and adoption.
    strategy = state["strategy"]
    strategy_round = state["strategy_declared_round"]
    strategy_commands = [command for command in commands if command.op == "declare_strategy"]
    if len(strategy_commands) > 1:
        raise SimulationError("conflicting_commands", "strategy")
    strategy_changed = False
    if strategy_commands:
        selected = strategy_commands[0].strategy
        if selected not in {item.key for item in casepack.strategies}:
            raise SimulationError("invalid_reference", "strategy", {"strategy": selected})
        strategy_changed = selected != strategy
        if strategy_changed:
            strategy = selected; strategy_round = round
            selected_strategy = next(item for item in casepack.strategies if item.key == selected)
            charge_entries.append(_cost(round, "strategy", strategy_commands[0].key, selected_strategy.reopen_cost, category="strategy"))

    seen_assignments: set[str] = set()
    for command in commands:
        if command.op != "assign":
            continue
        if command.capability not in capabilities:
            raise SimulationError("invalid_reference", "capability", {"capability": command.capability})
        if command.capability in seen_assignments:
            raise SimulationError("conflicting_commands", "assign", {"capability": command.capability})
        seen_assignments.add(command.capability)
        owner = stakeholders.get(command.owner) if command.owner is not None else None
        sponsor = stakeholders.get(command.sponsor) if command.sponsor is not None else None
        if owner is not None and owner.stakeholder_type != "internal":
            raise SimulationError("invalid_reference", "owner", {"owner": command.owner})
        if command.owner is not None and owner is None:
            raise SimulationError("invalid_reference", "owner", {"owner": command.owner})
        if sponsor is not None and (sponsor.stakeholder_type != "internal" or sponsor.archetype not in {"c_suite", "finance"}):
            raise SimulationError("invalid_reference", "sponsor", {"sponsor": command.sponsor})
        if command.sponsor is not None and sponsor is None:
            raise SimulationError("invalid_reference", "sponsor", {"sponsor": command.sponsor})
        governance[command.capability] = {"owner": command.owner, "sponsor": command.sponsor}

    primary_commands = [command for command in commands if command.op == "set_primary"]
    if len({command.capability for command in primary_commands}) != len(primary_commands):
        raise SimulationError("conflicting_commands", "primary")
    for command in primary_commands:
        if command.capability not in capabilities:
            raise SimulationError("invalid_reference", "capability", {"capability": command.capability})
        if command.asset is None:
            primary[command.capability] = None
            continue
        asset = assets.get(command.asset)
        if asset is None or not _active(asset, round) or asset["source_kind"] != "catalog":
            raise SimulationError("invalid_reference", "asset", {"asset": command.asset})
        source = catalogs[asset["source_key"]]
        if command.capability not in source.serves:
            raise SimulationError("invalid_reference", "primary", {"capability": command.capability, "asset": command.asset})
        if command.asset in {selected for cap, selected in primary.items() if cap != command.capability and selected is not None}:
            raise SimulationError("conflicting_commands", "primary", {"asset": command.asset})
        primary[command.capability] = command.asset

    # Policy selections persist, but activity is exactly the presence of this round's
    # set_policy command.  The resource projection consumes the selected ordinal.
    for key, value in policies.items():
        value["actively_decided"] = False
    policy_commands = [command for command in commands if command.op == "set_policy"]
    seen_policies: set[str] = set()
    for command in policy_commands:
        if command.policy in seen_policies:
            raise SimulationError("conflicting_commands", "policy", {"policy": command.policy})
        seen_policies.add(command.policy)
        policy = next((item for item in casepack.policies if item.key == command.policy), None)
        if policy is None or command.selected not in policy.options:
            raise SimulationError("invalid_reference", "policy", {"policy": command.policy, "selected": command.selected})
        old = policies.get(command.policy, {"selected": policy.default, "actively_decided": False})["selected"]
        policies[command.policy] = {"selected": command.selected, "actively_decided": True}
        if command.selected != old:
            charge_entries.append(_cost(round, "policy", command.key, policy.cost, category="policy"))
            effects.append(_effect("policy", command, round, None, command.policy, sorted(capabilities), policy.cost, "add_policy"))

    # Training and process choices read the post-estate live catalog only.
    targeted_training: set[str] = set(); targeted_process: set[str] = set()
    for command in commands:
        if command.op not in {"train", "set_process"}:
            continue
        asset = assets.get(command.asset)
        if asset is None or not _active(asset, round) or asset["source_kind"] != "catalog" or command.asset not in rollouts:
            raise SimulationError("invalid_reference", "asset", {"asset": command.asset})
        source = catalogs.get(asset["source_key"])
        if source is None:
            raise SimulationError("invalid_reference", "asset.source_key")
        rollout = rollouts[command.asset]
        if command.op == "train":
            if command.asset in targeted_training:
                raise SimulationError("conflicting_commands", "training", {"asset": command.asset})
            targeted_training.add(command.asset)
            option = source.training_options.get(command.option)
            if option is None:
                raise SimulationError("invalid_reference", "option", {"option": command.option})
            target = _round_up_count(source.people_affected.count, option.coverage)
            if option.coverage <= 0 or command.option == "none":
                continue
            if option.cost > 0:
                charge_entries.append(_cost(round, "training", command.key, option.cost, asset=command.asset, capability=source.serves[0] if source.serves else None, category="training"))
            if target > rollout["trained_count"]:
                rollout["trained_count"] = target
                rollout["ever_trained"] = True
                effects.append(_effect("training", command, round, command.asset, command.asset, list(source.serves), option.cost, "add_training"))
        else:
            if command.asset in targeted_process:
                raise SimulationError("conflicting_commands", "process", {"asset": command.asset})
            targeted_process.add(command.asset)
            choice = command.choice
            if choice == rollout["process"]:
                continue
            if source.process_option is None and choice != "unchanged":
                raise SimulationError("invalid_reference", "process", {"asset": command.asset})
            if choice == "partial":
                price = _money(source.process_option.cost * runtime.accounting.process_partial_fraction)
            elif choice == "redesigned":
                price = source.process_option.cost if source.process_option else 0
            else:
                price = 0
            improves = PROCESS_FIT[choice] > PROCESS_FIT[rollout["process"]]
            rollout["process"] = choice
            if price:
                charge_entries.append(_cost(round, "process", command.key, price, asset=command.asset, capability=source.serves[0] if source.serves else None, category="process_redesign"))
            if improves:
                effects.append(_effect("process", command, round, command.asset, command.asset, list(source.serves), price, "redesign_process"))

    # Communication changes only the named unit for this round.
    for command in commands:
        if command.op != "communicate":
            continue
        if command.org_unit not in units:
            raise SimulationError("invalid_reference", "org_unit", {"org_unit": command.org_unit})
        if command.org_unit in communication:
            raise SimulationError("conflicting_commands", "communication", {"org_unit": command.org_unit})
        if command.option != "none" and command.option not in runtime.people.communication_options:
            raise SimulationError("invalid_reference", "option", {"option": command.option})
        communication[command.org_unit] = command.option
        if command.option != "none":
            option = runtime.people.communication_options[command.option]
            charge_entries.append(_cost(round, "communication", command.key, option.cost, category="communication"))

    # Staffing uses the same resource projection as P2 after policy selection and
    # support modifies capacity only; it never changes physical resource draw.
    policies_models = policies
    resources = resource_projection(pack, assets, connections, policies_models, round)
    tier_by_key = {item.key: item for item in casepack.platform.support_tiers}
    support_credit = 0.0
    if support.get("tier") is not None:
        tier = tier_by_key[support["tier"]]
        covered_load = sum(resources.by_asset.get(asset_id, {}).get("staff_load", 0.0) for asset_id in support.get("covered_assets", []))
        support_credit = min(tier.fte_equivalent, covered_load)
    arrived_fte = sum(runtime.people.hiring_options[hire["option"]].fte for hire in staff_hires if hire["arrival_round"] <= round)
    capacity = casepack.platform.starting_staff_fte + arrived_fte + support_credit
    load = resources.total_load
    staff = StaffPoolV1(capacity=_r6(capacity, "staff.capacity"), load=_r6(load, "staff.load"), available=_r6(capacity - load, "staff.available"))
    staffing = _staffing_factor(staff.capacity, staff.load)

    # Resistance receives only catalog arrival shocks.  Service arrivals do not
    # invent end-user change, and communication only affects its named unit.
    arrival_counts = {unit: 0 for unit in units}
    for asset_id in active_arrivals:
        asset = assets.get(asset_id)
        source = catalogs.get(asset.get("source_key")) if asset else None
        if source is not None and _active(asset, round):
            arrival_counts[source.people_affected.org_unit] += 1
    for unit in units:
        previous = state["unit_resistance"].get(unit, runtime.people.units[unit].initial_resistance)
        option = communication.get(unit, "none")
        reduction = runtime.people.communication_options[option].resistance_reduction if option != "none" else 0.0
        shock = runtime.people.arrival_shock * arrival_counts[unit] / max(staffing, runtime.people.staff_floor)
        strategy_shock = runtime.people.strategy_shock if strategy_changed else 0.0
        unit_resistance[unit] = _round_clamp(previous * runtime.people.resistance_retention + shock + strategy_shock - reduction, 0.0, runtime.people.resistance_ceiling)

    # Adoption is derived from real rollout state, never accepted from a command.
    for asset_id, rollout in rollouts.items():
        asset = assets.get(asset_id); source = catalogs.get(asset.get("source_key")) if asset else None
        if source is None or not _active(asset, round):
            continue
        primary_cap = next((cap for cap, selected in primary.items() if selected == asset_id), None)
        sponsor = primary_cap is not None and governance.get(primary_cap, {}).get("sponsor") is not None
        target = (rollout["trained_count"] / source.people_affected.count) * PROCESS_FIT[rollout["process"]] * (runtime.people.sponsor_present if sponsor else runtime.people.sponsor_absent) * staffing * (1.0 - unit_resistance[source.people_affected.org_unit])
        rollout["adoption"] = _round_clamp(rollout["adoption"] + runtime.people.adoption_adjustment * (target - rollout["adoption"]))

    # Convert all six policy/default states and the ten authored non-policy rules to
    # detached strict DTOs.  Absence is inactive; explicit retention is active.
    alignment = _preference_alignments(pack, assets, rollouts, unit_resistance, communication, SupportV1.model_validate(support), staff, connections, round)
    return OrgDeltaV1(
        rollouts={key: RolloutV1.model_validate(value) for key, value in sorted(rollouts.items())},
        unit_resistance={key: _r6(value, f"unit_resistance.{key}") for key, value in sorted(unit_resistance.items())},
        governance={key: GovernanceStateV1.model_validate(value) for key, value in sorted(governance.items())},
        primary={key: primary.get(key) for key in sorted(primary)},
        policies={key: PolicyStateV1.model_validate(value) for key, value in sorted(policies.items())},
        support=SupportV1.model_validate(support), strategy=strategy,
        hiring_orders={key: HiringOrderV1.model_validate(value) for key, value in sorted(hiring_orders.items())},
        staff_hires=[StaffHireV1.model_validate(value) for value in sorted(staff_hires, key=lambda item: (item["arrival_round"], item["order_id"]))],
        strategy_declared_round=strategy_round, staff=staff,
        communication=dict(sorted(communication.items())),
        charge_entries=sorted(charge_entries, key=lambda item: (item.round, item.kind, item.source)),
        stakeholder_alignments=alignment,
        effect_candidates=sorted(effects, key=lambda item: (item.effect_round, item.source_round, item.source_command, item.effect_kind, item.target_key or "")),
    )

"""P2 projection into the existing pure engine TeamState."""

from __future__ import annotations

from typing import Any, Iterable

from app.casepack.models import Casepack
from app.engine.state import (
    ActionRecord, ArchEdge, ArchNode, DataFreshnessState, DecisionState, DeploymentState, EntityAccess,
    FinancialModelState,
    GovernanceState, OrgUnitState, PolicyDecisionState, SignalState, StaffPool, TeamState,
)
from .types import CheckpointStateV1, ResourceViewV1, RuntimePackV1, SimulationError


def _decision_records(
    pack: RuntimePackV1,
    state: CheckpointStateV1,
    round: int,
    actions: Iterable[Any],
) -> tuple[DecisionState, ...]:
    """Project modern round spend into the pure engine's decision vocabulary.

    The runtime checkpoint is the source of truth for money and action history, while
    ``DecisionState`` is the scorer's deliberately smaller input.  Modern commands do
    not carry legacy sheet-only R/G/T fields, so the adapter resolves those from the
    authored catalog item (services are operational ``run`` spend).  Only the current
    round is projected, matching the legacy snapshot contract.
    """
    catalogs = {item.key: item for item in pack.casepack.catalog}
    services = {item.key: item for item in pack.casepack.platform.services}
    assets = state.assets
    category_by_action = {
        "add_node": "application", "scale_node": "application",
        "move_to_cloud": "platform_service", "upgrade_component": "platform_service",
        "add_training": "training", "redesign_process": "process_redesign",
        "add_service_tier": "integration", "retire_component": "lifecycle",
    }

    def source_for(target: str | None) -> Any | None:
        if target in catalogs:
            return catalogs[target]
        if target in services:
            return services[target]
        for asset in assets.values():
            if asset.id == target:
                return catalogs.get(asset.source_key) or services.get(asset.source_key)
        return None

    def rgt_for(target: str | None) -> str:
        source = source_for(target)
        tag = getattr(source, "rgt_tag", None)
        return str(getattr(tag, "value", tag or "run"))

    rows: list[DecisionState] = []
    seen: set[tuple[str, str | None]] = set()
    for envelope in actions:
        record = envelope.record
        # Policy effects are firm-wide choices, not capability portfolio spend. Their
        # alignment is scored by the policy factors and must not be duplicated once
        # per served capability.
        if record.cost <= 0 or record.capability is None or record.action_type == "add_policy":
            continue
        seen.add((envelope.source_command, record.capability))
        rows.append(DecisionState(
            key=f"{envelope.source_command}_{record.capability}_{record.action_type}",
            category=category_by_action.get(record.action_type, record.action_type),
            capability=record.capability,
            capex=int(record.cost),
            rgt_tag=rgt_for(record.target_key),
            is_maintenance=False,
        ))

    for charge in state.cost_ledger:
        if charge.round != round:
            continue
        if charge.category == "maintenance" and charge.operating_delta < 0:
            rows.append(DecisionState(
                key=f"maintenance_{charge.source}", category="maintenance", capability=None,
                capex=-int(charge.operating_delta), rgt_tag="run", is_maintenance=True,
            ))
            continue
        if charge.capital_delta >= 0:
            continue
        capex = -int(charge.capital_delta)
        if capex <= 0 or (charge.source, charge.capability) in seen:
            continue
        rows.append(DecisionState(
            key=f"charge_{charge.source}_{charge.category or charge.kind}",
            category=charge.category or charge.kind,
            capability=charge.capability,
            capex=capex,
            rgt_tag=rgt_for(charge.asset),
            is_maintenance=False,
        ))
    return tuple(rows)


def project_team_state(
    pack: RuntimePackV1,
    state: CheckpointStateV1,
    round: int,
    resources: ResourceViewV1,
    staff: StaffPool,
    stakeholder_alignments: Iterable[Any] = (),
    decisions: Iterable[Any] = (),
    actions: Iterable[Any] = (),
    funds: Iterable[int] = (),
    debt_ratios: dict[str, float] | None = None,
    signals: Iterable[SignalState] = (),
    entity_access: Iterable[EntityAccess] = (),
    repair_assessments: Iterable[Any] = (),
    data_freshness: DataFreshnessState | None = None,
    financial_model: FinancialModelState | None = None,
) -> TeamState:
    """Build a detached scorer snapshot from the authoritative checkpoint."""
    casepack = pack.casepack
    if not isinstance(round, int) or isinstance(round, bool) or round < 1 or round > casepack.metadata.rounds:
        raise SimulationError("round_state", "round")
    catalogs = {x.key: x for x in casepack.catalog}; services = {x.key: x for x in casepack.platform.services}
    nodes: list[ArchNode] = []; deployments: list[DeploymentState] = []
    for key, asset in state.assets.items():
        if (asset.retired_round is not None and asset.retired_round <= round) or asset.installed_round > round:
            continue
        source = catalogs.get(asset.source_key) or services.get(asset.source_key)
        if source is None: raise SimulationError("invalid_reference", f"assets/{key}")
        runtime_row = resources.by_asset.get(key, {})
        capacities = runtime_row.get("capacity_by_capability")
        nodes.append(ArchNode(key=key, roles_filled=tuple(source.roles_filled), availability=(source.availability if asset.source_kind == "catalog" else pack.runtime.services[source.key].availability), installed_round=asset.installed_round, service_life_rounds=source.service_life_rounds if asset.source_kind == "catalog" else pack.runtime.services[source.key].service_life_rounds, serves=tuple(source.serves if asset.source_kind == "catalog" else pack.runtime.services[source.key].serves), owns_entities=tuple((item.entity, item.level_of_detail) for item in source.owns_entities), placement=asset.placement, capacity_by_capability=capacities, base_rto_hours=getattr(source, "base_rto_hours", None)))
        if asset.source_kind == "catalog":
            rollout = state.rollouts.get(key)
            people = source.people_affected
            if rollout is not None: deployments.append(DeploymentState(key=key, catalog_key=asset.source_key, org_unit=people.org_unit, people_affected=people.count, trained_count=rollout.trained_count, process=rollout.process, adoption=rollout.adoption, ever_trained=rollout.ever_trained, serves=tuple(source.serves), is_primary_for=next((cap for cap, selected in state.primary.items() if selected == key), None), initiated=True, abandoned=rollout.lifecycle == "abandoned"))
    edges = tuple(ArchEdge(src=edge.src, dst=edge.dst, kind=edge.kind) for edge in state.connections.values() if edge.retired_round is None or edge.retired_round > round)
    org_units = tuple(OrgUnitState(key=key, resistance=value) for key, value in sorted(state.unit_resistance.items()))
    governance = tuple(GovernanceState(capability=key, owner_assigned=value.owner is not None, sponsor_assigned=value.sponsor is not None) for key, value in sorted(state.governance.items()))
    policies = tuple(PolicyDecisionState(policy=key, selected=value.selected, actively_decided=value.actively_decided) for key, value in sorted(state.policies.items()))
    action_records = tuple(ActionRecord(action_type=x.record.action_type, locked_round=x.record.locked_round, capability=x.record.capability, target_key=x.record.target_key, cost=x.record.cost) for x in actions)
    decision_records = tuple(decisions) or _decision_records(pack, state, round, actions)
    grants = tuple(entity_access) if entity_access else _entity_access(casepack, nodes, edges, state.connections, {key: asset.source_key for key, asset in state.assets.items()})
    return TeamState(round=round, declared_strategy=state.strategy, nodes=tuple(nodes), edges=edges, deployments=tuple(deployments), org_units=org_units, governance=governance, staff=staff, signals=tuple(signals), decisions=decision_records, stakeholder_alignments=tuple(stakeholder_alignments), policy_decisions=policies, action_history=action_records, available_funds_by_round=tuple(funds), debt_ratio_by_capability=debt_ratios, entity_access=grants, repair_assessments=tuple(repair_assessments) if repair_assessments else None, data_freshness=data_freshness, financial_model=financial_model)


def _entity_access(
    casepack: Casepack,
    nodes: list[ArchNode],
    edges: tuple[ArchEdge, ...],
    connections: dict[str, Any] | None = None,
    asset_sources: dict[str, str] | None = None,
) -> tuple[EntityAccess, ...]:
    by_key = {node.key: node for node in nodes}; grants: set[EntityAccess] = set()
    catalog = {x.key: x for x in casepack.catalog}; services = {x.key: x for x in casepack.platform.services}
    asset_sources = asset_sources or {}
    for edge in edges:
        if edge.kind != "integration": continue
        source_node, receiver_node = by_key.get(edge.src), by_key.get(edge.dst)
        if source_node is None or receiver_node is None: continue
        source_entities = dict(source_node.owns_entities)
        for receiver_cap in receiver_node.serves:
            receiver_source = catalog.get(asset_sources.get(receiver_node.key, receiver_node.key.split("initial_", 1)[-1]))
            if receiver_source is None: continue
            for dependency in receiver_source.must_be_fed_by:
                if dependency.entity not in source_entities: continue
                if dependency.from_capability is not None and dependency.from_capability not in source_node.serves: continue
                connection_id = next(
                    (key for key, value in (connections or {}).items()
                     if (value.src if hasattr(value, "src") else value.get("src")) == edge.src
                     and (value.dst if hasattr(value, "dst") else value.get("dst")) == edge.dst
                     and (value.kind if hasattr(value, "kind") else value.get("kind")) == edge.kind),
                    f"{edge.src}_{edge.dst}",
                )
                grants.add(EntityAccess(connection=connection_id, source=edge.src, receiver=edge.dst, capability=receiver_cap, entity=dependency.entity))
    return tuple(sorted(grants, key=lambda x: (x.connection, x.source, x.receiver, x.capability, x.entity)))

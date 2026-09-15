"""Pure P4 transition preparation, quotation and resolution."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable

from app.engine import events as event_engine
from app.engine import ledger as ledger_engine
from app.engine.score import score_team
from app.engine.state import StaffPool, StakeholderDecisionAlignment
from app.round.runner import rolled_scorecard

from .accounting import entry, forecast_operating, grant_and_allowance, recurring_entries, totals, money
from .estate import reduce_estate
from .organisation import reduce_organisation
from .projection import project_team_state
from .types import (
    ActionEnvelopeV1, ActionRecordV1, CheckpointStateV1, CommandV1, CostEntryV1,
    DebtV1, EventEvidenceV1, EventHistoryV1, PreviewV1, ResponseV1, RuntimePackV1,
    SignalV1, SimulationError, TcoV1, TransitionV1, WarningV1, PreventionEvidenceV1, SignalEpisodeV1,
)


def _dump(value: Any) -> Any:
    return value.model_dump(mode="python") if hasattr(value, "model_dump") else deepcopy(value)


def _canonical(value: Any) -> bytes:
    def plain(x: Any) -> Any:
        if hasattr(x, "model_dump"):
            return plain(x.model_dump(mode="json", exclude_none=False))
        if isinstance(x, dict):
            return {str(k): plain(v) for k, v in x.items()}
        if isinstance(x, (tuple, list)):
            return [plain(v) for v in x]
        return x
    return json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _valid_round(pack: RuntimePackV1, round: int) -> None:
    if type(round) is not int or round < 1 or round > pack.casepack.metadata.rounds:
        raise SimulationError("round_state", "round")


def _commands(commands: Iterable[CommandV1]) -> tuple[CommandV1, ...]:
    out = tuple(commands)
    if any(not isinstance(c, CommandV1) for c in out):
        raise SimulationError("invalid_input", "commands")
    keys = [c.key for c in out]
    if len(keys) != len(set(keys)):
        raise SimulationError("command_key_collision", "commands")
    return out


def _state_merge(prior: CheckpointStateV1, estate: Any, org: Any, charges: list[CostEntryV1]) -> CheckpointStateV1:
    data = prior.model_dump(mode="python")
    for name in ("assets", "connections", "projects", "hiring_orders", "staff_hires", "rollouts", "primary"):
        if hasattr(estate, name): data[name] = _dump(getattr(estate, name))
    for name in ("rollouts", "unit_resistance", "governance", "primary", "policies", "support", "hiring_orders", "staff_hires", "strategy", "strategy_declared_round"):
        if hasattr(org, name): data[name] = _dump(getattr(org, name))
    data["cost_ledger"] = list(data["cost_ledger"]) + [_dump(x) for x in charges]
    return CheckpointStateV1.model_validate(data)


def _action_id(source_round: int, source_command: str, effect_round: int, action_type: str, capability: str | None, target_key: str | None) -> str:
    return hashlib.sha256(_canonical([source_round, source_command, effect_round, action_type, capability, target_key])).hexdigest()


def _actions(pack: RuntimePackV1, prior: CheckpointStateV1, estate: Any, org: Any, commands: tuple[CommandV1, ...], round: int) -> list[ActionEnvelopeV1]:
    assets = {k: _dump(v) for k, v in estate.assets.items()}
    effects = list(getattr(estate, "effect_candidates", ())) + list(getattr(org, "effect_candidates", ()))
    prior_assets = prior.assets
    for asset_id in getattr(estate, "retired_ids", ()):
        old = prior_assets.get(asset_id)
        if old is not None and old.source_kind == "catalog":
            effects.append({"effect_kind": "retirement", "source_round": round, "source_command": f"retire_{asset_id}", "effect_round": round, "asset_id": asset_id, "target_key": old.source_key, "capabilities": list(next((x.serves for x in pack.casepack.catalog if x.key == old.source_key), ())), "cost": 0, "action_type": "retire_component"})
    out: list[ActionEnvelopeV1] = []
    for effect in effects:
        row = _dump(effect)
        if not row.get("capabilities"):
            continue
        asset_id = row.get("asset_id")
        target = row.get("target_key")
        if asset_id in assets and assets[asset_id].get("source_kind") == "catalog":
            target = assets[asset_id].get("source_key")
        for capability in sorted(set(row["capabilities"])):
            action_type = row["action_type"]
            action_id = _action_id(int(row["source_round"]), str(row["source_command"]), int(row["effect_round"]), action_type, capability, target)
            out.append(ActionEnvelopeV1(
                id=action_id, source_round=int(row["source_round"]), source_command=str(row["source_command"]),
                effect_round=int(row["effect_round"]), record=ActionRecordV1(
                    action_type=action_type, locked_round=int(row["source_round"]), capability=capability,
                    target_key=target, cost=max(0, int(row.get("cost", 0))),
                ),
            ))
    unique = {x.id: x for x in out}
    return [unique[key] for key in sorted(unique)]


def _response_entries(pack: RuntimePackV1, commands: tuple[CommandV1, ...], round: int) -> tuple[list[CostEntryV1], list[ResponseV1], set[str]]:
    entries: list[CostEntryV1] = []
    responses: list[ResponseV1] = []
    prevented: set[str] = set()
    event_map = {event.key: event for event in pack.casepack.events}
    for command in commands:
        if command.op != "respond":
            continue
        event = event_map.get(command.event)
        if event is None:
            raise SimulationError("invalid_reference", "event", {"event": command.event})
        option = next((x for x in event.options if x.key == command.option), None)
        if option is None or command.rationale_tag not in option.tags:
            raise SimulationError("invalid_reference", "response", {"event": command.event})
        cost = int(option.cost) if command.option == "fund" else 0
        effect = pack.runtime.response_disposition.get(event.key)
        effect_name = effect.fund_effect if (command.option == "fund" and effect is not None) else "none"
        responses.append(ResponseV1(round=round, key=command.key, event=event.key, option=command.option, rationale_tag=command.rationale_tag, cost=cost, effect=effect_name))
        if effect_name == "prevent_current_round":
            prevented.add(event.key)
            entries.append(entry(round, "response", command.key, capital=-cost, category="response"))
    return entries, responses, prevented


@dataclass(frozen=True)
class PreparedEffects:
    pack: RuntimePackV1
    prior: CheckpointStateV1
    state: CheckpointStateV1
    commands: tuple[CommandV1, ...]
    round: int
    estate: Any
    organisation: Any
    resources: Any
    charges: tuple[CostEntryV1, ...]
    actions: tuple[ActionEnvelopeV1, ...]
    responses: tuple[ResponseV1, ...]
    prevented: frozenset[str]
    arrivals: tuple[str, ...]
    retirements: tuple[str, ...]
    expiries: tuple[str, ...]
    capital_available: int
    capital_spend: int
    capital_remaining: int
    operating_runrate: int


def prepare_effects(pack: RuntimePackV1, prior: CheckpointStateV1, commands: Iterable[CommandV1], round: int) -> PreparedEffects:
    _valid_round(pack, round)
    cmds = _commands(commands)
    estate = reduce_estate(pack, prior, cmds, round)
    organisation = reduce_organisation(pack, prior, estate, cmds, round)
    base_state = _state_merge(prior, estate, organisation, [])
    response_charges, responses, prevented = _response_entries(pack, cmds, round)
    rec = recurring_entries(pack, base_state, round)
    grant, allowance = grant_and_allowance(pack, round)
    charges = tuple([grant, allowance, *estate.charge_entries, *organisation.charge_entries, *response_charges, *rec])
    capital_delta, operating_delta = totals(charges)
    capital_available = int(prior.capital_balance) + int(grant.capital_delta)
    capital_spend = -sum(x.capital_delta for x in charges if x.capital_delta < 0)
    capital_remaining = capital_available - capital_spend
    operating_runrate = -sum(x.operating_delta for x in rec)
    actions = tuple(_actions(pack, prior, estate, organisation, cmds, round))
    state = _state_merge(prior, estate, organisation, charges)
    return PreparedEffects(pack, prior, state, cmds, round, estate, organisation, resource_view(pack, state, round), charges, actions, tuple(responses), frozenset(prevented), tuple(estate.arrived_ids), tuple(estate.retired_ids), tuple(estate.expired_ids), capital_available, capital_spend, capital_remaining, operating_runrate)


def resource_view(pack: RuntimePackV1, state: CheckpointStateV1, round: int):
    from .resources import resource_projection
    return resource_projection(pack, state.assets, state.connections, state.policies, round)


def _preview(pack: RuntimePackV1, prior: CheckpointStateV1, prepared: PreparedEffects, assessments: list[Any] | None = None) -> PreviewV1:
    forecast = forecast_operating(pack, prior.operating_reserve, prepared.state, prepared.round)
    from .types import OperatingForecastV1
    rows = [OperatingForecastV1.model_validate(row) for row in forecast]
    warnings = []
    if any(x.closing < 0 for x in rows): warnings.append(WarningV1(code="operating_deficit", keys=[str(x.round) for x in rows if x.closing < 0]))
    return PreviewV1(version=1, round=prepared.round, normalized_commands=list(prepared.commands), arrivals=list(prepared.arrivals), retirements=list(prepared.retirements), expiries=list(prepared.expiries), capital_available=prepared.capital_available, capital_spend=prepared.capital_spend, capital_remaining=prepared.capital_remaining, operating_runrate=prepared.operating_runrate, operating_forecast=rows, challenges=[], repair_assessments=[_dump(x) for x in (assessments or [])], prevented_events=sorted(prepared.prevented), would_fire=[], cost_entries=[_dump(x) for x in prepared.charges], warnings=warnings)


def quote_transition(pack: RuntimePackV1, prior: CheckpointStateV1, commands: Iterable[CommandV1], round: int) -> PreviewV1:
    prepared = prepare_effects(pack, prior, commands, round)
    return _preview(pack, prior, prepared)


def _ledger_rows(rows: Iterable[SignalV1]) -> tuple:
    from app.engine.ledger import LedgerSignal
    return tuple(LedgerSignal(**{key: value for key, value in _dump(row).items() if key != "cleared_by"}, cleared_by=tuple(row.cleared_by)) for row in rows)


def _event_records(pack: RuntimePackV1, team_state: Any, ledger: tuple, fired: Iterable[str], round: int) -> tuple[list[dict[str, Any]], list[CostEntryV1]]:
    records: list[dict[str, Any]] = []
    losses: list[CostEntryV1] = []
    events = {event.key: event for event in pack.casepack.events}
    for key in fired:
        event = events[key]
        node = event_engine.failed_node(event, team_state, pack.casepack)
        capability = event_engine.primary_capability(event, pack.casepack)
        evidence = event_engine.outage_duration(team_state, node, capability, pack.casepack) if node and capability else {"node": node, "blast_radius": []}
        records.append({"key": key, "node": node, "outcomes": event.outcomes.model_dump(mode="python"), **evidence})
        if event.outcomes.revenue_loss:
            losses.append(entry(round, "event_loss", key, operating=-int(event.outcomes.revenue_loss), category="event_loss", capability=capability))
    return records, losses


def _tco(pack: RuntimePackV1, prior: CheckpointStateV1, prepared: PreparedEffects) -> list[TcoV1]:
    rows: list[TcoV1] = []
    existing = {row.asset_id for row in prior.tco_forecasts}
    for project in prepared.state.projects.values():
        raw = _dump(project)
        if raw["source_kind"] != "catalog" or raw["asset_id"] in existing or not raw.get("tco_categories"):
            continue
        source = next((x for x in pack.casepack.catalog if x.key == raw["source_key"]), None)
        if source is None: continue
        selected = list(raw["tco_categories"])
        allowed = set(source.true_cost_categories) | set(source.decoy_cost_categories)
        if any(x not in allowed for x in selected) or len(set(selected)) != len(selected):
            raise SimulationError("invalid_input", "tco_categories")
        base = int(raw["paid_capex"])
        estimates = {key: 0 for key in selected}
        forecast = base
        rows.append(TcoV1(asset_id=raw["asset_id"], ordered_round=raw["ordered_round"], selected_categories=selected, forecast=forecast, forecast_horizon_round=pack.casepack.metadata.rounds, estimates=estimates))
    return rows


def resolve_transition(pack: RuntimePackV1, prior: CheckpointStateV1, commands: Iterable[CommandV1], round: int) -> TransitionV1:
    prepared = prepare_effects(pack, prior, commands, round)
    if prepared.capital_remaining < 0:
        raise SimulationError("unaffordable", "capital")
    forecast = forecast_operating(pack, prior.operating_reserve + sum(x.operating_delta for x in prepared.charges), prepared.state, round + 1) if round < pack.casepack.metadata.rounds else []
    # A negative close is allowed when it is caused solely by a reduction/no-op;
    # new discretionary liabilities must stay funded through the horizon.
    if any(row["closing"] < 0 for row in forecast) and prepared.operating_runrate > 0:
        raise SimulationError("unaffordable", "operating")
    staff = StaffPool(staff_fte=float(prepared.organisation.staff.capacity), load_fte=float(prepared.organisation.staff.load))
    alignments = tuple(StakeholderDecisionAlignment(stakeholder=x.stakeholder, alignment=float(x.value), cares_about=tuple(x.cares_about)) for x in prepared.organisation.stakeholder_alignments)
    team_state = project_team_state(pack, prepared.state, round, prepared.resources, staff, alignments, actions=prepared.actions, funds=[prepared.capital_remaining], debt_ratios={}, signals=())
    prior_ledger = _ledger_rows(prior.signal_ledger)
    official_ledger = ledger_engine.advance_ledger(prior_ledger, team_state, pack.casepack)
    signals = ledger_engine.project_signal_state(official_ledger, current_round=round)
    team_state = project_team_state(pack, prepared.state, round, prepared.resources, staff, alignments, actions=prepared.actions, funds=[prepared.capital_remaining], debt_ratios={}, signals=signals)
    fired, suppressed = event_engine.resolve_events(team_state, pack.casepack, official_ledger, frozenset(x.key for x in prior.event_history for x in x.fired))
    fired_records, event_costs = _event_records(pack, team_state, official_ledger, fired, round)
    all_charges = list(prepared.charges) + event_costs
    capital_delta, operating_delta = totals(all_charges)
    new_data = prepared.state.model_dump(mode="python")
    new_data["capital_balance"] = prior.capital_balance + capital_delta
    new_data["operating_reserve"] = prior.operating_reserve + operating_delta
    new_data["signal_ledger"] = [
        {**vars(x), "cleared_by": list(x.cleared_by)} for x in official_ledger
    ]
    existing_debt = {(x.signal, x.episode_id) for x in prior.technical_debt}
    debts = list(prior.technical_debt)
    for row in official_ledger:
        if row.status != "open" or (row.key, row.episode_id) in existing_debt:
            continue
        if row.cheapest_fix_when_raised is not None and row.cheapest_fix_when_raised > 0:
            debts.append(DebtV1(signal=row.key, episode_id=row.episode_id, capability=row.capability, opened_round=row.first_shown_round, amount=int(row.cheapest_fix_when_raised), settled_round=None))
    new_data["technical_debt"] = [_dump(x) for x in debts]
    new_data["action_history"] = [_dump(x) for x in list(prior.action_history) + list(prepared.actions)]
    new_data["response_history"] = [_dump(x) for x in list(prior.response_history) + list(prepared.responses)]
    prior_signals = {x.key: x for x in official_ledger}
    prevented_rows = []
    for response in prepared.responses:
        if response.effect != "prevent_current_round":
            continue
        event = next((x for x in pack.casepack.events if x.key == response.event), None)
        episode_ids = []
        if event is not None:
            wanted = {pc.signal for pc in event.preconditions if pc.type == "signal_open" and pc.signal}
            episode_ids = [SignalEpisodeV1(key=row.key, episode_id=row.episode_id) for key, row in prior_signals.items() if key in wanted and row.status == "open"]
        prevented_rows.append(PreventionEvidenceV1(key=response.event, round=round, option=response.option, rationale_tag=response.rationale_tag, cost=response.cost, effect=response.effect, signal_episodes=episode_ids))
    history_row = EventHistoryV1(
        round=round,
        fired=[EventEvidenceV1.model_validate(x) for x in fired_records],
        suppressed=[{"event_key": x.event_key, "round": x.round, "reason": x.reason, "capability": x.capability} for x in suppressed],
        prevented=prevented_rows,
    )
    new_data["event_history"] = [_dump(x) for x in list(prior.event_history) + [history_row]]
    new_data["cost_ledger"] = [_dump(x) for x in all_charges] + [_dump(x) for x in prior.cost_ledger]
    new_data["available_funds_by_round"] = list(prior.available_funds_by_round) + [prepared.capital_remaining]
    new_data["tco_forecasts"] = [_dump(x) for x in list(prior.tco_forecasts) + _tco(pack, prior, prepared)]
    state = CheckpointStateV1.model_validate(new_data)
    final_score = score_team(pack.casepack, team_state)
    scorecard, scorecard_meta = rolled_scorecard(pack, final_score, fired_records)
    result = {"round": round, "score": final_score.record(), "scorecard": scorecard, "scorecard_meta": scorecard_meta, "events": fired_records, "suppressed_events": [_dump(x) for x in suppressed], "financials": {"capital_balance": state.capital_balance, "operating_reserve": state.operating_reserve}}
    preview = _preview(pack, prior, prepared)
    return TransitionV1(state=state, result=result, preview=preview)

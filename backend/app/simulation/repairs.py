"""Bounded, pure repair assessment seam.

The producer intentionally reports only witnesses that can be proven from the
current immutable checkpoint.  It never mutates the checkpoint or invokes the
public quote/resolve functions recursively.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from app.engine.ledger import evaluate
from app.engine.metrics import metric_value
from app.engine import events as event_engine
from app.engine.state import StaffPool, StakeholderDecisionAlignment

from .consequences import _canonical, prepare_effects, resource_view, _ledger_rows
from .accounting import forecast_operating
from .projection import project_team_state
from .types import (
    CheckpointStateV1, CommandV1, OperatingForecastV1, RepairAssessmentV1,
    RepairExcludedV1, RepairWitnessV1, RuntimePackV1, SimulationError,
)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _catalogue_commands(pack: RuntimePackV1, state: CheckpointStateV1, rule_key: str, capability: str, round: int) -> list[CommandV1]:
    """Enumerate the finite non-training P4 repair families in canonical order."""
    commands: list[CommandV1] = []
    def add(op: str, **fields: Any) -> None:
        seed = _digest([rule_key, op, fields])[:16]
        commands.append(CommandV1(key=f"repair_{seed}", op=op, **fields))
    for source in sorted(pack.casepack.catalog, key=lambda x: x.key):
        if capability not in source.serves:
            continue
        for placement, mode in sorted(source.deployment_modes.items(), key=lambda x: x[0].value):
            for config in sorted(source.config_tiers):
                if placement.value in pack.runtime.catalog[source.key].purchasable_placements:
                    add("buy_application", catalog=source.key, placement=placement.value, config=config, primary_for=None, tco_categories=[])
    for service in sorted(pack.casepack.platform.services, key=lambda x: x.key):
        for placement in sorted(service.placement_options, key=lambda x: x.value):
            if capability in pack.runtime.services[service.key].serves:
                for units in range(1, pack.runtime.services[service.key].max_units + 1):
                    add("buy_service", service=service.key, placement=placement.value, units=units)
    for asset_id, asset in sorted(state.assets.items()):
        if asset.source_kind == "catalog" and capability in next(x for x in pack.casepack.catalog if x.key == asset.source_key).serves:
            source = next(x for x in pack.casepack.catalog if x.key == asset.source_key)
            for placement in sorted(source.deployment_modes, key=lambda x: x.value):
                for config in sorted(source.config_tiers):
                    add("replace_application", asset=asset_id, placement=placement.value, config=config)
        elif asset.source_kind == "service":
            service = next((x for x in pack.casepack.platform.services if x.key == asset.source_key), None)
            if service:
                for placement in sorted(service.placement_options, key=lambda x: x.value):
                    for units in range(1, pack.runtime.services[service.key].max_units + 1):
                        add("replace_service", asset=asset_id, placement=placement.value, units=units)
    for policy in sorted(pack.casepack.policies, key=lambda x: x.key):
        for selected in policy.options:
            add("set_policy", policy=policy.key, selected=selected)
    for tier in sorted(pack.casepack.platform.support_tiers, key=lambda x: x.key):
        add("set_support", tier=tier.key, covered_assets=sorted(key for key, value in state.assets.items() if value.source_kind == "catalog"))
    catalogs = {item.key: item for item in pack.casepack.catalog}
    for src_id, src_asset in sorted(state.assets.items()):
        if src_asset.source_kind != "catalog":
            continue
        src = catalogs.get(src_asset.source_key)
        if src is None:
            continue
        for dst_id, dst_asset in sorted(state.assets.items()):
            if src_id == dst_id or dst_asset.source_kind != "catalog":
                continue
            dst = catalogs.get(dst_asset.source_key)
            if dst is None:
                continue
            for dependency in dst.must_be_fed_by:
                if not any(owner.entity == dependency.entity for owner in src.owns_entities):
                    continue
                for tier in sorted(pack.casepack.platform.integration_tiers, key=lambda x: x.key):
                    add("connect", src=src_id, dst=dst_id, kind="integration", entity=dependency.entity, tier=tier.key)
    return commands


def assess_repairs(pack: RuntimePackV1, prior: CheckpointStateV1, commands: Iterable[CommandV1], round: int, prepared: Any | None = None) -> list[RepairAssessmentV1]:
    """Return one typed assessment for every authored watch rule.

    This v1 catalogue is deliberately conservative: a rule is ``unassessed``
    unless a real current ledger row is open and a bounded candidate can be
    checked without inventing a future command or changing the source pack.
    """
    if prepared is None:
        prepared = prepare_effects(pack, prior, commands, round)
    digest = _digest(prior)
    merged_digest = _digest(list(prepared.commands))
    staff = StaffPool(staff_fte=float(prepared.organisation.staff.capacity), load_fte=float(prepared.organisation.staff.load))
    alignments = tuple(StakeholderDecisionAlignment(stakeholder=x.stakeholder, alignment=float(x.value), cares_about=tuple(x.cares_about)) for x in prepared.organisation.stakeholder_alignments)
    team = project_team_state(pack, prepared.state, round, prepared.resources, staff, alignments, actions=prepared.actions, funds=[prepared.capital_remaining], debt_ratios={}, signals=())
    results: list[RepairAssessmentV1] = []
    prior_by_signal = {row.key: row for row in prior.signal_ledger}
    prior_engine_ledger = _ledger_rows(prior.signal_ledger)
    for rule in sorted(pack.casepack.watch_rules, key=lambda x: x.key):
        raised = evaluate(rule, team, pack.casepack)
        latest = prior_by_signal.get(rule.key)
        if raised is None and latest is None:
            results.append(_assessment(round, rule.key, digest, merged_digest, [], []))
            continue
        candidates: list[RepairWitnessV1] = []
        uncredited: list[RepairWitnessV1] = []
        excluded: list[RepairExcludedV1] = []
        # The bounded v1 catalogue includes legal effectful training and
        # process choices for currently live catalog assets.  It is finite,
        # deterministic and uses the same reducer from the same prior state.
        live_assets = sorted((key, value) for key, value in prior.assets.items()
                             if value.source_kind == "catalog" and value.installed_round <= round
                             and (value.retired_round is None or value.retired_round > round))
        for asset_id, asset in live_assets:
            source = next((item for item in pack.casepack.catalog if item.key == asset.source_key), None)
            if source is None or rule.capability not in source.serves:
                continue
            options = []
            if "add_training" in rule.cleared_by:
                options.extend(("train", key) for key, option in sorted(source.training_options.items()) if option.coverage > 0 and key != "none")
            if "redesign_process" in rule.cleared_by and source.process_option is not None:
                options.append(("set_process", "redesigned"))
            for op, option in options:
                key_seed = _digest([rule.key, asset_id, op, option])[:16]
                command = CommandV1(key=f"repair_{key_seed}", op=op, asset=asset_id, option=option) if op == "train" else CommandV1(key=f"repair_{key_seed}", op=op, asset=asset_id, choice=option)
                if any(item.key == command.key for item in prepared.commands):
                    excluded.append(RepairExcludedV1(candidate_key=_digest([command.model_dump(mode="python")]), reason="command_key_collision"))
                    continue
                try:
                    candidate_prepared = prepare_effects(pack, prior, tuple(prepared.commands) + (command,), round)
                except SimulationError as exc:
                    excluded.append(RepairExcludedV1(candidate_key=_digest([command.model_dump(mode="python")]), reason=exc.code if exc.code in {"not_found", "invalid_input", "invalid_reference", "conflicting_commands", "unaffordable", "revision_conflict", "locked", "round_state", "pack_mismatch", "scope_exists", "unsupported_operation", "arrival_after_game_end", "invalid_output", "held_response_ineligible", "command_key_collision", "baseline_not_raised", "metric_not_repaired", "no_positive_path", "no_in_game_effect"} else "invalid_input"))
                    continue
                candidate_resources = candidate_prepared.resources
                candidate_staff = StaffPool(staff_fte=float(candidate_prepared.organisation.staff.capacity), load_fte=float(candidate_prepared.organisation.staff.load))
                candidate_align = tuple(StakeholderDecisionAlignment(stakeholder=x.stakeholder, alignment=float(x.value), cares_about=tuple(x.cares_about)) for x in candidate_prepared.organisation.stakeholder_alignments)
                candidate_team = project_team_state(pack, candidate_prepared.state, round, candidate_resources, candidate_staff, candidate_align, actions=candidate_prepared.actions, funds=[candidate_prepared.capital_remaining], debt_ratios={}, signals=())
                if prepared.responses and any(not event_engine._satisfiable(next(event for event in pack.casepack.events if event.key == response.event), candidate_team, pack.casepack, prior_engine_ledger) for response in prepared.responses if response.effect == "prevent_current_round"):
                    excluded.append(RepairExcludedV1(candidate_key=_digest([command.model_dump(mode="python")]), reason="held_response_ineligible"))
                    continue
                after = evaluate(rule, candidate_team, pack.casepack)
                if raised is None or after is not None:
                    excluded.append(RepairExcludedV1(candidate_key=_digest([command.model_dump(mode="python")]), reason="metric_not_repaired" if raised is not None else "baseline_not_raised"))
                    continue
                matching = [action for action in candidate_prepared.actions if action.record.action_type in rule.cleared_by and action.record.locked_round == round]
                candidate_key = _digest([command.model_dump(mode="python")])
                raw_forecast = forecast_operating(pack, prior.operating_reserve, candidate_prepared.state, round)
                # OperatingForecastV1 is a committed nonnegative schedule.  A
                # hypothetical witness may be signed while proving that it is
                # unaffordable, so retain a bounded display schedule and carry
                # affordability separately.
                forecast = [OperatingForecastV1.model_validate({key: max(0, value) for key, value in row.items()}) for row in raw_forecast]
                affordable = candidate_prepared.capital_remaining >= 0 and all(row["closing"] >= 0 for row in raw_forecast)
                candidate_metric = after[1] if isinstance(after, tuple) else False
                witness = RepairWitnessV1(candidate_key=candidate_key, commands=[command], capital_cost=max(0, candidate_prepared.capital_spend - prepared.capital_spend), effective_round=round, affordable=affordable, operating_forecast=forecast, baseline_metric=raised[1] if isinstance(raised, tuple) else bool(raised), candidate_metric=candidate_metric, emitted_action_ids=[item.id for item in matching], credit_eligible=bool(matching) and affordable, assumptions="empty_future_decisions")
                (candidates if witness.credit_eligible else uncredited).append(witness) if matching else excluded.append(RepairExcludedV1(candidate_key=candidate_key, reason="no_in_game_effect"))
        # The remaining approved families are enumerated even when they cannot
        # repair this watch.  Their failed verification is retained as an
        # explicit exclusion rather than silently dropping the catalogue row.
        seen_candidate_keys = {item.candidate_key for item in candidates} | {item.candidate_key for item in excluded}
        processed_families: set[str] = set()
        for command in _catalogue_commands(pack, prior, rule.key, rule.capability, round):
            candidate_key = _digest([command.model_dump(mode="python")])
            if candidate_key in seen_candidate_keys or any(item.key == command.key for item in prepared.commands):
                continue
            family = "replace" if command.op.startswith("replace") else command.op
            if family in processed_families:
                excluded.append(RepairExcludedV1(candidate_key=candidate_key, reason="no_in_game_effect"))
                continue
            processed_families.add(family)
            try:
                candidate_prepared = prepare_effects(pack, prior, tuple(prepared.commands) + (command,), round)
                candidate_staff = StaffPool(staff_fte=float(candidate_prepared.organisation.staff.capacity), load_fte=float(candidate_prepared.organisation.staff.load))
                candidate_align = tuple(StakeholderDecisionAlignment(stakeholder=x.stakeholder, alignment=float(x.value), cares_about=tuple(x.cares_about)) for x in candidate_prepared.organisation.stakeholder_alignments)
                candidate_team = project_team_state(pack, candidate_prepared.state, round, candidate_prepared.resources, candidate_staff, candidate_align, actions=candidate_prepared.actions, funds=[candidate_prepared.capital_remaining], debt_ratios={}, signals=())
                if prepared.responses and any(not event_engine._satisfiable(next(event for event in pack.casepack.events if event.key == response.event), candidate_team, pack.casepack, prior_engine_ledger) for response in prepared.responses if response.effect == "prevent_current_round"):
                    excluded.append(RepairExcludedV1(candidate_key=candidate_key, reason="held_response_ineligible"))
                    continue
                after = evaluate(rule, candidate_team, pack.casepack)
                matching = [action for action in candidate_prepared.actions if action.record.action_type in rule.cleared_by and action.record.locked_round == round]
                if raised is not None and after is None and matching:
                    raw_forecast = forecast_operating(pack, prior.operating_reserve, candidate_prepared.state, round)
                    forecast = [OperatingForecastV1.model_validate({key: max(0, value) for key, value in row.items()}) for row in raw_forecast]
                    affordable = candidate_prepared.capital_remaining >= 0 and all(row["closing"] >= 0 for row in raw_forecast)
                    witness = RepairWitnessV1(candidate_key=candidate_key, commands=[command], capital_cost=max(0, candidate_prepared.capital_spend - prepared.capital_spend), effective_round=round, affordable=affordable, operating_forecast=forecast, baseline_metric=raised[1], candidate_metric=metric_value(rule, candidate_team, pack.casepack), emitted_action_ids=[item.id for item in matching], credit_eligible=affordable, assumptions="empty_future_decisions")
                    (candidates if witness.credit_eligible else uncredited).append(witness)
                else:
                    excluded.append(RepairExcludedV1(candidate_key=candidate_key, reason="metric_not_repaired" if raised is not None else "baseline_not_raised"))
            except SimulationError as exc:
                excluded.append(RepairExcludedV1(candidate_key=candidate_key, reason=exc.code if exc.code in {"not_found", "invalid_input", "invalid_reference", "conflicting_commands", "unaffordable", "revision_conflict", "locked", "round_state", "pack_mismatch", "scope_exists", "unsupported_operation", "arrival_after_game_end", "invalid_output"} else "invalid_input"))
        candidates.sort(key=lambda item: (item.capital_cost, item.candidate_key))
        results.append(_assessment(round, rule.key, digest, merged_digest, candidates, excluded, uncredited))
    return results


def _assessment(round: int, signal: str, digest: str, merged_digest: str, candidates: list[RepairWitnessV1], excluded: list[RepairExcludedV1], uncredited: list[RepairWitnessV1] | None = None) -> RepairAssessmentV1:
    eligible = [x for x in candidates if x.credit_eligible]
    return RepairAssessmentV1(round=round, signal=signal, status="verified" if eligible else "unassessed", reason=None if eligible else "bounded_catalogue_no_verified_repair", initial_state_digest=digest, merged_sheet_digest=merged_digest, candidates=candidates, repaired_but_uncredited=uncredited or [], excluded=excluded)


def repair_assessments_for_engine(pack: RuntimePackV1, assessments: Iterable[RepairAssessmentV1]) -> dict[str, Any]:
    """Convert public history rows to the engine's compact assessment seam."""
    from app.engine.state import RepairAssessment, RepairCandidate
    return {row.signal: RepairAssessment(signal=row.signal, checked_round=row.round, candidates=tuple(RepairCandidate(candidate_key=item.candidate_key, capital_cost=item.capital_cost, effective_round=item.effective_round, affordable=item.affordable) for item in row.candidates if item.credit_eligible)) for row in assessments}

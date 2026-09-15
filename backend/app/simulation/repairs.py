"""Bounded, pure repair assessment seam.

The producer intentionally reports only witnesses that can be proven from the
current immutable checkpoint.  It never mutates the checkpoint or invokes the
public quote/resolve functions recursively.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from app.engine.ledger import evaluate
from app.engine.state import StaffPool, StakeholderDecisionAlignment

from .consequences import _canonical, prepare_effects, resource_view
from .accounting import forecast_operating
from .projection import project_team_state
from .types import (
    CheckpointStateV1, CommandV1, OperatingForecastV1, RepairAssessmentV1,
    RepairExcludedV1, RepairWitnessV1, RuntimePackV1, SimulationError,
)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


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
    for rule in sorted(pack.casepack.watch_rules, key=lambda x: x.key):
        raised = evaluate(rule, team, pack.casepack)
        latest = prior_by_signal.get(rule.key)
        if raised is None and latest is None:
            results.append(_assessment(round, rule.key, digest, merged_digest, [], []))
            continue
        candidates: list[RepairWitnessV1] = []
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
                candidates.append(RepairWitnessV1(candidate_key=candidate_key, commands=[command], capital_cost=max(0, candidate_prepared.capital_spend - prepared.capital_spend), effective_round=round, affordable=affordable, operating_forecast=forecast, baseline_metric=raised[1] if isinstance(raised, tuple) else bool(raised), candidate_metric=0.0, emitted_action_ids=[item.id for item in matching], credit_eligible=bool(matching) and affordable, assumptions="empty_future_decisions"))
        candidates.sort(key=lambda item: (item.capital_cost, item.candidate_key))
        results.append(_assessment(round, rule.key, digest, merged_digest, candidates, excluded))
    return results


def _assessment(round: int, signal: str, digest: str, merged_digest: str, candidates: list[RepairWitnessV1], excluded: list[RepairExcludedV1]) -> RepairAssessmentV1:
    eligible = [x for x in candidates if x.credit_eligible]
    return RepairAssessmentV1(round=round, signal=signal, status="verified" if eligible else "unassessed", reason=None if eligible else "bounded_catalogue_no_verified_repair", initial_state_digest=digest, merged_sheet_digest=merged_digest, candidates=candidates, repaired_but_uncredited=[], excluded=excluded)


def repair_assessments_for_engine(pack: RuntimePackV1, assessments: Iterable[RepairAssessmentV1]) -> dict[str, Any]:
    """Convert public history rows to the engine's compact assessment seam."""
    from app.engine.state import RepairAssessment
    return {row.signal: RepairAssessment(signal=row.signal, checked_round=row.round, candidates=tuple()) for row in assessments}

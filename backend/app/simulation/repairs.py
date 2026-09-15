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
from .projection import project_team_state
from .types import (
    CheckpointStateV1, CommandV1, OperatingForecastV1, RepairAssessmentV1,
    RepairExcludedV1, RuntimePackV1, SimulationError,
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
            results.append(RepairAssessmentV1(round=round, signal=rule.key, status="unassessed", reason="bounded_catalogue_no_verified_repair", initial_state_digest=digest, merged_sheet_digest=merged_digest, candidates=[], repaired_but_uncredited=[], excluded=[]))
            continue
        # The status is useful even when there is no verified candidate.  Keep
        # the explicit reason so P0b cannot mistake an empty list for free repair.
        results.append(RepairAssessmentV1(round=round, signal=rule.key, status="unassessed", reason="bounded_catalogue_no_verified_repair", initial_state_digest=digest, merged_sheet_digest=merged_digest, candidates=[], repaired_but_uncredited=[], excluded=[]))
    return results


def repair_assessments_for_engine(pack: RuntimePackV1, assessments: Iterable[RepairAssessmentV1]) -> dict[str, Any]:
    """Convert public history rows to the engine's compact assessment seam."""
    from app.engine.state import RepairAssessment
    return {row.signal: RepairAssessment(signal=row.signal, checked_round=row.round, candidates=tuple()) for row in assessments}

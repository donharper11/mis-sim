"""Organisational Readiness -- computed from what was funded (spec 5.2).

org(c) = geomean(training, process_fit, adoption, resistance_inv, staffing)

The capability's Organisation term reads its *primary* rollout -- the application
whose people are being asked to change. Training coverage, the process choice and
adoption are that deployment's state; resistance is its org unit's; staffing is the
firm-wide IT capacity pool (G1). A separate rollout that serves the same capability
but is not its primary (the warehouse system behind order fulfilment) shows up in
follow-through and in its own signal, not by dragging this term -- which is why the
spec's worked example reads training 49/140, process partial, and nothing about the
warehouse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engine.mathx import clamp, geomean
from app.engine.state import TeamState


#: process_fit mapping (spec 5.2): a full redesign, a partial one, or nothing.
PROCESS_FIT = {"redesigned": 1.0, "partial": 0.5, "unchanged": 0.25}


@dataclass
class OrgResult:
    value: float
    sub_factors: dict[str, float]
    evidence: dict[str, Any] = field(default_factory=dict)


def staffing_factor(state: TeamState) -> float:
    """IT capacity pool (G1): min(1, capacity / load). Over-commitment is a
    modifier on a term already scored, not a fourth term."""
    load = state.staff.load_fte
    if load <= 0:
        return 1.0
    return clamp(state.staff.staff_fte / load)


def organisation(state: TeamState, cap_key: str) -> OrgResult:
    staffing = staffing_factor(state)
    dep = state.primary_deployment(cap_key)

    evidence: dict[str, Any] = {}
    if dep is None:
        # No primary rollout: nothing has been rolled out to anyone. The people
        # terms are floored at zero (geomean will crush the term), which is the
        # honest reading of an unstaffed capability.
        sub_factors = {
            "training": 0.0,
            "process_fit": 0.0,
            "adoption": 0.0,
            "resistance_inv": 0.0,
            "staffing": round(staffing, 6),
        }
        evidence["primary_deployment"] = None
        return OrgResult(value=0.0, sub_factors=sub_factors, evidence=evidence)

    training = clamp(dep.trained_count / dep.people_affected) if dep.people_affected else 0.0
    process_fit = PROCESS_FIT.get(dep.process, 0.25)
    adoption = clamp(dep.adoption)
    unit = state.org_unit(dep.org_unit)
    resistance = unit.resistance if unit is not None else 0.0
    resistance_inv = clamp(1.0 - resistance)

    sub_factors = {
        "training": round(training, 6),
        "process_fit": round(process_fit, 6),
        "adoption": round(adoption, 6),
        "resistance_inv": round(resistance_inv, 6),
        "staffing": round(staffing, 6),
    }
    value = geomean(list(sub_factors.values()))

    evidence["training"] = {"trained": dep.trained_count, "affected": dep.people_affected}
    evidence["process"] = dep.process
    evidence["resistance"] = round(resistance, 6)
    evidence["staffing"] = {"staff_fte": state.staff.staff_fte, "load_fte": state.staff.load_fte}

    return OrgResult(value=round(value, 6), sub_factors=sub_factors, evidence=evidence)

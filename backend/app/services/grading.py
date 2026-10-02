"""M5.5 grade derivation, override, and CSV export service.

Grades are computed from persisted RoundResult scorecard data.  This module
never recomputes scores or modifies RoundResult rows.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grading import GradeConfig, GradeOverride
from app.models.platform import Course, Section, SimulationInstance, Team
from app.round.models import RoundResult, TeamStateRow


BSC_DIMS = ("financial", "customer", "internal_process", "learning_growth")

DEFAULT_WEIGHTS = {
    "weight_financial": 0.25,
    "weight_customer": 0.25,
    "weight_internal_process": 0.25,
    "weight_learning_growth": 0.25,
}


def derive_grade(scorecard: dict[str, float], config: dict[str, float]) -> float:
    """Compute a weighted average of the four BSC dimensions."""
    return (
        scorecard.get("financial", 0.0) * config.get("weight_financial", 0.25)
        + scorecard.get("customer", 0.0) * config.get("weight_customer", 0.25)
        + scorecard.get("internal_process", 0.0) * config.get("weight_internal_process", 0.25)
        + scorecard.get("learning_growth", 0.0) * config.get("weight_learning_growth", 0.25)
    )


def _average_scorecards(results: list[dict]) -> dict[str, float]:
    """Average the scorecard values across multiple round results."""
    if not results:
        return {}
    totals: dict[str, float] = {dim: 0.0 for dim in BSC_DIMS}
    count = len(results)
    for result in results:
        scorecard = result.get("scorecard", {})
        for dim in BSC_DIMS:
            totals[dim] += scorecard.get(dim, 0.0)
    return {dim: totals[dim] / count for dim in BSC_DIMS}


async def get_config(session: AsyncSession, instance_id: int) -> dict[str, Any]:
    """Return the grade config for the instance, or defaults."""
    row = await session.get(GradeConfig, instance_id)
    if row is None:
        return {**DEFAULT_WEIGHTS, "rounds_mode": "final"}
    return {
        "weight_financial": row.weight_financial,
        "weight_customer": row.weight_customer,
        "weight_internal_process": row.weight_internal_process,
        "weight_learning_growth": row.weight_learning_growth,
        "rounds_mode": row.rounds_mode,
    }


async def get_team_grades(session: AsyncSession, instance_id: int) -> dict[str, Any]:
    """Compute the full grade read model for an instance."""
    config = await get_config(session, instance_id)

    # Fetch all teams for this instance
    teams = list((await session.scalars(
        select(Team).where(Team.instance_id == instance_id).order_by(Team.id)
    )).all())

    # Fetch all round results for this instance
    results = list((await session.scalars(
        select(RoundResult).where(RoundResult.instance_id == instance_id).order_by(RoundResult.round)
    )).all())

    # Group results by team_id
    results_by_team: dict[int, list[dict]] = {}
    for result in results:
        results_by_team.setdefault(result.team_id, []).append(result.payload)

    # Fetch overrides
    overrides = list((await session.scalars(
        select(GradeOverride).where(GradeOverride.instance_id == instance_id)
    )).all())
    overrides_by_team = {o.team_id: o for o in overrides}

    # Fetch strategy from TeamStateRow if available
    team_states = list((await session.scalars(
        select(TeamStateRow).where(TeamStateRow.instance_id == instance_id)
    )).all())
    strategy_by_team = {ts.team_id: ts.declared_strategy for ts in team_states}

    team_grades = []
    for team in teams:
        team_results = results_by_team.get(team.id, [])
        override_row = overrides_by_team.get(team.id)

        # Derive scorecard based on rounds_mode
        scorecard: dict[str, float] | None = None
        derived_grade: float | None = None
        final_realised_value: float | None = None

        if team_results:
            if config["rounds_mode"] == "average":
                scorecard = _average_scorecards(team_results)
            else:
                # Final mode: use last completed round
                final_payload = team_results[-1]
                scorecard = {
                    dim: final_payload.get("scorecard", {}).get(dim, 0.0)
                    for dim in BSC_DIMS
                }
            derived_grade = round(derive_grade(scorecard, config), 6)
            # Get the final realised value (firm_score) from the last round
            final_realised_value = team_results[-1].get("firm_score")

        # Determine final_grade
        override_value = float(override_row.override) if override_row and override_row.override is not None else None
        override_reason = override_row.reason if override_row else None
        final_grade = override_value if override_value is not None else derived_grade

        strategy = strategy_by_team.get(team.id)

        team_grades.append({
            "team_id": team.id,
            "team_name": team.name,
            "strategy": strategy,
            "final_realised_value": final_realised_value,
            "scorecard": scorecard if scorecard else {dim: None for dim in BSC_DIMS},
            "derived_grade": derived_grade,
            "override": override_value,
            "override_reason": override_reason,
            "final_grade": final_grade,
        })

    return {
        "instance_id": instance_id,
        "config": config,
        "teams": team_grades,
    }


def validate_weights(
    weight_financial: float,
    weight_customer: float,
    weight_internal_process: float,
    weight_learning_growth: float,
) -> str | None:
    """Validate weight constraints.  Returns error message or None."""
    weights = [weight_financial, weight_customer, weight_internal_process, weight_learning_growth]
    for w in weights:
        if w < 0:
            return "Weights must be non-negative"
    total = sum(weights)
    if abs(total - 1.0) > 0.01:
        return f"Weights must sum to 1.0 (got {total:.4f})"
    return None


async def export_csv(session: AsyncSession, instance_id: int) -> tuple[str, str]:
    """Generate CSV content and suggested filename.

    Returns (csv_string, filename).
    """
    grades_data = await get_team_grades(session, instance_id)

    # Look up course and section for the filename
    instance = await session.get(SimulationInstance, instance_id)
    section = await session.get(Section, instance.section_id) if instance else None
    course = await session.get(Course, section.course_id) if section else None

    course_code = course.course_code if course else "UNKNOWN"
    section_code = section.section_code if section else "UNKNOWN"
    filename = f"{course_code}_{section_code}_grades.csv"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "team_name", "strategy", "final_realised_value",
        "financial", "customer", "internal_process", "learning_growth",
        "instructor_override", "final_grade", "override_reason",
    ])

    for team in grades_data["teams"]:
        sc = team["scorecard"]
        writer.writerow([
            team["team_name"],
            team["strategy"] or "",
            team["final_realised_value"] if team["final_realised_value"] is not None else "",
            sc.get("financial") if sc.get("financial") is not None else "",
            sc.get("customer") if sc.get("customer") is not None else "",
            sc.get("internal_process") if sc.get("internal_process") is not None else "",
            sc.get("learning_growth") if sc.get("learning_growth") is not None else "",
            team["override"] if team["override"] is not None else "",
            team["final_grade"] if team["final_grade"] is not None else "",
            team["override_reason"] or "",
        ])

    return output.getvalue(), filename

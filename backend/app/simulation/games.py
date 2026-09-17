"""Deterministic headless production games for Simulation v1.

This module is deliberately a thin consumer of :class:`SimulationService`.
Plans contain typed command fields only; reducers and content remain the sole
owners of prices, state, effects, scores and persistence.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from .service import SimulationService
from .types import COMMAND_FIELDS, SheetPatchV1, SimulationError, RuntimePackV1


ARCHETYPES = ("balanced", "all_tech_no_org", "do_nothing", "overspender")
ORG_OPERATIONS = {"train", "set_process", "communicate", "assign", "set_policy", "hire"}

# M4 calibration profiles deliberately affect only the coherent plan. The three
# negative controls remain the exact checked-in fixture so their penalties stay
# interpretable. These are plan choices, not scoring constants.
STRATEGY_PLAN_PROFILES: dict[str, dict[str, Any]] = {
    "cost_leadership": {"customer_placement": "cloud", "focus": "order_fulfilment"},
    "differentiation": {"customer_placement": "on_prem", "focus": "customer_insight"},
    "customer_supplier_intimacy": {"customer_placement": "cloud", "focus": "customer_insight"},
    "focus_strategy": {"customer_placement": "on_prem", "focus": "order_fulfilment"},
}


def _command(key: str, op: str, **fields: Any) -> dict[str, Any]:
    return {"key": key, "op": op, **fields}


def _patch(commands: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {
        "buy_application": "application", "buy_service": "platform_service",
        "connect": "integration", "train": "training", "set_process": "process_redesign",
        "assign": "governance", "communicate": "communication", "set_policy": "policy",
        "respond": "event_response", "hire": "staffing",
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for command in commands:
        grouped.setdefault(categories[command["op"]], []).append(command)
    return {
        "version": 1,
        "replace_categories": {
            category: sorted(rows, key=lambda row: row["key"])
            for category, rows in sorted(grouped.items())
        },
    }


FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "simulation_v1_decisions.json"


class _ExecutionPack:
    """One detached pack view for a bounded playthrough batch.

    RuntimePackV1 intentionally returns a defensive deepcopy on every public
    access. A matrix is read-only, so copying once preserves that boundary while
    avoiding repeated deepcopies across the repair catalogue.
    """

    def __init__(self, pack: RuntimePackV1):
        self.casepack = pack.casepack
        self.runtime = pack.runtime
        self.pack_digest = pack.pack_digest
        self.canonical_bytes = pack.canonical_bytes


def _fixture() -> dict[str, dict[str, Any]]:
    rows = json.loads(FIXTURE.read_text())
    if not isinstance(rows, list):
        raise SimulationError("invalid_output", "decision_fixture")
    result = {str(row["archetype"]): row for row in rows}
    if set(result) != set(ARCHETYPES):
        raise SimulationError("invalid_output", "decision_fixture.archetypes")
    return result


def decision_plan(archetype: str, pack: RuntimePackV1, strategy: str | None = None) -> list[SheetPatchV1]:
    """Load six typed accepted patches from the checked-in decision fixture."""
    if archetype not in ARCHETYPES:
        raise SimulationError("invalid_input", "archetype")
    if strategy is not None and strategy not in {item.key for item in pack.casepack.strategies}:
        raise SimulationError("invalid_reference", "strategy", {"strategy": strategy})
    rows = _fixture()[archetype]["rounds"]
    if len(rows) != pack.casepack.metadata.rounds:
        raise SimulationError("invalid_output", "decision_fixture.rounds")
    return [SheetPatchV1.model_validate(row["accepted"]) for row in rows]


_fixture_decision_plan = decision_plan


def _command_payload(command: Any) -> dict[str, Any]:
    """Keep only the typed operation fields while retaining explicit nulls."""
    raw = command.model_dump(mode="python", exclude_none=False)
    allowed = {"key", "op", *COMMAND_FIELDS[command.op]}
    return {
        key: value for key, value in raw.items()
        if key in allowed and (value is not None or key in command.model_fields_set)
    }


def calibrated_strategy_plan(
    archetype: str, pack: RuntimePackV1, strategy: str
) -> list[SheetPatchV1]:
    """Return the bounded M4 plan-calibration variant.

    The authored fixture remains the source for every plan. For the coherent plan,
    calibration adds explicit policy decisions in rounds that otherwise leave the
    switches untouched, trains the small live order-data cluster, and varies the
    customer-system placement by declared strategy. This gives the Management term
    a real decision pattern to review without changing engine formulas or weakening
    the negative controls.
    """
    plans = _fixture_decision_plan(archetype, pack, strategy)
    if archetype != "balanced":
        return plans
    profile = STRATEGY_PLAN_PROFILES[strategy]
    policy_defaults = {
        "access_logging": "unlogged", "data_access": "open_to_all_staff",
        "data_collection": "everything_by_default", "data_egress": "unrestricted",
        "data_retention": "indefinite", "staff_monitoring": "untracked",
    }
    calibrated: list[SheetPatchV1] = []
    for round_number, patch in enumerate(plans, 1):
        categories = {
            category: [_command_payload(command) for command in commands]
            for category, commands in patch.replace_categories.items()
        }
        policy_rows = categories.setdefault("policy", [])
        selected_policies = {row.get("policy") for row in policy_rows}
        for policy, selected in policy_defaults.items():
            if policy not in selected_policies:
                policy_rows.append({
                    "key": f"calibrate_{round_number}_{policy}", "op": "set_policy",
                    "policy": policy, "selected": selected,
                })
        if round_number == 2:
            categories.setdefault("training", []).extend([
                {"key": "calibrate_order_data", "op": "train", "asset": "initial_order_db_cluster", "option": "full"},
                {"key": "calibrate_pos", "op": "train", "asset": "initial_pos_system_2011", "option": "full"},
                {"key": "calibrate_accounting", "op": "train", "asset": "initial_accounting_package", "option": "full"},
                {"key": "calibrate_spreadsheets", "op": "train", "asset": "initial_store_spreadsheets", "option": "full"},
                {"key": "calibrate_backoffice", "op": "train", "asset": "initial_store_back_office_pc", "option": "full"},
            ])
        if round_number == 3:
            application_rows = categories.setdefault("application", [])
            customer = next((row for row in application_rows if row.get("key") == "customer"), None)
            if customer is not None:
                customer["placement"] = profile["customer_placement"]
        calibrated.append(SheetPatchV1.model_validate({
            "version": 1, "replace_categories": categories,
        }))
    return calibrated


def _assert_finite(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise SimulationError("invalid_output", "game.result")
    if isinstance(value, dict):
        for item in value.values():
            _assert_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_finite(item)


def _overspender_attempt() -> dict[str, Any]:
    row = _fixture()["overspender"]["rounds"][0]
    return row["attempt"]


def _empty_patch() -> SheetPatchV1:
    """Typed empty replacement used to clear a refused draft on retry."""
    return SheetPatchV1.model_validate({
        "version": 1,
        "replace_categories": {
            category: [] for category in (
                "application", "platform_service", "integration", "lifecycle",
                "training", "process_redesign", "communication", "staffing",
                "governance", "policy", "event_response", "capital_request",
            )
        },
    })


def run_game(
    engine,
    pack: RuntimePackV1,
    archetype: str,
    strategy: str,
    instance_id: int,
    team_id: int,
    *,
    plans: list[SheetPatchV1] | None = None,
) -> list[dict]:
    """Run six typed decision rounds through the production service.

    The caller supplies an already migrated engine.  This function never creates
    tables, seeds legacy rows, supplies prices/scores, or writes outside the
    service's transaction boundary.
    """
    if archetype not in ARCHETYPES:
        raise SimulationError("invalid_input", "archetype")
    if strategy not in {item.key for item in pack.casepack.strategies}:
        raise SimulationError("invalid_reference", "strategy", {"strategy": strategy})
    service = SimulationService(engine, pack)
    service.initialize(instance_id, team_id, strategy)
    plans = plans if plans is not None else decision_plan(archetype, pack, strategy)
    reports: list[dict] = []
    for round, raw_patch in enumerate(plans, 1):
        if archetype == "overspender" and round == 1:
            before = service.read(instance_id, team_id)
            attempt = service.patch_sheet(instance_id, team_id, round, 0, SheetPatchV1.model_validate(_overspender_attempt()))
            locked_attempt = service.lock(instance_id, team_id, round, attempt.revision)
            try:
                service.advance(instance_id, team_id, round, locked_attempt.locked_revision)
            except SimulationError as exc:
                if exc.code not in {"unaffordable", "arrival_after_game_end"}:
                    raise
            else:
                raise SimulationError("invalid_output", "overspender.refusal")
            reopened = service.reopen(instance_id, team_id, round, locked_attempt.locked_revision)
            after = service.read(instance_id, team_id)
            if before.state != after.state:
                raise SimulationError("invalid_output", "overspender.atomicity")
            patch = _empty_patch()
            edited = service.patch_sheet(instance_id, team_id, round, reopened.revision, patch)
            locked = service.lock(instance_id, team_id, round, edited.revision)
            result = service.advance(instance_id, team_id, round, locked.locked_revision)
            _assert_finite(result)
            reports.append(copy.deepcopy(result))
            continue
        patch = SheetPatchV1.model_validate(raw_patch)
        edited = service.patch_sheet(instance_id, team_id, round, 0, patch)
        locked = service.lock(instance_id, team_id, round, edited.revision)
        result = service.advance(instance_id, team_id, round, locked.locked_revision)
        _assert_finite(result)
        reports.append(copy.deepcopy(result))
    return reports


def run_strategy_matrix(
    engine,
    pack: RuntimePackV1,
    instance_start: int = 1000,
    archetypes: tuple[str, ...] = ARCHETYPES,
    *,
    calibrated: bool = True,
) -> list[dict[str, Any]]:
    """Exercise every declared strategy against every decision archetype.

    This is an evidence-producing playthrough, not a balance gate: the returned
    rows make score curves, rank order, and spread reviewable without asserting
    that one strategy must win.
    """
    strategies = [item.key for item in pack.casepack.strategies]
    execution_pack = _ExecutionPack(pack)
    rows: list[dict[str, Any]] = []
    instance_id = instance_start
    for strategy in strategies:
        for archetype in archetypes:
            plans = calibrated_strategy_plan(archetype, execution_pack, strategy) if calibrated else None
            reports = run_game(
                engine, execution_pack, archetype, strategy, instance_id, 1, plans=plans
            )
            rows.append({
                "strategy": strategy,
                "archetype": archetype,
                "plan_profile": dict(STRATEGY_PLAN_PROFILES[strategy]) if archetype == "balanced" else None,
                "rounds": [
                    {"round": report["round"], "firm_score": report["score"].get("firm_score", 0.0), "scorecard": report.get("scorecard", {})}
                    for report in reports
                ],
            })
            instance_id += 1
    return rows

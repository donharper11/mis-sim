"""Invariant functions for casepack validation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.casepack.models import Casepack


SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ACTION_TYPES = {
    "scale_node",
    "add_node",
    "move_to_cloud",
    "add_training",
    "redesign_process",
    "fund_response",
    "upgrade_component",
    "retire_component",
    "add_service_tier",
    "add_policy",
}

#: The 14 platform stakeholder archetypes. Schema vocabulary, not validator-local state --
#: 1.4 and 1.5 will want it, which is why it lives here beside ACTION_TYPES rather than in
#: validate.py (1.2 spec v1.2 section 3 decision 9).
#: Source: design/05-implementation-plan.md section 1.4.1, which names the platform layer in
#: full, cross-checked against design/01-mis_lite-harvest.md section 2 (`stakeholders`,
#: 14 rows, 7 internal + 7 external). Sourcing verified by the 1.2 audit, finding 1.2-016.
ARCHETYPES = {
    "c_suite",
    "finance",
    "employees",
    "operations",
    "it",
    "hr",
    "marketing",
    "investor",
    "customer",
    "vendor",
    "security_auditor",
    "regulator",
    "general_public",
    "media",
}

#: The seven areas a round's review is broken down by, as `review.lines[].area`.
#: Source: mockups/review.html -- the 0.4 reference mockup's review table declares exactly
#: Platform, Components, Rollout, Services, People, Governance, Challenges. Taken from the
#: mockup rather than from any pack, so no engine constant is derived from pack content.
REVIEW_AREAS = {
    "platform",
    "components",
    "rollout",
    "services",
    "people",
    "governance",
    "challenges",
}


def _walk_keys(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "key" and isinstance(child, str):
                yield child
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def check_snake_case_keys(casepack: Casepack) -> list[str]:
    errors: list[str] = []
    for key in _walk_keys(casepack.model_dump(mode="json")):
        if not SNAKE_RE.fullmatch(key):
            errors.append(key)
    return errors


def check_required_roles_fillable(casepack: Casepack) -> list[str]:
    filled = {role for item in casepack.catalog for role in item.roles_filled}
    filled.update(role for service in casepack.platform.services for role in service.roles_filled)
    missing: list[str] = []
    for capability in casepack.capabilities:
        for role in capability.required_roles:
            if role not in filled:
                missing.append(f"{capability.key}.{role}")
    return missing


def check_strategy_weight_sums(casepack: Casepack) -> list[str]:
    errors: list[str] = []
    for strategy in casepack.strategies:
        total = sum(strategy.capability_weights.values())
        if abs(total - 1.0) > 0.001:
            errors.append(f"{strategy.key}:{total:.3f}")
    return errors


def check_cleared_by_resolves(casepack: Casepack) -> list[str]:
    missing: list[str] = []
    for rule in casepack.watch_rules:
        for action in rule.cleared_by:
            if action not in ACTION_TYPES:
                missing.append(f"{rule.key}.{action}")
    return missing


def check_demand_curve_lengths(casepack: Casepack) -> list[str]:
    errors: list[str] = []
    rounds = casepack.metadata.rounds
    for capability in casepack.capabilities:
        if len(capability.demand_curve) != rounds:
            errors.append(f"{capability.key}:{len(capability.demand_curve)}")
    return errors


def check_yaml_round_trip(casepack: Casepack) -> list[str]:
    dumped = casepack.model_dump(mode="json")
    reparsed = Casepack.model_validate(dumped).model_dump(mode="json")
    return [] if dumped == reparsed else ["casepack"]


def run_all_checks(casepack: Casepack) -> dict[str, list[str]]:
    return {
        "I3": check_snake_case_keys(casepack),
        "I4": check_required_roles_fillable(casepack),
        "I5": check_strategy_weight_sums(casepack),
        "I6": check_cleared_by_resolves(casepack),
        "I7": check_demand_curve_lengths(casepack),
        "I8": check_yaml_round_trip(casepack),
    }

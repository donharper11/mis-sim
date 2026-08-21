"""Invariant functions for casepack validation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Literal, get_args, get_origin

from app.casepack.models import Casepack, EventPrecondition


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

#: The complete event-precondition vocabulary and the exact authored fields each shape
#: accepts. 1.5's event engine consumes this contract, so the validator and engine must
#: import it rather than maintain parallel lists.
PRECONDITION_FIELDS: dict[str, frozenset[str]] = {
    "signal_open": frozenset({"signal", "severity"}),
    "demand_exceeds_capacity": frozenset({"capability", "ratio"}),
    "adoption_below": frozenset({"capability", "ratio"}),
    "staffing_over": frozenset({"ratio"}),
    "debt_above": frozenset({"ratio"}),
    "node_is_spof": frozenset({"node"}),
    "entity_unowned": frozenset({"entity"}),
    "placement_count": frozenset({"placement", "count"}),
    "policy_contradiction": frozenset({"policy", "other_policy"}),
    "sponsor_unassigned": frozenset({"capability"}),
    "round_equals": frozenset({"round"}),
}
PRECONDITION_TYPES = frozenset(PRECONDITION_FIELDS)


def check_precondition_shape(
    type_name: str,
    authored_fields: set[str],
    values: Mapping[str, object],
) -> tuple[bool, frozenset[str], frozenset[str]]:
    """Return (known type, missing fields, extra fields) for one authored condition."""
    required = PRECONDITION_FIELDS.get(type_name)
    if required is None:
        return False, frozenset(), frozenset(authored_fields - {"type"})
    authored = authored_fields - {"type"}
    missing = frozenset(
        field for field in required if field not in authored or values.get(field) is None
    )
    return True, missing, frozenset(authored - required)


def _closed_vocabulary(field_name: str) -> tuple[str, ...]:
    """The exact values `EventPrecondition.<field_name>` accepts, read off the model.

    Read from the annotation rather than restated here on purpose. A closed vocabulary
    copied into a second file is the defect `CONTRACTS.md` (`placement`) and finding
    `1.5-RC-002` are both about, and this vocabulary exists so the validator can give
    that field a diagnostic -- it must not become another home for the values.
    """
    annotation = EventPrecondition.model_fields[field_name].annotation
    values: list[str] = []
    for arg in get_args(annotation):
        if get_origin(arg) is Literal:
            values.extend(str(member) for member in get_args(arg))
    if not values:
        raise RuntimeError(f"EventPrecondition.{field_name} declares no closed vocabulary")
    return tuple(values)


#: Precondition fields whose value vocabulary is CLOSED at the model, so an out-of-vocabulary
#: value makes `models.py` refuse the whole pack before any check can see it. Finding `B7`:
#: that refusal reached the instructor as a bare `E00 "This pack could not be read"` against a
#: file that parsed perfectly, which `GOVERNANCE 4.10` forbids. `validate.py`'s raw-stage
#: `check_precondition_vocab_raw` reads this map and reports `E29` instead.
PRECONDITION_VOCABULARIES: dict[str, tuple[str, ...]] = {
    "placement": _closed_vocabulary("placement"),
    "severity": _closed_vocabulary("severity"),
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

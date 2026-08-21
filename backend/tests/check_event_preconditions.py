#!/usr/bin/env python3
"""Focused readiness checks for EventPrecondition and its closed validator shapes."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.casepack.checks import (  # noqa: E402
    PRECONDITION_FIELDS,
    PRECONDITION_TYPES,
    PRECONDITION_VOCABULARIES,
    check_precondition_shape,
)
from app.casepack.models import EventPrecondition  # noqa: E402
from app.casepack.validate import validate_pack_dir  # noqa: E402

MINIMAL = Path(__file__).resolve().parent / "fixtures/packs/minimal_valid"


VALID = {
    "signal_open": {"signal": "ord_cap_01", "severity": "critical"},
    "demand_exceeds_capacity": {"capability": "order_fulfilment", "ratio": 1.1},
    "adoption_below": {"capability": "order_fulfilment", "ratio": 0.5},
    "staffing_over": {"ratio": 1.2},
    "debt_above": {"ratio": 0.8},
    "node_is_spof": {"node": "kelso_road_link"},
    "entity_unowned": {"entity": "customer"},
    "placement_count": {"placement": "cloud", "count": 2},
    "policy_contradiction": {"policy": "data_retention", "other_policy": "data_access"},
    "sponsor_unassigned": {"capability": "order_fulfilment"},
    "round_equals": {"round": 4},
}

failures: list[str] = []


def require(ok: bool, label: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        failures.append(label)


require(
    PRECONDITION_TYPES == frozenset(VALID),
    "canonical set contains exactly eleven types",
)

for type_name, fields in VALID.items():
    payload = {"type": type_name, **fields}
    condition = EventPrecondition.model_validate(payload)
    dumped = condition.model_dump(exclude_none=True)
    require(dumped == payload, f"{type_name}: model load and round-trip")
    known, missing, extra = check_precondition_shape(
        condition.type, set(condition.model_fields_set), condition.model_dump()
    )
    require(known and not missing and not extra, f"{type_name}: valid exact shape")

    missing_field = sorted(PRECONDITION_FIELDS[type_name])[0]
    missing_payload = {
        key: value for key, value in payload.items() if key != missing_field
    }
    missing_condition = EventPrecondition.model_validate(missing_payload)
    known, missing, extra = check_precondition_shape(
        missing_condition.type,
        set(missing_condition.model_fields_set),
        missing_condition.model_dump(),
    )
    require(
        known and missing == frozenset({missing_field}) and not extra,
        f"{type_name}: missing {missing_field} rejected",
    )

    foreign_field = next(
        field
        for field in sorted(
            set(EventPrecondition.model_fields) - {"type"} - set(fields)
        )
        if field not in PRECONDITION_FIELDS[type_name]
    )
    foreign_value = next(
        values[foreign_field] for values in VALID.values() if foreign_field in values
    )
    extra_payload = {**payload, foreign_field: foreign_value}
    extra_condition = EventPrecondition.model_validate(extra_payload)
    known, missing, extra = check_precondition_shape(
        extra_condition.type,
        set(extra_condition.model_fields_set),
        extra_condition.model_dump(),
    )
    require(
        known and not missing and extra == frozenset({foreign_field}),
        f"{type_name}: foreign field {foreign_field} rejected",
    )

unknown = EventPrecondition.model_validate({"type": "not_a_precondition"})
known, missing, extra = check_precondition_shape(
    unknown.type, set(unknown.model_fields_set), unknown.model_dump()
)
require(not known and not missing, "unknown precondition type rejected")

both = EventPrecondition.model_validate(
    {"type": "placement_count", "placement": "saas", "count": 3}
)
require(
    both.model_dump(exclude_none=True)
    == {"type": "placement_count", "placement": "saas", "count": 3},
    "placement and count survive together",
)
policies = EventPrecondition.model_validate(
    {"type": "policy_contradiction", "policy": "retention", "other_policy": "access"}
)
require(
    policies.model_dump(exclude_none=True)
    == {
        "type": "policy_contradiction",
        "policy": "retention",
        "other_policy": "access",
    },
    "policy and other_policy survive together",
)


# -- B7: an out-of-vocabulary precondition value is a targeted code, never E00 -------------
#
# `placement` and `severity` are Literal fields, so models.py refuses the whole pack before
# any check can look at it. That refusal used to reach the instructor as a bare
# E00 "This pack could not be read" naming no field, for an events.yaml that parsed
# perfectly (GOVERNANCE 4.10). Both directions are asserted here: the targeted code IS
# raised, and E00 is NOT.

require(
    set(PRECONDITION_VOCABULARIES) == {"placement", "severity"},
    "closed precondition vocabularies are placement and severity",
)


def validate_with(replacement: str) -> list:
    """Validate minimal_valid with its first precondition swapped for `replacement`."""
    original = "- {type: signal_open, signal: book_cap_01, severity: critical}"
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp) / "pack"
        shutil.copytree(MINIMAL, pack)
        events = pack / "events.yaml"
        text = events.read_text(encoding="utf-8")
        assert original in text, "minimal_valid's first precondition moved"
        events.write_text(text.replace(original, replacement, 1), encoding="utf-8")
        return validate_pack_dir(pack).findings


for label, replacement, field_name, bad_value in (
    ("placement", "- {type: placement_count, placement: hybrid, count: 2}", "placement", "hybrid"),
    ("severity", "- {type: signal_open, signal: book_cap_01, severity: urgent}", "severity", "urgent"),
):
    found = validate_with(replacement)
    codes = {item.code for item in found}
    require("E00" not in codes, f"out-of-vocabulary {label} does not collapse to E00")
    require(codes == {"E29"}, f"out-of-vocabulary {label} raises E29 and nothing else")
    targeted = [item for item in found if item.code == "E29"]
    require(
        len(targeted) == 1
        and targeted[0].file == "events.yaml"
        and targeted[0].field.endswith(f".{field_name}")
        and bad_value in targeted[0].message
        and field_name in targeted[0].fix,
        f"E29 names events.yaml, the {label} field, and the offending value",
    )

require(
    {item.code for item in validate_pack_dir(MINIMAL).findings} == set(),
    "minimal_valid still validates clean with the raw vocabulary check in place",
)

if failures:
    print(f"\n{len(failures)} focused precondition checks failed")
    raise SystemExit(1)
print("\nAll focused precondition checks passed")

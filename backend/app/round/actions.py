"""Deriving the immutable ``action_history`` from committed decision lines (decision 9/CC-D10).

1.6 emits one ``ActionRecord`` per committed ``decision_line`` whose category performs a
signal-clearing action (spec section 10, compliant route). The engine reads the resulting
``action_history`` on the snapshot to decide which committed action cleared which signal
(``ledger.matching_clear_actions``); it never re-reads the ``decision_line`` table -- that
would put persistence in the pure core (spec section 10, rejected alternative).

``action_type`` comes from the decision line's explicit ``action_type`` when set, else from
the 1:1 category map below. Categories that perform no engine action -- ``staffing``,
``governance``, ``communication``, ``capital_request`` -- map to ``None`` and yield **no**
ActionRecord (they cannot clear a signal). The set is closed to ``checks.ACTION_TYPES``.
"""

from __future__ import annotations

from app.casepack.checks import ACTION_TYPES
from app.engine.state import ActionRecord
from app.round.models import DecisionLineRow

#: The unambiguous 1:1 category -> action_type defaults (CONTRACTS.md decision_line.category ->
#: checks.ACTION_TYPES). Categories mapping to a *family* (application / integration /
#: platform_service / lifecycle) carry NO default here: a decision line that performs a
#: signal-clearing action under one of those categories must name its `action_type` explicitly
#: (add_node vs scale_node vs move_to_cloud etc.), which is the single source of truth for it.
#: Categories that perform no engine action are absent (None) and yield no ActionRecord.
CATEGORY_ACTION_DEFAULTS: dict[str, str] = {
    "training": "add_training",
    "process_redesign": "redesign_process",
    "policy": "add_policy",
    "event_response": "fund_response",
}


def action_type_for(line: DecisionLineRow) -> str | None:
    """The engine action_type this decision line commits, or None if it performs no action."""
    if line.action_type:
        if line.action_type not in ACTION_TYPES:
            raise ValueError(
                f"decision_line {line.key!r} action_type {line.action_type!r} "
                f"is not a checks.ACTION_TYPES key"
            )
        return line.action_type
    return CATEGORY_ACTION_DEFAULTS.get(line.category)


def action_record(line: DecisionLineRow) -> ActionRecord | None:
    """One frozen ActionRecord for a committed line, or None if the line performs no action."""
    action_type = action_type_for(line)
    if action_type is None:
        return None
    return ActionRecord(
        action_type=action_type,
        locked_round=line.round,
        capability=line.capability,
        target_key=line.target_key,
        cost=max(0, int(line.capex)),
    )

#!/usr/bin/env python3
"""Focused W08 checks: pack-relative rounds and unchanged empty-affinity semantics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.casepack.loader import load_casepack  # noqa: E402
from app.casepack.validate import (  # noqa: E402
    Lens,
    PackSource,
    check_strategy_draws,
    check_untargeted_events,
)

ROOT = Path(__file__).resolve().parent / "fixtures" / "packs" / "minimal_valid"
pack = load_casepack(ROOT)
strategy = pack.strategies[0].key
other = pack.strategies[1].key


def with_draws(count: int, *, one_global: bool = False):
    events = []
    for index, event in enumerate(pack.events):
        affinity = [strategy] if index < count else [other]
        if one_global and index == count:
            affinity = []
        events.append(event.model_copy(update={"strategy_affinity": affinity}))
    return pack.model_copy(update={"events": events})


def codes(candidate) -> list[str]:
    return [
        item.code for item in check_strategy_draws(Lens(candidate, PackSource(ROOT)))
    ]


four = with_draws(4)
target_four = [
    item
    for item in check_strategy_draws(Lens(four, PackSource(ROOT)))
    if strategy in item.field
]
assert (
    not target_four
), "a four-round pack with four draws must not warn for that strategy"
print("PASS  four-round pack with four draws passes W08")

three = with_draws(3)
target_three = [
    item
    for item in check_strategy_draws(Lens(three, PackSource(ROOT)))
    if strategy in item.field
]
assert len(target_three) == 1 and target_three[0].code == "W08"
assert "at least 4" in target_three[0].message
print("PASS  four-round pack with three draws warns W08 with minimum 4")

global_fourth = with_draws(3, one_global=True)
target_global = [
    item
    for item in check_strategy_draws(Lens(global_fourth, PackSource(ROOT)))
    if strategy in item.field
]
assert not target_global, "empty affinity must count as a draw for every strategy"
global_w03 = check_untargeted_events(Lens(global_fourth, PackSource(ROOT)))
assert any(item.code == "W03" for item in global_w03)
print("PASS  empty affinity counts for W08 and still emits W03")

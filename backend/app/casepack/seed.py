"""Seed command for loading a packaged casepack from disk."""

from __future__ import annotations

import sys
from pathlib import Path

from app.casepack.checks import run_all_checks
from app.casepack.loader import load_casepack


def _pack_root(pack_key: str) -> Path:
    return Path(__file__).resolve().parents[2] / "packs" / pack_key


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: python -m app.casepack.seed pack_key")
        return 2
    casepack = load_casepack(_pack_root(args[0]))
    checks = run_all_checks(casepack)
    failed = {key: value for key, value in checks.items() if value}
    if failed:
        print(f"checks failed: {failed}")
        return 1
    state = casepack.metadata.initial_state
    print(
        f"{len(casepack.capabilities)} capabilities, "
        f"{len(casepack.catalog)} catalog items, "
        f"{len(casepack.strategies)} strategies"
    )
    for strategy in casepack.strategies:
        print(f"{strategy.key} weights sum {sum(strategy.capability_weights.values()):.3f}")
    print(
        "pinned figures: "
        f"round {state.round}; "
        f"capital {state.budget.capital_remaining} of {state.budget.capital_available}; "
        f"run_rate {state.budget.run_rate}; "
        f"scorecard {state.scorecard.financial}/"
        f"{state.scorecard.customer}/"
        f"{state.scorecard.internal_process}/"
        f"{state.scorecard.learning_growth}; "
        f"signals {state.open_signals}; "
        f"inbox {state.inbox_waiting}; "
        f"staff {state.people.staff_fte}; "
        f"load {state.people.load_fte}; "
        f"over {state.people.overcommitted_pct}; "
        f"review_capital {state.review.capital_committed} of {state.review.capital_available}; "
        # Derived, not authored -- the review block no longer carries this figure (CG-6).
        f"remaining {state.review.capital_available - state.review.capital_committed}; "
        f"run_rate_after {state.review.run_rate_after}; "
        f"run_rate_before {state.review.run_rate_before}"
    )
    for unit in state.unit_responses:
        print(f"{unit.unit} people {unit.people} contribution {unit.contribution_pct}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build persona grounding blocks from team checkpoint state.

The adapter extracts a compact, scoped fact set from the team's current
state.  Facts are read-only projections: no secrets, no cross-team data,
no credentials.  The block is digest-bound so downstream guards can verify
that the provider response quotes only the injected figures.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .contracts import GroundingBlockV1, GroundingFactV1


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON for digest computation."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_persona_grounding(
    *,
    instance_id: int,
    team_id: int,
    current_round: int,
    state: Mapping[str, Any],
    result_payload: Mapping[str, Any] | None,
    strategy_labels: Mapping[str, str] | None = None,
) -> GroundingBlockV1:
    """Build a grounding block from the team's checkpoint state.

    The fact set is intentionally small and contains only figures that a
    persona may legitimately quote in conversation.  Every numeric value
    visible in the response must come from this block — the grounding
    guard rejects anything else.
    """
    facts: list[GroundingFactV1] = []

    # Round number
    facts.append(GroundingFactV1(
        key="round",
        display_value=f"Round {current_round}",
        numeric_value=current_round,
        source_path="/state/round",
        round=current_round,
    ))

    # Capital balance
    capital = state.get("capital_balance")
    if capital is not None:
        display = f"${capital:,.0f}" if isinstance(capital, (int, float)) else str(capital)
        facts.append(GroundingFactV1(
            key="capital_balance",
            display_value=display,
            numeric_value=capital if isinstance(capital, (int, float)) else None,
            unit="usd",
            source_path="/state/capital_balance",
            round=current_round,
        ))

    # Declared strategy (display value only, no numeric).
    # Resolve the machine key to its label so students never see snake_case.
    strategy = state.get("strategy")
    if strategy and isinstance(strategy, str):
        if strategy_labels and strategy in strategy_labels:
            display_strategy = strategy_labels[strategy]
        else:
            display_strategy = strategy.replace("_", " ").title()
        facts.append(GroundingFactV1(
            key="strategy",
            display_value=display_strategy,
            source_path="/state/strategy",
            round=current_round,
        ))

    # Scorecard dimensions from result payload
    if result_payload:
        for dimension in ("financial", "customer", "internal_process", "learning_growth"):
            key = f"scorecard_{dimension}"
            value = result_payload.get("scorecard", {}).get(dimension)
            if value is not None and isinstance(value, (int, float)):
                facts.append(GroundingFactV1(
                    key=key,
                    display_value=f"{value:.2f}" if isinstance(value, float) else str(value),
                    numeric_value=value,
                    source_path=f"/result/scorecard/{dimension}",
                    round=current_round,
                ))

        # Run rate from result financials
        run_rate = result_payload.get("run_rate")
        if run_rate is not None and isinstance(run_rate, (int, float)):
            facts.append(GroundingFactV1(
                key="run_rate",
                display_value=f"${run_rate:,.0f}",
                numeric_value=run_rate,
                unit="usd",
                source_path="/result/run_rate",
                round=current_round,
            ))

    # Open signal count
    open_signals = state.get("open_signals")
    if open_signals is not None and isinstance(open_signals, int):
        facts.append(GroundingFactV1(
            key="open_signals",
            display_value=str(open_signals),
            numeric_value=open_signals,
            source_path="/state/open_signals",
            round=current_round,
        ))

    # Build the state payload for digest computation — scoped, no secrets
    digest_payload = _canonical_json({
        "instance_id": instance_id,
        "team_id": team_id,
        "round": current_round,
        "facts": [f.key for f in facts],
    })

    return GroundingBlockV1.from_digest(
        instance_id=instance_id,
        team_id=team_id,
        round=current_round,
        state=digest_payload,
        facts=facts,
    )

"""Governance-safe rationale review seam.

Challenge notes are useful for teaching, but the simulation engine must remain the
authority for every scored number. This module validates an optional evaluator's
bounded metadata and provides a neutral disabled fallback. It deliberately contains
no network client and no score mutation; an approved provider can be injected by an
application layer later.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from .types import RationaleReviewV1


class RationaleEvaluator(Protocol):
    def evaluate(
        self,
        *,
        note: str,
        event: str,
        option: str,
        rationale_tag: str,
        option_tags: Sequence[str],
    ) -> Mapping[str, Any]: ...


def review_rationale(
    *,
    note: str | None,
    event: str,
    option: str,
    rationale_tag: str,
    option_tags: Sequence[str],
    evaluator: RationaleEvaluator | None = None,
) -> RationaleReviewV1:
    """Return a bounded review while preserving neutral behavior by default.

    Provider errors, malformed output, and an absent provider are all explicit in
    the returned status and leave ``modifier == 1.0``. The engine never consumes the
    modifier; callers may display it to an instructor or route it through a separately
    approved grading surface.
    """
    if evaluator is None:
        return RationaleReviewV1(
            status="not_scored", quality=None, modifier=1.0,
            provider="disabled", reason="LLM rationale scoring is disabled by governance",
        )
    if not note or not note.strip():
        return RationaleReviewV1(
            status="unavailable", quality=None, modifier=1.0,
            provider="fallback", reason="no rationale note supplied",
        )
    try:
        raw = evaluator.evaluate(
            note=note, event=event, option=option,
            rationale_tag=rationale_tag, option_tags=option_tags,
        )
        if not isinstance(raw, Mapping):
            raise ValueError("evaluator output must be an object")
        payload = dict(raw)
        payload.setdefault("status", "scored")
        payload.setdefault("provider", evaluator.__class__.__name__)
        return RationaleReviewV1.model_validate(payload)
    except Exception as exc:  # provider failures must never block round progression
        return RationaleReviewV1(
            status="unavailable", quality=None, modifier=1.0,
            provider="fallback", reason=f"evaluator unavailable: {type(exc).__name__}",
        )

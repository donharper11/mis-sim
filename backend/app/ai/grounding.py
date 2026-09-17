"""Numeric grounding guard for provider output."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .contracts import GroundingBlockV1


class GroundingViolation(ValueError):
    """Raised when provider text contains a number absent from current state."""


_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?P<currency>[$€£¥])?"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)"
    r"(?P<percent>%)?(?![A-Za-z0-9_])"
)


def _decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def _number_candidates(text: str) -> list[tuple[Decimal, bool]]:
    values: list[tuple[Decimal, bool]] = []
    for match in _NUMBER_RE.finditer(text):
        try:
            values.append((_decimal(match.group("number")), bool(match.group("percent"))))
        except InvalidOperation:
            # The regex is deliberately narrow; this is defensive for future edits.
            continue
    return values


def _allowed_numbers(grounding: GroundingBlockV1) -> set[Decimal]:
    allowed: set[Decimal] = set()
    for fact in grounding.facts:
        if fact.numeric_value is not None:
            value = Decimal(str(fact.numeric_value))
            allowed.add(value)
        # display_value is the only human-readable value the provider may quote.
        # Include its numeric form when it is explicitly part of the fact.
        for value, is_percent in _number_candidates(fact.display_value):
            allowed.add(value / Decimal("100") if is_percent else value)
    return allowed


def validate_grounded_text(text: str, grounding: GroundingBlockV1 | None) -> str:
    """Reject numeric claims absent from the injected grounding block.

    A response without grounding is allowed only when it contains no numeric
    figure.  The function returns the original text so callers can retain the
    provider's wording after the guard passes.
    """
    numbers = _number_candidates(text)
    if not numbers:
        return text
    if grounding is None:
        raise GroundingViolation("numeric_claim_without_grounding")
    allowed = _allowed_numbers(grounding)
    for value, is_percent in numbers:
        normalized = value / Decimal("100") if is_percent else value
        if normalized not in allowed:
            raise GroundingViolation("ungrounded_numeric_claim")
    return text


# A descriptive alias helps callers make the governance intent obvious.
guard_grounded_text = validate_grounded_text

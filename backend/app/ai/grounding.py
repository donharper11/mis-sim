"""Numeric grounding guard for provider output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .contracts import GroundingBlockV1


class GroundingViolation(ValueError):
    """Raised when provider text contains a number absent from current state."""


_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?P<sign>[+-])?(?P<currency>[$€£¥])?"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)"
    r"(?P<percent>%)?(?![A-Za-z0-9_])"
)


@dataclass(frozen=True)
class _NumericToken:
    """The exact numeric representation visible to the model."""

    sign: str
    currency: str
    number: str
    percent: bool

    @property
    def decimal(self) -> Decimal:
        value = Decimal(self.number.replace(",", ""))
        return -value if self.sign == "-" else value


def _number_candidates(text: str) -> list[_NumericToken]:
    values: list[_NumericToken] = []
    for match in _NUMBER_RE.finditer(text):
        try:
            token = _NumericToken(
                sign=match.group("sign") or "",
                currency=match.group("currency") or "",
                number=match.group("number"),
                percent=bool(match.group("percent")),
            )
            # Validate the captured representation once, while retaining its
            # exact sign/currency/format for the grounding comparison below.
            token.decimal
            values.append(token)
        except InvalidOperation:
            # The regex is deliberately narrow; this is defensive for future edits.
            continue
    return values


def _allowed_numbers(grounding: GroundingBlockV1) -> set[_NumericToken]:
    allowed: set[_NumericToken] = set()
    for fact in grounding.facts:
        # display_value is the only human-readable value the provider may quote.
        # numeric_value is deliberately *not* an authorization source: it is
        # semantic metadata for adapters and cannot authorize a different
        # representation than the authored display value.
        allowed.update(_number_candidates(fact.display_value))
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
    for token in numbers:
        if token not in allowed:
            raise GroundingViolation("ungrounded_numeric_claim")
    return text


# A descriptive alias helps callers make the governance intent obvious.
guard_grounded_text = validate_grounded_text

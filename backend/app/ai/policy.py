"""Small deterministic policy guard for untrusted provider output."""

from __future__ import annotations

import re


class PolicyViolation(ValueError):
    """Raised when generated teaching content crosses the advisor boundary."""


# The guard is intentionally conservative.  The coach/persona may explain an
# authored opinion or an already-computed result, but it may not decide for the
# student or evaluate the student's plan.
_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("decision_recommendation", re.compile(r"\b(?:you should|you ought to|i recommend|my recommendation)\b", re.I)),
    ("plan_evaluation", re.compile(r"\b(?:your plan|your architecture|this plan)\s+(?:is|looks)\s+(?:good|bad|best|better|worse|optimal|wrong)\b", re.I)),
    ("purchase_instruction", re.compile(r"\b(?:buy|purchase|choose|select|pick)\s+(?:the|a|an|cloud|on[- ]prem|saas)\b", re.I)),
    ("architecture_recommendation", re.compile(r"\b(?:go|move|switch)\s+(?:to|with)\s+(?:the\s+)?cloud\b", re.I)),
    ("ranking_or_score", re.compile(r"\b(?:score|ranking|rank|winner|highest|lowest)\b", re.I)),
)


def validate_teaching_output(text: str) -> str:
    """Return text when it stays in the teaching boundary, else raise safely."""
    if not isinstance(text, str) or not text.strip():
        raise PolicyViolation("empty_output")
    for reason, pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(text):
            raise PolicyViolation(reason)
    return text


def policy_violation_reason(text: str) -> str | None:
    try:
        validate_teaching_output(text)
    except PolicyViolation as exc:
        return str(exc)
    return None

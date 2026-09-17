"""Small deterministic policy guard for untrusted provider output."""

from __future__ import annotations

import re


class PolicyViolation(ValueError):
    """Raised when generated teaching content crosses the advisor boundary."""


# The guard is intentionally conservative.  The coach/persona may explain an
# authored opinion or an already-computed result, but it may not decide for the
# student or evaluate the student's plan.
_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("decision_recommendation", re.compile(
        r"\b(?:you\s+should|you\s+ought\s+to|i\s+recommend|i['’]d\s+recommend|"
        r"my\s+recommendation|i\s+suggest|we\s+suggest|i\s+would\s+go|"
        r"what\s+(?:do\s+you\s+)?recommend)\b|"
        r"\brecommendation\s*:", re.I
    )),
    ("plan_evaluation", re.compile(
        r"\b(?:your|my|our|this|the)\s+(?:plan|architecture|design|strategy|approach)\s+"
        r"(?:is|looks|seems)\s+(?:good|bad|best|better|worse|optimal|wrong|right|sound|viable|"
        r"flawed|weak|risky|appropriate|inappropriate)\b|"
        r"\b(?:is|was)\s+(?:my|our|this|the)\s+(?:plan|architecture|design|strategy|approach)\s+"
        r"(?:good|bad|best|better|worse|optimal|wrong|right|sound|viable|flawed|weak|risky)\b|"
        r"\b(?:the\s+)?best\s+(?:plan|architecture|design|strategy|approach|option|choice)\s+"
        r"(?:is|would\s+be)\b|"
        r"\b(?:what|which)\s+is\s+(?:the\s+)?best\s+(?:plan|architecture|design|strategy|approach|option|choice)\b|"
        r"\b(?:cloud|on[- ]prem(?:ises)?|saas)\s+(?:is|would\s+be)\s+(?:the\s+)?best\b|"
        r"\b(?:is|was)\s+(?:this|that|it)\s+(?:a\s+)?(?:good|bad|best|better|worse|optimal|right|wrong)\b|"
        r"\b(?:your|my|this)\s+(?:plan|architecture|design|strategy|approach)\s+(?:is|looks|seems)\b", re.I
    )),
    ("purchase_instruction", re.compile(
        r"\b(?:what\s+should\s+(?:i|we)\s+|should\s+(?:i|we)\s+|"
        r"what\s+should\s+(?:i|we)\s+do\b|"
        r"(?:buy|purchase|choose|select|pick|use|adopt)\s+(?:the|a|an|cloud|on[- ]prem|saas)\b)"
        r"(?:buy|purchase|choose|select|pick|use|adopt|go)?\b|"
        r"\b(?:should|ought)\s+(?:i|we)\s+(?:use|choose|select|pick|go|move|switch|buy|purchase)\b", re.I
    )),
    ("architecture_recommendation", re.compile(
        r"\b(?:go|move|switch)\s+(?:to|with)\s+(?:the\s+)?cloud\b|"
        r"\b(?:migrate|move|switch)\s+to\s+(?:the\s+)?cloud\b|"
        r"\b(?:i|we)\s+(?:would|will)\s+(?:choose|use|pick|select)\s+(?:the\s+)?cloud\b|"
        r"\b(?:i|we)\s+would\s+(?:go|move|switch)\s+(?:to|with)\s+(?:the\s+)?cloud\b|"
        r"\bwhich\s+(?:architecture|plan|strategy|option|solution)\s+(?:wins?|is\s+best)\b|"
        r"\b(?:what|which)\s+(?:architecture|plan|strategy|option|solution)\s+should\b", re.I
    )),
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

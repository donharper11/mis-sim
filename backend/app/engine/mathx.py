"""Pure numeric helpers for the scoring engine.

No I/O, no clock, no randomness. Every function here is a total function of its
arguments (invariant I2).
"""

from __future__ import annotations

from collections.abc import Sequence


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp `value` into the closed interval [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def geomean(values: Sequence[float]) -> float:
    """Weighted-equal geometric mean of a sequence in [0, 1].

    Settled decision 2: the *within-term* aggregation is the geometric mean, so a
    single crushed sub-factor pulls the term down without five multiplied factors
    collapsing to an unreadable value. A zero anywhere returns zero (invariant I7
    at the sub-factor level): the geometric mean of a set containing 0 is 0.

    O1 default: sub-factor weights are equal and hard-coded for v1.
    """
    if not values:
        raise ValueError("geomean of an empty sequence is undefined")
    product = 1.0
    for v in values:
        if v < 0.0:
            raise ValueError("geomean is defined here only on non-negative values")
        if v == 0.0:
            return 0.0
        product *= v
    return product ** (1.0 / len(values))


def round6(value: float) -> float:
    """Deterministic rounding for reported figures (determinism, invariant I5)."""
    return round(value, 6)

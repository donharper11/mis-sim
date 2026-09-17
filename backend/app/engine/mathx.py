"""Pure numeric helpers for the scoring engine.

No I/O, no clock, no randomness. Every function here is a total function of its
arguments (invariant I2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp `value` into the closed interval [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def geomean(values: Sequence[float]) -> float:
    """Equal geometric mean helper for rollups that still require a hard zero."""
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


def weighted_mean(values: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """Return a bounded weighted arithmetic mean for named score factors.

    The scoring terms use this for partial evidence: one missing factor lowers a
    term in proportion to its authored weight instead of collapsing the whole term.
    Structural blockers are handled by the caller before invoking this helper.
    """
    if not values:
        raise ValueError("weighted mean of an empty mapping is undefined")
    if set(values) != set(weights):
        raise ValueError("weighted mean values and weights must have identical keys")
    total = 0.0
    weight_total = 0.0
    for key, value in values.items():
        weight = weights[key]
        if value < 0.0 or value > 1.0:
            raise ValueError("weighted mean values must be in [0, 1]")
        if weight < 0.0:
            raise ValueError("weighted mean weights must be non-negative")
        total += value * weight
        weight_total += weight
    if weight_total <= 0.0:
        raise ValueError("weighted mean requires positive total weight")
    return total / weight_total


def round6(value: float) -> float:
    """Deterministic rounding for reported figures (determinism, invariant I5)."""
    return round(value, 6)

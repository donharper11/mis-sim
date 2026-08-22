"""I10 -- the frozen 1.4 pin survives the six-round seed (1.6 spec section 6, decision 12).

Two things are proven here, both plant-falsifiable (SPEC_PROTOCOL 4.3):

1. **Hermetic pin.** Scoring the riverside_r3 snapshot reproduces the frozen pin byte-for-byte
   (tech 0.750008 / org 0.507003 / mgmt 0.656778 / realised 0.249744). 1.6 touches no engine or
   scoring code, so `--full` leaves this untouched (also guarded by test_engine_scoring.py).

2. **The projection seam preserves the pin.** The R1-R3 signal-ledger history projects (via
   `project_signal_state`) to exactly the three SignalState rows the pin depends on, and scoring
   the snapshot with those PROJECTED signals still yields the pin. The projection is driven by the
   round-evolution inputs 1.6 produces (`action_history` sets `cleared_round`; `available_funds_by
   _round` sets `was_actionable`). Planting either input so the R3 projection changes drifts the
   pin -- the falsification the spec's I10 names.
"""

from __future__ import annotations

from dataclasses import replace

from app.engine.ledger import project_signal_state
from app.engine.score import score_team
from app.seed.demo import load_scenario

import seeds.riverside_signals as sig

TOL = 1e-6


def _order_fulfilment(pack, state):
    return next(c for c in score_team(pack, state).capabilities if c.capability == "order_fulfilment")


def test_i10_pin_hermetic():
    pack, state = load_scenario("riverside_r3")
    of = _order_fulfilment(pack, state)
    assert abs(of.terms["tech"] - 0.750008) <= TOL, of.terms
    assert abs(of.terms["org"] - 0.507003) <= TOL, of.terms
    assert abs(of.terms["mgmt"] - 0.656778) <= TOL, of.terms
    assert abs(of.realised - 0.249744) <= TOL, of.realised
    assert of.throttle == "org"


def test_i10_projection_seam_preserves_pin():
    pack, state = load_scenario("riverside_r3")
    projected = project_signal_state(sig.signal_history())
    # the projection reproduces the three SignalState rows the pin depends on (CC4 seam)
    assert projected == state.signals
    # scoring with the PROJECTED signals (not the hand-built ones) still yields the pin
    of = _order_fulfilment(pack, replace(state, signals=projected))
    assert abs(of.terms["mgmt"] - 0.656778) <= TOL, of.terms
    assert abs(of.realised - 0.249744) <= TOL, of.realised


def test_i10_plant_missing_clear_action_drifts_pin():
    """`ord_cap_01.cleared_round` is set by the scale_node in `action_history`
    (ledger.matching_clear_actions). Planting a history WITHOUT that clear (as if the action was
    never committed) flips ord_cap to un-credited -> responsiveness 1/3 -> 0/3 -> the pin drifts."""
    pack, state = load_scenario("riverside_r3")
    planted = tuple(
        replace(s, status="open", cleared_round=None, cleared_by=()) if s.key == "ord_cap_01" else s
        for s in sig.signal_history()
    )
    of = _order_fulfilment(pack, replace(state, signals=project_signal_state(planted)))
    assert abs(of.terms["mgmt"] - 0.656778) > TOL, "planted missing clear must drift the pin"
    assert abs(of.realised - 0.249744) > TOL


def test_i10_plant_unaffordable_drifts_pin():
    """`ord_cap_01.was_actionable` is set by `available_funds_by_round` (ledger.was_actionable).
    Planting funds below the fix (was_actionable False) excludes ord_cap from the responsiveness
    denominator, changing the score -> the pin drifts."""
    pack, state = load_scenario("riverside_r3")
    planted = tuple(
        replace(s, was_actionable=False) if s.key == "ord_cap_01" else s
        for s in sig.signal_history()
    )
    of = _order_fulfilment(pack, replace(state, signals=project_signal_state(planted)))
    assert abs(of.terms["mgmt"] - 0.656778) > TOL, "planted unaffordable ord_cap must drift the pin"

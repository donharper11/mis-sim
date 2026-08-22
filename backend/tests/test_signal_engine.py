"""Falsifiable tests for the 1.5 event & signal engine (contract-spec section 11, CC1-CC14).

Every metric, ledger rule, precondition boundary, event-firing rule, and the blast-radius /
duration path has a row here that asserts the frozen behaviour -- and would FAIL on the planted
defect the contract-spec names. The 1.4 pin (CC9) and the purity grep (CC8) live in
test_engine_scoring.py and check_engine_purity.py respectively.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.casepack.models import Event, EventPrecondition, PolicyOption, WatchRule
from app.engine import events as ev
from app.engine import ledger as lg
from app.engine import metrics as mx
from app.engine import preconditions as pc
from app.engine.ledger import LedgerSignal
from app.engine.state import (
    ActionRecord, ArchEdge, ArchNode, GovernanceState, SignalState, StaffPool, TeamState,
)
from app.seed.demo import load_scenario

import seeds.riverside_signals as sig


@pytest.fixture(scope="module")
def pack_state():
    return load_scenario("riverside_r3")


def _rule(pack, key):
    return next(r for r in pack.watch_rules if r.key == key)


def _bare_state(**kw):
    base = dict(
        round=3, declared_strategy="cost_leadership", nodes=(), edges=(), deployments=(),
        org_units=(), governance=(), staff=StaffPool(2.0, 3.4), signals=(), decisions=(),
    )
    base.update(kw)
    return TeamState(**base)


# -- CC1: unknown metric key raises, never returns false ---------------------------------

def test_cc1_unknown_metric_raises(pack_state):
    pack, state = pack_state
    bad = WatchRule(
        key="x", capability="order_fulfilment", metric="not_a_metric", metric_kind="threshold",
        warn_above=0.1, critical_above=0.2, cleared_by=[],
        provenance={"source": "AUTHORED", "note": "n"},
    )
    with pytest.raises(mx.UnknownMetricError):
        mx.metric_value(bad, state, pack)


# -- CC2: threshold comparison is strict > -----------------------------------------------

def test_cc2_threshold_strict_greater(pack_state):
    pack, state = pack_state
    rule = _rule(pack, "ord_cap_01")
    value = mx.capacity_utilisation(state, pack, rule)  # 1.6609
    at = rule.model_copy(update={"warn_above": value / 2, "critical_above": value})  # value == critical_above
    assert lg.evaluate(at, state, pack) == ("warning", value)  # exactly-at does NOT raise critical
    over = rule.model_copy(update={"warn_above": 0.1, "critical_above": value - 0.0001})
    assert lg.evaluate(over, state, pack)[0] == "critical"


# -- CC3: no serving path returns 0.0, no ZeroDivisionError ------------------------------

def test_cc3_no_path_returns_zero(pack_state):
    pack, _ = pack_state
    empty = _bare_state(nodes=(), edges=())
    for key in ("ord_cap_01", "fin_close_01", "cust_data_01"):
        rule = _rule(pack, key)
        assert mx.metric_value(rule, empty, pack) == 0.0  # no exception


# -- CC4: projection reproduces the seed rows AND credits clear-before-fire --------------

def test_cc4_projection_reproduces_seed_rows(pack_state):
    _, state = pack_state
    projected = lg.project_signal_state(sig.signal_history())
    assert projected == state.signals


def test_cc4_clear_before_fire_is_credited():
    ledger = (LedgerSignal(
        key="k", episode_id=1, capability="c", metric="m", metric_kind="threshold", value=1.0,
        severity="critical", status="cleared", first_shown_round=2, cleared_round=3,
        fire_round=None, was_actionable=True,
    ),)
    row = lg.project_signal_state(ledger)[0]
    assert row.acted_before_fire is True  # fire_round None (prevented) is the most responsive


# -- CC5: recurrence opens a new episode; history is never overwritten -------------------

def test_cc5_recurrence_opens_new_episode(pack_state):
    pack, state = pack_state
    rule = _rule(pack, "ord_cap_01")
    prior_row = LedgerSignal(
        key="ord_cap_01", episode_id=1, capability="order_fulfilment",
        metric="capacity_utilisation", metric_kind="threshold", value=1.66,
        severity="critical", status="cleared", first_shown_round=1, cleared_round=2,
        fire_round=None, was_actionable=True,
    )
    new = lg.advance_ledger((prior_row,), state, pack)
    ep1 = [s for s in new if s.key == "ord_cap_01" and s.episode_id == 1]
    ep2 = [s for s in new if s.key == "ord_cap_01" and s.episode_id == 2]
    assert ep1 == [prior_row]  # byte-identical, never overwritten
    assert len(ep2) == 1 and ep2[0].first_shown_round == 3 and ep2[0].status == "open"


# -- CC6: lifecycle status ordering (no de-escalation; clear-after-fire stays fired) -----

def test_cc6_no_de_escalation(pack_state):
    pack, state = pack_state
    # At round 1 the order system sits at 6000/7225 = 0.83 -> ord_cap_01 evaluates WARNING; carry
    # a critical open episode into that round. Severity is a floor and must never fall back to
    # warning (no de-escalation, contract-spec section 5.2).
    warn_state = replace(state, round=1)
    assert lg.evaluate(_rule(pack, "ord_cap_01"), warn_state, pack)[0] == "warning"
    open_crit = LedgerSignal(
        key="ord_cap_01", episode_id=1, capability="order_fulfilment",
        metric="capacity_utilisation", metric_kind="threshold", value=1.66,
        severity="critical", status="open", first_shown_round=1, was_actionable=True,
    )
    out = next(s for s in lg.advance_ledger((open_crit,), warn_state, pack) if s.key == "ord_cap_01")
    assert out.severity == "critical"


def test_cc6_clear_after_fire_stays_fired():
    assert lg.compute_status(cleared_round=4, fire_round=3, still_raises=False) == "fired"
    assert lg.compute_status(cleared_round=3, fire_round=3, still_raises=False) == "cleared"
    assert lg.compute_status(cleared_round=None, fire_round=None, still_raises=True) == "open"
    # a clear after fire projects to no credit
    row = lg.project_signal_state((LedgerSignal(
        key="k", episode_id=1, capability="c", metric="m", metric_kind="presence", value=1.0,
        severity="critical", status="fired", first_shown_round=1, cleared_round=4, fire_round=3,
        was_actionable=True,
    ),))[0]
    assert row.acted_before_fire is False


# -- CC7: action-target matching + effectful price selection -----------------------------

def test_cc7_training_none_excluded(pack_state):
    pack, _ = pack_state
    from types import SimpleNamespace
    # a rule cleared only by add_training, with a capability whose only training option is the
    # zero-coverage `none`: cheapest fix must be None, not 0 (the effectfulness filter fires).
    item = SimpleNamespace(
        serves=("synthetic_cap",),
        training_options={"none": SimpleNamespace(cost=0, coverage=0.0)},
    )
    rule = WatchRule(
        key="r", capability="synthetic_cap", metric="rollout_without_support",
        metric_kind="presence", cleared_by=["add_training"],
        provenance={"source": "AUTHORED", "note": "n"},
    )
    fake = SimpleNamespace(catalog=[item])
    assert lg.cheapest_effectful_fix(rule, fake) is None
    # add one effectful option (coverage > 0) and the fix appears at that cost
    item.training_options["basic"] = SimpleNamespace(cost=5000, coverage=0.6)
    assert lg.cheapest_effectful_fix(rule, fake) == 5000


def test_cc7_wrong_capability_does_not_clear(pack_state):
    pack, state = pack_state
    rule = _rule(pack, "ord_cap_01")  # capability order_fulfilment, cleared_by scale_node
    wrong = replace(state, action_history=(
        ActionRecord("scale_node", locked_round=3, capability="store_operations", cost=1000),
    ))
    cleared_round, cleared_by = lg.matching_clear_actions(
        rule, "order_fulfilment", wrong, 2, 3, pack
    )
    assert cleared_round is None and cleared_by == ()
    right = replace(state, action_history=(
        ActionRecord("scale_node", locked_round=3, capability="order_fulfilment", cost=1000),
    ))
    cleared_round, cleared_by = lg.matching_clear_actions(
        rule, "order_fulfilment", right, 2, 3, pack
    )
    assert cleared_round == 3 and cleared_by == ("scale_node",)


# -- CC10: eleven precondition boundaries (positive + negative + boundary) ----------------

def _pcond(**kw):
    return EventPrecondition.model_validate(kw)


def test_cc10_signal_open_severity_floor(pack_state):
    pack, state = pack_state
    ledger = (LedgerSignal(
        key="ord_cap_01", episode_id=1, capability="order_fulfilment", metric="m",
        metric_kind="threshold", value=1.0, severity="critical", status="open",
        first_shown_round=1,
    ),)
    assert pc.evaluate_precondition(_pcond(type="signal_open", signal="ord_cap_01", severity="warning"), state, pack, ledger) is True
    assert pc.evaluate_precondition(_pcond(type="signal_open", signal="ord_cap_01", severity="critical"), state, pack, ledger) is True
    assert pc.evaluate_precondition(_pcond(type="signal_open", signal="none", severity="warning"), state, pack, ledger) is False


def test_cc10_demand_exceeds_capacity_strict(pack_state):
    pack, state = pack_state
    util = mx.capacity_utilisation(state, pack, _rule(pack, "ord_cap_01"))  # 1.6609
    p = lambda ratio: _pcond(type="demand_exceeds_capacity", capability="order_fulfilment", ratio=ratio)
    assert pc.evaluate_precondition(p(util), state, pack) is False   # boundary: not strictly >
    assert pc.evaluate_precondition(p(util - 0.1), state, pack) is True
    assert pc.evaluate_precondition(p(util + 0.1), state, pack) is False


def test_cc10_adoption_below_strict(pack_state):
    pack, state = pack_state
    adoption = state.primary_deployment("order_fulfilment").adoption  # 0.61
    p = lambda ratio: _pcond(type="adoption_below", capability="order_fulfilment", ratio=ratio)
    assert pc.evaluate_precondition(p(adoption), state, pack) is False  # boundary strict <
    assert pc.evaluate_precondition(p(adoption + 0.1), state, pack) is True
    no_dep = replace(state, deployments=())
    assert pc.evaluate_precondition(p(0.9), no_dep, pack) is False


def test_cc10_staffing_over(pack_state):
    pack, state = pack_state  # load 3.4 / staff 2.0 = 1.7
    p = lambda ratio: _pcond(type="staffing_over", ratio=ratio)
    assert pc.evaluate_precondition(p(1.7), state, pack) is False  # boundary strict >
    assert pc.evaluate_precondition(p(1.5), state, pack) is True
    zero = replace(state, staff=StaffPool(0.0, 3.4))
    assert pc.evaluate_precondition(p(99.0), zero, pack) is True   # zero capacity is over


def test_cc10_debt_above(pack_state):
    pack, state = pack_state
    p = _pcond(type="debt_above", capability="order_fulfilment", ratio=0.8)
    with pytest.raises(pc.MissingRoundInputError):
        pc.evaluate_precondition(p, state, pack)  # absent input raises, never silent FALSE
    with_debt = replace(state, debt_ratio_by_capability={"order_fulfilment": 0.8})
    assert pc.evaluate_precondition(p, with_debt, pack) is False  # boundary strict >
    with_debt2 = replace(state, debt_ratio_by_capability={"order_fulfilment": 0.9})
    assert pc.evaluate_precondition(p, with_debt2, pack) is True


def test_cc10_node_is_spof(pack_state):
    pack, state = pack_state
    assert pc.evaluate_precondition(_pcond(type="node_is_spof", node="wan_link"), state, pack) is True
    assert pc.evaluate_precondition(_pcond(type="node_is_spof", node="store_pc"), state, pack) is False
    assert pc.evaluate_precondition(_pcond(type="node_is_spof", node="nope"), state, pack) is False


def test_cc10_entity_unowned(pack_state):
    pack, state = pack_state
    assert pc.evaluate_precondition(_pcond(type="entity_unowned", entity="order"), state, pack) is False
    assert pc.evaluate_precondition(_pcond(type="entity_unowned", entity="ghost"), state, pack) is True


def test_cc10_placement_count(pack_state):
    pack, state = pack_state
    with pytest.raises(pc.MissingRoundInputError):
        pc.evaluate_precondition(_pcond(type="placement_count", placement="cloud", count=1), state, pack)
    placed = replace(state, nodes=tuple(
        replace(n, placement="cloud") if i < 2 else n for i, n in enumerate(state.nodes)
    ))
    assert pc.evaluate_precondition(_pcond(type="placement_count", placement="cloud", count=2), placed, pack) is True   # >= boundary
    assert pc.evaluate_precondition(_pcond(type="placement_count", placement="cloud", count=3), placed, pack) is False


def test_cc10_policy_contradiction(pack_state):
    pack, state = pack_state
    from app.engine.state import PolicyDecisionState
    both_perm = replace(state, policy_decisions=(
        PolicyDecisionState("data_retention", "indefinite", True),
        PolicyDecisionState("data_access", "open_to_all_staff", True),
    ))
    p = _pcond(type="policy_contradiction", policy="data_retention", other_policy="data_access")
    assert pc.evaluate_precondition(p, both_perm, pack) is False
    opposite = replace(state, policy_decisions=(
        PolicyDecisionState("data_retention", "indefinite", True),      # index 0 permissive
        PolicyDecisionState("data_access", "need_to_know", True),        # index 2 restrictive
    ))
    assert pc.evaluate_precondition(p, opposite, pack) is True


def test_cc10_policy_contradiction_guard_no_div_zero(pack_state):
    pack, state = pack_state
    from types import SimpleNamespace
    prov = {"source": "AUTHORED", "note": "n"}
    one = PolicyOption(key="one", category="c", cost=0, effects={}, options=["only"], default="only", provenance=prov)
    zero = PolicyOption(key="zero", category="c", cost=0, effects={}, options=[], default=None, provenance=prov)
    other = PolicyOption(key="other", category="c", cost=0, effects={}, options=["a", "b"], default="a", provenance=prov)
    fake = SimpleNamespace(policies=[one, zero, other])
    p1 = _pcond(type="policy_contradiction", policy="one", other_policy="other")
    p0 = _pcond(type="policy_contradiction", policy="zero", other_policy="other")
    assert pc._policy_contradiction(p1, state, fake) is False  # one-option: no ZeroDivisionError
    assert pc._policy_contradiction(p0, state, fake) is False  # legacy zero-option: no exception


def test_cc10_sponsor_unassigned(pack_state):
    pack, state = pack_state
    assert pc.evaluate_precondition(_pcond(type="sponsor_unassigned", capability="store_operations"), state, pack) is True
    assert pc.evaluate_precondition(_pcond(type="sponsor_unassigned", capability="order_fulfilment"), state, pack) is False
    assert pc.evaluate_precondition(_pcond(type="sponsor_unassigned", capability="ghost_cap"), state, pack) is True


def test_cc10_round_equals(pack_state):
    pack, state = pack_state  # round 3
    assert pc.evaluate_precondition(_pcond(type="round_equals", round=3), state, pack) is True
    assert pc.evaluate_precondition(_pcond(type="round_equals", round=4), state, pack) is False


# -- CC11: multi-cap suppression is deterministic in authored deck order ------------------

def test_cc11_suppression_deterministic(pack_state):
    pack, _ = pack_state
    do_nothing = sig.do_nothing_state()
    ledger = lg.advance_ledger((), do_nothing, pack)
    fired, suppressed = ev.resolve_events(do_nothing, pack, ledger)
    # exactly two order_fulfilment events fire (deck order), the third is suppressed by O2
    of_events = ["inventory_audit_question", "warehouse_rollout_gap", "pos_support_ending"]
    fired_of = [k for k in fired if k in of_events]
    assert fired_of == ["inventory_audit_question", "warehouse_rollout_gap"]
    supp = [s for s in suppressed if s.event_key == "pos_support_ending"]
    assert supp and supp[0].reason == "cap" and supp[0].capability == "order_fulfilment"
    # deterministic across runs
    for _ in range(20):
        again, _ = ev.resolve_events(do_nothing, pack, ledger)
        assert again == fired


# -- CC12: failed-node binding is total (node or None) and deterministic ------------------

def _event(preconditions):
    return Event.model_validate({
        "key": "synthetic", "preconditions": preconditions, "strategy_affinity": [],
        "from_persona": "p", "body_key": "b", "outcomes": {}, "options": [],
        "provenance": {"source": "AUTHORED", "note": "n"},
    })


def test_cc12_failed_node_binding(pack_state):
    pack, state = pack_state
    spof_event = _event([{"type": "node_is_spof", "node": "wan_link"},
                         {"type": "signal_open", "signal": "ord_cap_01", "severity": "critical"}])
    assert ev.failed_node(spof_event, state, pack) == "wan_link"  # explicit SPOF wins
    cap_event = _event([{"type": "signal_open", "signal": "ord_cap_01", "severity": "critical"}])
    assert ev.failed_node(cap_event, state, pack) == "order_app"  # primary-cap bottleneck
    empty_event = _event([{"type": "round_equals", "round": 3}])
    assert ev.failed_node(empty_event, state, pack) is None  # empty sequence -> no node bound


# -- CC13: arms is an additional gate, not a replacement ----------------------------------

def test_cc13_arms_gate(pack_state):
    pack, state = pack_state
    from app.engine.state import PolicyDecisionState
    # unlogged_system_change waits on sec_identity_01 critical; armed by user_account_changes_unlogged
    # (access_logging at permissive `unlogged`). Precondition FALSE (empty ledger) -> never fires,
    # even with the arm open.
    fired, _ = ev.resolve_events(state, pack, ())
    assert "unlogged_system_change" not in fired
    # arms open by default (access_logging unlogged)
    assert ev.arms_gate_satisfied(next(e for e in pack.events if e.key == "unlogged_system_change"), state, pack) is True
    # close the arm: move access_logging off its permissive value
    closed = replace(state, policy_decisions=(
        PolicyDecisionState("access_logging", "full_audit_trail", True),
    ))
    assert ev.arms_gate_satisfied(next(e for e in pack.events if e.key == "unlogged_system_change"), closed, pack) is False
    # both true: sec_identity_01 open critical AND arm open -> the event is SATISFIABLE (it fires
    # or is O2-suppressed, but never silently dropped). Isolate arms from the O2 cap by checking
    # satisfiability = fired or recorded-suppressed.
    ledger = (LedgerSignal(
        key="sec_identity_01", episode_id=1, capability="firm_infrastructure", metric="m",
        metric_kind="presence", value=1.0, severity="critical", status="open", first_shown_round=3,
    ),)
    fired2, supp2 = ev.resolve_events(state, pack, ledger)
    satisfiable_open = "unlogged_system_change" in fired2 or any(
        s.event_key == "unlogged_system_change" for s in supp2
    )
    assert satisfiable_open is True
    # arm closed, precondition true -> NOT satisfiable at all (arms is a required gate, so the
    # event is neither fired nor even recorded as cap-suppressed).
    fired3, supp3 = ev.resolve_events(closed, pack, ledger)
    satisfiable_closed = "unlogged_system_change" in fired3 or any(
        s.event_key == "unlogged_system_change" for s in supp3
    )
    assert satisfiable_closed is False


# -- CC14: duration evidence shape & staffing modifier -----------------------------------

def test_cc14_duration_and_staffing_modifier(pack_state):
    pack, state = pack_state
    d = ev.outage_duration(state, "order_app", "order_fulfilment", pack)
    assert set(d) == {"node", "base_rto_hours", "failover_exists", "failover_factor",
                      "staffing_modifier", "duration_hours", "blast_radius"}
    assert d["failover_exists"] is False and d["failover_factor"] == ev.NO_FAILOVER_MULTIPLIER
    assert d["base_rto_hours"] == ev.DEFAULT_BASE_RTO_HOURS  # order_app has no catalog base_rto
    assert d["staffing_modifier"] == 1.7  # load 3.4 / staff 2.0
    assert d["duration_hours"] == round(8.0 * 3.0 * 1.7, 1)

    balanced = replace(state, staff=StaffPool(3.4, 3.4))  # load == staff
    assert ev.outage_duration(balanced, "order_app", "order_fulfilment", pack)["staffing_modifier"] == 1.0
    doubled = replace(state, staff=StaffPool(2.0, 4.0))   # 200% load
    assert ev.outage_duration(doubled, "order_app", "order_fulfilment", pack)["staffing_modifier"] == 2.0
    understaffed = replace(state, staff=StaffPool(0.0, 3.4))
    assert ev.outage_duration(understaffed, "order_app", "order_fulfilment", pack)["staffing_modifier"] == ev.UNDERSTAFFED_MULTIPLIER


def test_cc14_failover_factor_one_with_failover_edge(pack_state):
    pack, state = pack_state
    # a failover edge that gives order_fulfilment an alternate path around order_app
    with_failover = replace(state, edges=state.edges + (ArchEdge("core_switch", "order_store", "failover"),))
    d = ev.outage_duration(with_failover, "order_app", "order_fulfilment", pack)
    assert d["failover_exists"] is True and d["failover_factor"] == 1.0

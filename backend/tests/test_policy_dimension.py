"""Focused tests for the 1.4 closeout information-policy dimension.

Covers the closeout spec §5.3 null/negative table and invariants C2-C7, C11, C12:
the asymmetric ordinal formula, weighted aggregation, the discipline floor, that
policy order (not string equality) drives the score, and that every broken scoring
input raises instead of guessing.

Run: `python -m pytest tests/test_policy_dimension.py`
"""
from __future__ import annotations

import dataclasses

import pytest

from app.engine.management import (
    POLICY_DISCIPLINE_FLOOR,
    _asymmetric_alignment,
    _resolve_policy_decisions,
    policy_discipline,
    policy_switch_alignment,
)
from app.engine.state import PolicyDecisionState
from app.seed.demo import load_scenario

SIX = ("data_collection", "data_retention", "data_access",
       "access_logging", "data_egress", "staff_monitoring")


def _seed():
    return load_scenario("riverside_r3")


def _decisions(active=True, overrides=None):
    """The six Riverside defaults, all active unless overridden. `overrides` maps a
    policy key to a (selected, actively_decided) pair."""
    pack, _ = _seed()
    defaults = {p.key: p.default for p in pack.policies}
    overrides = overrides or {}
    out = []
    for k in SIX:
        sel, act = overrides.get(k, (defaults[k], active))
        out.append(PolicyDecisionState(k, sel, actively_decided=act))
    return tuple(out)


def _with(state, decisions):
    return dataclasses.replace(state, policy_decisions=tuple(decisions))


# =====================================================================
# The frozen asymmetric ordinal formula (decision 2) — C2, C3, C4
# =====================================================================

def test_c3_exact_match_is_one():
    for n in range(2, 11):
        for i in range(n):
            val, direction = _asymmetric_alignment(i, i, n - 1)
            assert val == 1.0 and direction == "match"


def test_two_option_opposite_ends():
    # §5.3 exact row: permissive miss 0.0; strict overshoot 0.5.
    perm, d1 = _asymmetric_alignment(0, 1, 1)   # team permissive, ideal strict
    strict, d2 = _asymmetric_alignment(1, 0, 1)  # team strict, ideal permissive
    assert (perm, d1) == (0.0, "too_permissive")
    assert (strict, d2) == (0.5, "stricter")


def test_c2_equal_distance_penalizes_permissive_more():
    for n in range(2, 7):
        span = n - 1
        for i in range(n):
            if 0 <= i - 1 and i + 1 <= n - 1:
                perm, dp = _asymmetric_alignment(i - 1, i, span)
                strict, ds = _asymmetric_alignment(i + 1, i, span)
                assert dp == "too_permissive" and ds == "stricter"
                assert strict > perm, (n, i, perm, strict)


def test_c4_alignment_in_unit_interval():
    for n in range(2, 11):
        span = n - 1
        for t in range(n):
            for i in range(n):
                val, _ = _asymmetric_alignment(t, i, span)
                assert 0.0 <= val <= 1.0, (n, t, i, val)


# =====================================================================
# Aggregation, null paths, discipline — §5.3 table, C6, C12
# =====================================================================

def test_no_stakeholder_preference_alignment_is_one():
    # Strip the policy preference domain -> no rows -> alignment 1.0, preferences 0.
    pack, state = _seed()
    stripped = pack.model_copy(update={"preferences": {}})
    val, ev = policy_switch_alignment(stripped, _with(state, _decisions()))
    assert val == 1.0 and ev["preferences"] == 0 and ev["total_weight"] == 0.0


def test_empty_runtime_tuple_uses_defaults_and_is_undisciplined():
    # §5.3: policies present, empty runtime tuple -> every default, all inactive,
    # discipline at the floor. C12: ignoring policy is not neutral.
    pack, state = _seed()
    empty = _with(state, ())
    dval, dev = policy_discipline(pack, empty)
    assert dval == POLICY_DISCIPLINE_FLOOR
    assert dev["actively_decided"] == 0 and dev["eligible"] == 6
    assert set(dev["undecided"]) == set(SIX)
    # alignment is identical to the attentive seed (same selected defaults), because
    # only the discipline factor depends on the active flag.
    a_empty, _ = policy_switch_alignment(pack, empty)
    a_seed, _ = policy_switch_alignment(pack, _with(state, _decisions()))
    assert a_empty == a_seed


def test_c6_active_default_counts_as_managed():
    # Identical selections, active flag false vs true: alignment equal, discipline higher.
    pack, state = _seed()
    inactive = _with(state, _decisions(active=False))
    active = _with(state, _decisions(active=True))
    assert policy_switch_alignment(pack, inactive)[0] == policy_switch_alignment(pack, active)[0]
    assert policy_discipline(pack, active)[0] > policy_discipline(pack, inactive)[0]
    assert policy_discipline(pack, active)[0] == 1.0
    assert policy_discipline(pack, inactive)[0] == POLICY_DISCIPLINE_FLOOR


def test_discipline_partial_ratio():
    pack, state = _seed()
    # three of six actively decided
    decs = _decisions(active=False, overrides={
        "data_collection": (None, True), "data_retention": (None, True), "data_access": (None, True),
    })
    # fix selected to real defaults so resolution passes
    defaults = {p.key: p.default for p in pack.policies}
    decs = tuple(dataclasses.replace(d, selected=defaults[d.policy]) for d in decs)
    val, ev = policy_discipline(pack, _with(state, decs))
    assert ev["actively_decided"] == 3 and ev["eligible"] == 6
    assert val == pytest.approx(0.25 + 0.75 * 0.5)  # 0.625


def test_stakeholder_without_policy_view_excluded():
    # it/hr/investor/vendor/media archetypes hold no policy rows; the 9 that do drive
    # the score. Evidence rows reference only archetypes present in the preference table.
    pack, state = _seed()
    _, ev = policy_switch_alignment(pack, _with(state, _decisions()))
    scored_archetypes = {r["archetype"] for r in ev["rows"]}
    assert "it" not in scored_archetypes and "media" not in scored_archetypes
    assert {"finance", "customer", "regulator", "security_auditor"} <= scored_archetypes


# =====================================================================
# C5 — order is consumed, not string equality
# =====================================================================

def test_c5_reversing_option_order_changes_the_score():
    pack, state = _seed()
    base, _ = policy_switch_alignment(pack, _with(state, _decisions()))
    # Reverse data_retention's option order without touching any string. The team's
    # selected 'indefinite' moves from index 0 to index 2; ideals move too; the
    # asymmetric distances therefore change, so the aggregate must move.
    new_policies = [
        p.model_copy(update={"options": list(reversed(p.options))})
        if p.key == "data_retention" else p
        for p in pack.policies
    ]
    reversed_pack = pack.model_copy(update={"policies": new_policies})
    moved, _ = policy_switch_alignment(reversed_pack, _with(state, _decisions()))
    assert moved != base


# =====================================================================
# C11 — policy scores come from the pack and the state, independently
# =====================================================================

def test_c11_mutating_a_selection_changes_the_score():
    pack, state = _seed()
    base, _ = policy_switch_alignment(pack, _with(state, _decisions()))
    # Move data_egress from permissive (index 0) to strictest (index 2, 'no_export').
    moved, ev = policy_switch_alignment(
        pack, _with(state, _decisions(overrides={"data_egress": ("no_export", True)}))
    )
    assert moved != base
    egress_rows = [r for r in ev["rows"] if r["policy"] == "data_egress"]
    assert egress_rows and all(r["selected"] == "no_export" for r in egress_rows)


def test_c11_mutating_a_preference_ideal_changes_the_score():
    pack, state = _seed()
    base, _ = policy_switch_alignment(pack, _with(state, _decisions()))
    # Shift finance's data_collection ideal to the strict end.
    pref = pack.preferences["policies"]
    table = {a: dict(row) for a, row in pref.defaults_by_archetype.items()}
    fin = dict(table["finance"]); bd = dict(fin["by_decision"])
    bd["data_collection"] = {"ideal_posture": "minimal", "weight": 0.5}
    fin["by_decision"] = bd; table["finance"] = fin
    new_pref = pref.model_copy(update={"defaults_by_archetype": table})
    mutated = pack.model_copy(update={"preferences": {**pack.preferences, "policies": new_pref}})
    moved, _ = policy_switch_alignment(mutated, _with(state, _decisions()))
    assert moved != base


# =====================================================================
# C7 — no silent invalid input; every §5.3 negative case raises
# =====================================================================

def test_negative_duplicate_runtime_decision():
    pack, state = _seed()
    dup = _decisions() + (PolicyDecisionState("data_egress", "unrestricted", True),)
    with pytest.raises(ValueError, match="duplicate"):
        _resolve_policy_decisions(pack, _with(state, dup))


def test_negative_unknown_policy_key():
    pack, state = _seed()
    bad = _decisions() + (PolicyDecisionState("no_such_policy", "x", True),)
    with pytest.raises(ValueError, match="unknown policy"):
        _resolve_policy_decisions(pack, _with(state, bad))


def test_negative_selected_outside_options():
    pack, state = _seed()
    bad = _decisions(overrides={"data_retention": ("not_a_state", True)})
    with pytest.raises(ValueError, match="not one of its options"):
        _resolve_policy_decisions(pack, _with(state, bad))


def test_negative_missing_default_for_null_path():
    pack, state = _seed()
    # data_retention keeps options but loses its default; then omit it from runtime.
    new_policies = [
        p.model_copy(update={"default": None}) if p.key == "data_retention" else p
        for p in pack.policies
    ]
    holed = pack.model_copy(update={"policies": new_policies})
    partial = tuple(d for d in _decisions() if d.policy != "data_retention")
    with pytest.raises(ValueError, match="no default for the null path"):
        _resolve_policy_decisions(holed, _with(state, partial))


def test_negative_ideal_outside_options():
    pack, state = _seed()
    pref = pack.preferences["policies"]
    table = {a: dict(row) for a, row in pref.defaults_by_archetype.items()}
    fin = dict(table["finance"]); bd = dict(fin["by_decision"])
    bd["data_retention"] = {"ideal_posture": "not_a_state", "weight": 0.3}
    fin["by_decision"] = bd; table["finance"] = fin
    new_pref = pref.model_copy(update={"defaults_by_archetype": table})
    bad = pack.model_copy(update={"preferences": {**pack.preferences, "policies": new_pref}})
    with pytest.raises(ValueError, match="is not one of its options"):
        policy_switch_alignment(bad, _with(state, _decisions()))


def test_negative_preference_names_unknown_policy():
    pack, state = _seed()
    pref = pack.preferences["policies"]
    table = {a: dict(row) for a, row in pref.defaults_by_archetype.items()}
    fin = dict(table["finance"]); bd = dict(fin["by_decision"])
    bd["ghost_policy"] = {"ideal_posture": "whatever", "weight": 0.3}
    fin["by_decision"] = bd; table["finance"] = fin
    new_pref = pref.model_copy(update={"defaults_by_archetype": table})
    bad = pack.model_copy(update={"preferences": {**pack.preferences, "policies": new_pref}})
    with pytest.raises(ValueError, match="unknown policy"):
        policy_switch_alignment(bad, _with(state, _decisions()))

#!/usr/bin/env python3
"""Invariant I7 -- read the pinned figures back out of the LOADED pack and match them
against the fixed data in `handoffs/0.3-mockup-pilot/spec.md` sections 5.6/5.7 and the
0.4 mockups.

Spec section 5.4a: "the ~20 pinned figures read back and matched against 0.4 section 5.4".
This is the seed-in-the-loop half of GOVERNANCE section 4.9: the values below are read out
of `load_casepack()`, not out of the YAML text, so it proves the path from authored pack to
typed object holds the figures the mockups display.

    python3 backend/scripts/harvest_readback.py

Exit 0 when every row matches. Rows that are KNOWN to disagree are declared here with the
reason rather than silently excluded -- an omitted row is how a mismatch goes invisible.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.casepack.loader import load_casepack  # noqa: E402

PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def main() -> int:
    pack = load_casepack(PACK)
    meta = pack.metadata
    state = meta.initial_state
    catalog = {item.key: item for item in pack.catalog}
    services = {svc.key: svc for svc in pack.platform.services}
    units = {unit.unit: unit for unit in state.unit_responses}

    rows: list[tuple[str, object, object, str]] = [
        # label, actual (read from the loaded pack), expected (pinned), source
        ("company.sites", meta.company.sites, 8, "0.3 s5.7 sidebar: 8 stores"),
        ("rounds", meta.rounds, 6, "0.3 s5.7: Round 3 of 6"),
        ("initial_state.round", state.round, 3, "0.3 s5.7: Round 3 of 6"),
        ("budget.capex_per_round", meta.budget.capex_per_round,
         [400000, 260000, 220000, 220000, 200000, 200000], "0.3 s5.6 budget curve"),
        ("budget.opening_opex", meta.budget.opening_opex, 47000, "0.3 s5.6 run-rate R1 $47,000"),
        ("budget.capital_available", state.budget.capital_available, 220000, "0.3 s5.6 of $220,000"),
        ("budget.run_rate", state.budget.run_rate, 58300, "0.3 s5.6 run-rate R3 $58,300"),
        ("declared_strategy", state.declared_strategy, "cost_leadership", "0.3 s5.7 Low-Cost Leadership"),
        ("declared_strategy_round", state.declared_strategy_round, 2, "0.3 s5.7 locked in round 2"),
        ("scorecard", [state.scorecard.financial, state.scorecard.customer,
                       state.scorecard.internal_process, state.scorecard.learning_growth],
         [61, 48, 39, 27], "dashboard.html Balanced Scorecard"),
        ("unit warehouse people", units["warehouse"].people, 34, "dashboard.html WAREHOUSE 34 people"),
        ("unit warehouse contribution", units["warehouse"].contribution_pct, 25, "dashboard.html 25%"),
        ("unit store_operations people", units["store_operations"].people, 140, "dashboard.html 140 people"),
        ("unit store_operations contribution", units["store_operations"].contribution_pct, 44, "dashboard.html 44%"),
        ("unit finance people", units["finance"].people, 8, "dashboard.html FINANCE 8 people"),
        ("unit finance contribution", units["finance"].contribution_pct, 81, "dashboard.html 81%"),
        ("value_chain_coverage", dict(state.value_chain_coverage), {
            "inbound_logistics": "1/4", "operations": "2/4", "outbound_logistics": "4/5",
            "marketing_sales": "5/5", "service": "0/4", "firm_infrastructure": "3/4",
            "human_resources": "ok", "technology": "none", "procurement": "0/3",
        }, "dashboard.html Coverage across the value chain"),
        ("open_signals", state.open_signals, 3, "dashboard.html 3 open"),
        ("inbox_waiting", state.inbox_waiting, 3, "dashboard.html 3 items waiting"),
        ("people.staff_fte", state.people.staff_fte, 2.0, "people.html"),
        ("people.load_fte", state.people.load_fte, 3.4, "people.html"),
        ("people.overcommitted_pct", state.people.overcommitted_pct, 170, "people.html"),
        ("review.capital_committed", state.review.capital_committed, 174000, "review.html $174,000"),
        ("review.run_rate_before", state.review.run_rate_before, 58300, "review.html was $58,300"),
        ("review.run_rate_after", state.review.run_rate_after, 62200, "review.html $62,200 per round"),
        # per-round costs, components.html "Cost per round" column
        ("order_mgmt_v42 opex", catalog["order_mgmt_v42"].deployment_modes["on_prem"].opex, 2400, "components.html $2,400"),
        ("pos_system_2011 opex", catalog["pos_system_2011"].deployment_modes["on_prem"].opex, 3100, "components.html $3,100"),
        ("accounting_package opex", catalog["accounting_package"].deployment_modes["on_prem"].opex, 900, "components.html $900"),
        ("store_spreadsheets opex", catalog["store_spreadsheets"].deployment_modes["on_prem"].opex, 0, "components.html $0"),
        ("order_db_cluster opex", catalog["order_db_cluster"].deployment_modes["on_prem"].opex, 600, "components.html $600"),
        ("store_back_office_pc opex", catalog["store_back_office_pc"].deployment_modes["on_prem"].opex, 200, "components.html $200"),
        ("store_back_office_pc users", catalog["store_back_office_pc"].people_affected.count, 8, "components.html 8 users"),
        # components.html "Users" column, in full. Finding 1.3-008 was possible because only
        # two of the six rows were pinned; the whole column is pinned now so the pack and the
        # mockup cannot drift apart again unnoticed.
        ("order_mgmt_v42 users", catalog["order_mgmt_v42"].people_affected.count, 140, "components.html 140 users"),
        ("pos_system_2011 users", catalog["pos_system_2011"].people_affected.count, 62, "components.html 62 users"),
        ("accounting_package users", catalog["accounting_package"].people_affected.count, 8, "components.html 8 users"),
        ("store_spreadsheets users", catalog["store_spreadsheets"].people_affected.count, 140, "components.html 140 users"),
        # the wizard, 0.3 s5.6
        ("centraline_im7 on_prem", [catalog["centraline_im7"].deployment_modes["on_prem"].capex,
                                    catalog["centraline_im7"].deployment_modes["on_prem"].opex,
                                    catalog["centraline_im7"].deployment_modes["on_prem"].lead_time_rounds],
         [86000, 1900, 2], "0.3 s5.6 wizard: $86,000 + $1,900/round, 2 rounds"),
        ("centraline_im7 cloud", [catalog["centraline_im7"].deployment_modes["cloud"].capex,
                                  catalog["centraline_im7"].deployment_modes["cloud"].opex],
         [12000, 7400], "0.3 s5.6 wizard: $12,000 + $7,400/round"),
        ("centraline_im7 saas", [catalog["centraline_im7"].deployment_modes["saas"].capex,
                                 catalog["centraline_im7"].deployment_modes["saas"].opex],
         [0, 9100], "0.3 s5.6 wizard: $0 + $9,100/round"),
        ("centraline_im7 people", catalog["centraline_im7"].people_affected.count, 34, "0.3 s5.5 Warehouse 34 people"),
        ("centraline_im7 training full", catalog["centraline_im7"].training_options["full"].cost, 34000, "0.3 s5.5 full 24h $34,000"),
        ("centraline_im7 training basic", catalog["centraline_im7"].training_options["basic"].cost, 12000, "0.3 s5.5 basic 8h $12,000"),
        ("centraline_im7 process", catalog["centraline_im7"].process_option.cost, 22000, "0.3 s5.5 redesign picking $22,000"),
        ("cost_leadership reopen_cost", next(s.reopen_cost for s in pack.strategies if s.key == "cost_leadership"),
         80000, "strategy.html Reopening costs $80,000"),
        # platform pools, 0.3 s5.6 firm-wide panel
        ("compute_pool capacity_pct", services["compute_pool"].capacity_pct, 100, "0.3 s5.6 Compute pool 100% used"),
        ("storage_pool capacity_pct", services["storage_pool"].capacity_pct, 70, "0.3 s5.6 Storage pool 70% used"),
        ("starting_staff_fte", pack.platform.starting_staff_fte, 2.0, "people.html 2.0 FTE"),
    ]

    # Declared, not hidden. CG-6: the derivation and 16 of the 18 mockups disagree, and the
    # spec requires the conflict to be REPORTED rather than silently picked. The validator's
    # E14 enforces the derivation with zero tolerance, so the pack holds 46000.
    declared_conflicts = [
        ("budget.capital_remaining", state.budget.capital_remaining, 46000, 44000,
         "CG-6: derived = capital_available - capital_committed = 220000 - 174000. "
         "16 mockups display $44,000; review.html and review-locked.html display both. "
         "Recommendation in handoffs/1.3-harvest/dod.md -- 0.4 rework, not a 1.3 choice."),
        ("review remaining (derived)",
         state.review.capital_available - state.review.capital_committed, 46000, 46000,
         "CG-6: the review block's second authored home for this fact was REMOVED by the "
         "catch-up rework (models.py ReviewState). This row now recomputes it from the two "
         "fields the block still carries, and it agrees with the derivation and review.html."),
    ]

    bad = 0
    print(f"I7 read-back -- {len(rows)} pinned figures, loaded from {PACK}\n")
    for label, actual, expected, source in rows:
        ok = actual == expected
        if not ok:
            bad += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<34} {actual!r:>22}  vs pinned {expected!r}   [{source}]")

    print("\n  Declared conflicts (reported, not silently reconciled):")
    for label, actual, derived, mockup, why in declared_conflicts:
        print(f"    {label:<28} pack {actual!r} · derived {derived!r} · mockups {mockup!r}")
        print(f"      {why}")

    print(f"\n  {len(rows) - bad}/{len(rows)} matched, {bad} mismatched, "
          f"{len(declared_conflicts)} declared conflicts")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

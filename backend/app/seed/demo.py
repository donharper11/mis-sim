"""Seed a complete demo environment and describe it.

`load_scenario(name)` returns the parsed casepack and the seeded `TeamState` a
scenario is built from -- the one place the loader (which reads files) and the seed
builder (pure Python data) are wired together, so the engine package itself stays
free of I/O (invariant I2).

CLI: `python -m app.seed.demo --scenario riverside_r3` loads the pack, builds the
state, and prints what the demo contains -- the counts the scorer will read, so the
next session can confirm the seed is in the loop before trusting any figure.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.casepack.loader import load_casepack
from app.casepack.models import Casepack
from app.engine.state import TeamState

#: scenario name -> (pack directory relative to backend/, seed builder module path)
_SCENARIOS: dict[str, tuple[str, str]] = {
    "riverside_r3": ("packs/riverside_grocery", "seeds.riverside_r3"),
}

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def load_scenario(name: str) -> tuple[Casepack, TeamState]:
    if name not in _SCENARIOS:
        raise KeyError(f"unknown scenario {name!r}; known: {sorted(_SCENARIOS)}")
    pack_rel, builder_mod = _SCENARIOS[name]
    pack = load_casepack(_BACKEND_ROOT / pack_rel)

    import importlib

    module = importlib.import_module(builder_mod)
    state: TeamState = module.build_team_state()
    return pack, state


def _describe(name: str, pack: Casepack, state: TeamState) -> str:
    lines = [
        f"scenario {name}",
        f"pack {pack.metadata.pack_key} v{pack.metadata.pack_version} "
        f"round {state.round} of {pack.metadata.rounds}",
        f"strategy {state.declared_strategy}",
        f"capabilities {len(pack.capabilities)} · catalog {len(pack.catalog)} "
        f"· strategies {len(pack.strategies)}",
        f"nodes {len(state.nodes)} · edges {len(state.edges)} "
        f"· deployments {len(state.deployments)}",
        f"governance rows {len(state.governance)} · signals {len(state.signals)} "
        f"· decisions {len(state.decisions)}",
        f"staff pool {state.staff.staff_fte} fte carrying {state.staff.load_fte} load",
        f"stakeholder alignments {len(state.stakeholder_alignments)}",
        f"policy decisions {len(state.policy_decisions)} "
        f"({sum(1 for p in state.policy_decisions if p.actively_decided)} actively decided)",
    ]
    return "\n".join(lines)


def _describe_signals(pack: Casepack, state: TeamState) -> str:
    """The `--with-signals` demonstration: the R1-R3 ledger, its projection compatibility, the
    two-path event outcome, and a blast-radius traversal (1.5 spec section 5.5, contract-spec
    section 10). Pure orchestration -- the engine reads no file and no clock (invariant I2)."""
    from app.engine import events as events_mod
    from app.engine import graph as graph_mod
    from app.engine import ledger as ledger_mod
    from app.engine import catalog as catalog_mod
    import seeds.riverside_signals as sig

    lines: list[str] = ["", "-- signal ledger (R1-R3 history) --"]

    ledger = sig.signal_history()
    for s in ledger:
        lines.append(
            f"  {s.key} ep{s.episode_id} {s.metric_kind}/{s.metric} sev={s.severity} "
            f"status={s.status} shown={s.first_shown_round} cleared={s.cleared_round} "
            f"fired={s.fire_round} actionable={s.was_actionable} fix={s.cheapest_fix_when_raised}"
        )

    # Compatibility gate: the projection must reproduce the seed's three SignalState rows.
    projected = ledger_mod.project_signal_state(ledger)
    seed_rows = state.signals
    match = projected == seed_rows
    lines.append(f"  projection reproduces the seed SignalState rows: {match}")

    # Two paths from one event card (warehouse_rollout_gap), opposite outcomes, no branching.
    lines.append("")
    lines.append("-- two-path demonstration: warehouse_rollout_gap --")
    do_nothing = sig.do_nothing_state()
    open_ledger = ledger_mod.advance_ledger((), do_nothing, pack)
    fired_dn, _ = events_mod.resolve_events(do_nothing, pack, open_ledger)
    lines.append(f"  do-nothing path: warehouse_rollout_gap fires = {'warehouse_rollout_gap' in fired_dn}")

    cleared = sig.cleared_state()
    cleared_ledger = ledger_mod.advance_ledger(open_ledger, cleared, pack)
    wh = next(s for s in cleared_ledger if s.key == "wh_rollout_01")
    fired_cl, _ = events_mod.resolve_events(cleared, pack, cleared_ledger)
    lines.append(
        f"  cleared path: wh_rollout_01 status={wh.status} cleared_round={wh.cleared_round}; "
        f"warehouse_rollout_gap fires = {'warehouse_rollout_gap' in fired_cl}"
    )

    # Blast radius by traversal: removing the WAN link darkens the capabilities behind it.
    lines.append("")
    lines.append("-- blast radius (traversal) --")
    caps = [c.key for c in pack.capabilities]
    primary = {c: catalog_mod.primary_entity(pack, c) for c in caps}
    darkened = graph_mod.blast_radius(state, "wan_link", caps, primary)
    lines.append(f"  removing wan_link darkens: {darkened}")

    return "\n".join(lines)


def _describe_full(results: list[dict]) -> str:
    """The `--full` demonstration summary: six immutable RoundResults COMPUTED from the seed,
    the opex ratchet, and the R3 signal projection (spec section 5.5). Numbers come from the
    persisted RoundResult payloads, not from any hardcoded value beside them (GOVERNANCE 4.9)."""
    lines: list[str] = ["", "-- six-round game (--full): immutable RoundResults --"]
    for r in results:
        fin = r["financials"]
        sig = r["signals"]
        of = next((c for c in r["capabilities"] if c["capability"] == "order_fulfilment"), None)
        of_realised = f"{of['realised']:.4f}" if of else "n/a"
        lines.append(
            f"  round {r['round']}: opex_runrate={fin['opex_runrate']} capex_spent={fin['capex_spent']} "
            f"debt_total={fin['debt_total']} | order_fulfilment realised={of_realised} | "
            f"raised={len(sig['raised'])} cleared={len(sig['cleared'])} "
            f"fired={len(sig['fired'])} open={len(sig['open'])} | "
            f"missed_signals={len(r['missed_signals'])}"
        )
    opex = [r["financials"]["opex_runrate"] for r in results]
    lines.append(f"  opex ratchet: {' -> '.join(str(o) for o in opex)}")
    r3 = next((r for r in results if r["round"] == 3), None)
    if r3 is not None:
        lines.append("  R3 missed signals (what prints 'you were told in round N'):")
        for ms in r3["missed_signals"]:
            lines.append(
                f"    {ms['key']} first_shown_round={ms['first_shown_round']} "
                f"cheapest_fix_when_raised={ms['cheapest_fix_when_raised']}"
            )
    return "\n".join(lines)


def _run_full() -> int:
    """Seed and run the six-round game from a clean database (spec section 5.5). Creates the
    round-runner tables if absent (the Postgres path normally uses `alembic upgrade head` first;
    create_all is the idempotent fallback for a fresh DB)."""
    from app.round.db import create_all, make_engine, session_for
    from seeds.riverside_full import run_full_game

    create_all(make_engine())
    with session_for() as session:
        results = run_full_game(session)
    print(_describe_full(results))
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(prog="app.seed.demo")
    parser.add_argument("--scenario", default="riverside_r3", help="scenario name, e.g. riverside_r3")
    parser.add_argument(
        "--with-signals", action="store_true",
        help="also seed the R1-R3 signal ledger and demonstrate the two paths",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="seed and run the full six-round game into the database (spec section 5.5)",
    )
    args = parser.parse_args()

    if args.full:
        return _run_full()

    pack, state = load_scenario(args.scenario)
    print(_describe(args.scenario, pack, state))
    if args.with_signals:
        print(_describe_signals(pack, state))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

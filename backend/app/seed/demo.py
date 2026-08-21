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


def _main() -> int:
    parser = argparse.ArgumentParser(prog="app.seed.demo")
    parser.add_argument("--scenario", required=True, help="scenario name, e.g. riverside_r3")
    args = parser.parse_args()

    pack, state = load_scenario(args.scenario)
    print(_describe(args.scenario, pack, state))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

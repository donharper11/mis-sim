"""Regression guard for the raw-fit isolation contract (finding 1.3-RA-002).

`CONTRACTS.md` (`strategy.capability_weights`) and `PROVENANCE.md §4`: mis_lite's
un-normalised `component_strategy_fit` multipliers are a *different scheme* from the
authoritative `capability_weights`, retained on every strategy as `harvested_raw_fit` for
provenance only and NEVER mixed into scoring. Nothing in code consumed `harvested_raw_fit`
at `dad0989` -- it is referenced only by its field declaration in `models.py` -- but no test
made that executable. This does.

Two tests, and they are a pair:

  * the ISOLATION test mutates `harvested_raw_fit` on every strategy, three different ways,
    while holding `capability_weights` fixed, and asserts the actual 1.4 scorer produces a
    byte-identical score record. If any scorer path ever starts reading `harvested_raw_fit`,
    this fails.
  * the NON-VACUOUS test proves the isolation test can actually detect that consumer: it
    feeds the same raw-fit numbers in through `capability_weights` (the map the scorer DOES
    read) and shows the score changes. So the isolation test passes because the scorer
    ignores raw fit, not because raw fit happens to equal the weights.

Both exercise the real scorer (`score_team`) over the real loaded Riverside R3 strategy
shape via `app.seed.demo.load_scenario`, the same fixture the 1.4 pin tests use.
"""
from __future__ import annotations

from app.engine.score import score_team
from app.seed.demo import load_scenario


def _record(pack, state):
    return score_team(pack, state).record()


def _with_raw_fit(pack, transform):
    """A copy of the pack with harvested_raw_fit transformed on every strategy and every
    other field -- capability_weights included -- left exactly as loaded."""
    strategies = [
        s.model_copy(update={"harvested_raw_fit": transform(dict(s.harvested_raw_fit))})
        for s in pack.strategies
    ]
    return pack.model_copy(update={"strategies": strategies})


def test_raw_fit_mutation_cannot_change_score():
    pack, state = load_scenario("riverside_r3")
    baseline = _record(pack, state)

    mutations = {
        "zeroed": lambda rf: {k: 0.0 for k in rf},
        "reflected": lambda rf: {k: 9.9 - v for k, v in rf.items()},
        "emptied": lambda rf: {},
    }
    for label, transform in mutations.items():
        after = _record(_with_raw_fit(pack, transform), state)
        assert after == baseline, f"scoring changed under harvested_raw_fit mutation '{label}'"


def test_isolation_guard_is_not_vacuous():
    """Falsification: route the raw-fit numbers through capability_weights -- the map the
    scorer actually reads -- and the score must change. This is what the isolation test
    would catch if a scorer were switched to consume harvested_raw_fit."""
    pack, state = load_scenario("riverside_r3")
    baseline = _record(pack, state)

    prohibited = pack.model_copy(
        update={
            "strategies": [
                s.model_copy(update={"capability_weights": dict(s.harvested_raw_fit)})
                for s in pack.strategies
            ]
        }
    )
    after = _record(prohibited, state)
    assert after != baseline, (
        "raw-fit values produce the same score as the authored weights, so the isolation "
        "test could not distinguish a scorer that consumed harvested_raw_fit"
    )


if __name__ == "__main__":  # plain-stdlib run, matching test_engine_scoring.py's convention
    test_raw_fit_mutation_cannot_change_score()
    test_isolation_guard_is_not_vacuous()
    print("raw-fit isolation: both guards pass")

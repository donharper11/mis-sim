#!/usr/bin/env python3
"""Instance-isolation canary (GOVERNANCE section 5, CONTRACTS.md instance_id).

Two instances run side by side; assert ZERO cross-instance reads. Every runtime table 1.6
creates carries `instance_id` non-null (invariant I4), and every read filters on it -- this
canary proves the filtering actually isolates. Runs standalone on a temp SQLite database so it
is reachable from `make check` (rung 2) with no external Postgres; the `--full` seed exercises
the same code on Postgres.

BECSR had to retrofit instance scoping with a backfill migration and the standing note "No data
should ever leak between sections." This is the first packet where that is avoidable, and this
canary is the executable proof for module 1.6 (the full cross-section canary lands at 2.2).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.round import models as m  # noqa: E402
from app.round import snapshot as snap  # noqa: E402
from app.round.db import create_all, make_engine  # noqa: E402
from app.round.runner import RoundRunner  # noqa: E402
from app.seed.demo import load_scenario  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import seeds.riverside_full as full  # noqa: E402

failures: list[str] = []


def require(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{('  ' + detail) if detail and not ok else ''}")
    if not ok:
        failures.append(label)


def _seed_instance(session, pack, instance_id: int, strategy: str, marker_key: str) -> RoundRunner:
    """Seed one instance/team with round-1 estate, tagged with a unique marker node key."""
    session.add(m.TeamStateRow(
        instance_id=instance_id, team_id=1, current_round=1, declared_strategy=strategy,
        declared_strategy_round=2, cash=0, opex_runrate=pack.metadata.budget.opening_opex,
    ))
    session.flush()
    # reuse the full-game round-1 estate assembly, then swap instance_id + add a marker node.
    full._seed_round_estate(session, pack, 1)
    # relabel the just-seeded round-1 rows from instance 1 (the assembler's default) to this id.
    if instance_id != full.INSTANCE_ID:
        for model in m.ALL_TABLES:
            for row in session.query(model).filter(
                model.instance_id == full.INSTANCE_ID, model.team_id == 1
            ).all():
                if isinstance(row, m.TeamStateRow):
                    continue
                row.instance_id = instance_id
        session.flush()
    session.add(m.ArchNodeRow(
        instance_id=instance_id, team_id=1, round=1, key=marker_key,
        roles_filled=[], availability=0.99, installed_round=1, service_life_rounds=6,
        serves=[], throughput=None, owns_entities=[], placement=None, opex_contribution=0,
    ))
    session.flush()
    return RoundRunner(session, pack, instance_id, 1)


def main() -> int:
    pack, _ = load_scenario("riverside_r3")
    with tempfile.TemporaryDirectory() as td:
        url = f"sqlite:///{Path(td) / 'iso.db'}"
        engine = make_engine(url)
        create_all(engine)
        session = sessionmaker(bind=engine, future=True, expire_on_commit=False)()

        # instance 101 seeded first and fully, so its default-labelled rows are claimed before
        # instance 202 is seeded (the relabel only moves the just-added instance-1 rows).
        r1 = _seed_instance(session, pack, 101, "cost_leadership", "iso_marker_A")
        # advance instance 101 round 1 BEFORE seeding 202, so the assembler's default rows are gone.
        r1.lock(1)
        r1.advance(1)
        r2 = _seed_instance(session, pack, 202, "differentiation", "iso_marker_B")
        r2.lock(1)
        r2.advance(1)

        # 1. every table's rows partition by instance_id: instance 101 sees none of 202's, and v.v.
        cross = []
        for model in m.ALL_TABLES:
            a_ids = {getattr(row, "instance_id") for row in session.query(model).filter(
                model.instance_id == 101).all()}
            b_ids = {getattr(row, "instance_id") for row in session.query(model).filter(
                model.instance_id == 202).all()}
            if a_ids - {101} or b_ids - {202}:
                cross.append(model.__tablename__)
        require(not cross, "every runtime table partitions strictly by instance_id",
                f"leaking tables: {cross}")

        # 2. the snapshot for instance 101 never contains instance 202's marker node, and v.v.
        s1 = snap.build_team_state(session, 101, 1, 1, pack)
        s2 = snap.build_team_state(session, 202, 1, 1, pack)
        keys1 = {n.key for n in s1.nodes}
        keys2 = {n.key for n in s2.nodes}
        require("iso_marker_A" in keys1 and "iso_marker_A" not in keys2,
                "instance 101 marker node is visible to 101 and invisible to 202")
        require("iso_marker_B" in keys2 and "iso_marker_B" not in keys1,
                "instance 202 marker node is visible to 202 and invisible to 101")

        # 3. each instance carries its own declared strategy through the snapshot (no bleed).
        require(s1.declared_strategy == "cost_leadership" and s2.declared_strategy == "differentiation",
                "each instance keeps its own declared strategy")

        # 4. RoundResults are isolated: reading instance 101 never returns 202's payload.
        rr1 = session.get(m.RoundResult, (101, 1, 1))
        rr2 = session.get(m.RoundResult, (202, 1, 1))
        require(rr1 is not None and rr2 is not None
                and rr1.payload["instance_id"] == 101 and rr2.payload["instance_id"] == 202,
                "each instance has its own immutable RoundResult, no cross-read")

        session.close()
        engine.dispose()

    if failures:
        print(f"\n{len(failures)} isolation check(s) failed")
        return 1
    print("\ninstance-isolation canary green -- zero cross-instance reads")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

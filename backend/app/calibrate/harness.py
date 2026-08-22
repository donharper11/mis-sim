"""Seed the archetypes, run them through the real round-runner, and read back the scores.

Pack-agnostic (invariant I1): this module names no casepack. It loads whatever pack the caller
passes and runs the registered archetypes against it. The archetypes themselves are pack-specific
seed builders that live in ``backend/seeds/`` -- the same split the ``--full`` seed uses.
"""

from __future__ import annotations

import hashlib
import importlib
import json

from app.casepack.models import Casepack

#: The registered archetypes (spec section 5.1). The four mandatory ones; more may be appended.
#: Named by module -- no casepack identity here (I1).
ARCHETYPE_MODULES: tuple[str, ...] = (
    "seeds.archetype_do_nothing",
    "seeds.archetype_all_tech_no_org",
    "seeds.archetype_balanced",
    "seeds.archetype_overspender",
)


def load_archetypes() -> list:
    """Import each archetype module and return its ``ARCHETYPE`` instance, in registration order."""
    return [importlib.import_module(mod).ARCHETYPE for mod in ARCHETYPE_MODULES]


def run_calibration(pack: Casepack, *, db_url: str | None = None):
    """Seed and run every archetype for six rounds on a fresh database; return
    ``(archetypes, results)`` where ``results`` maps ``archetype.key -> [payload_r1 .. payload_r6]``.

    Runs headless: builds the round-runner tables via ``create_all`` (the idempotent fallback the
    ``--full`` seed uses) so no Postgres is required in local dev. Each archetype wipes its own
    instance first, so a re-run and a clean DB produce identical results (I4)."""
    from app.round.db import create_all, make_engine
    from sqlalchemy.orm import sessionmaker

    engine = make_engine(db_url)
    create_all(engine)
    session = sessionmaker(bind=engine, future=True, expire_on_commit=False)()
    try:
        archetypes = load_archetypes()
        results = {a.key: a.run(session, pack) for a in archetypes}
        session.commit()
    finally:
        session.close()
        engine.dispose()
    return archetypes, results


def score_digest(results: dict[str, list[dict]]) -> str:
    """A hash of the COMPUTED SCORE FIELDS only -- ``firm_score``, per-capability ``terms`` and
    ``realised``, and the ``scorecard`` -- across every archetype and round (invariant I2).

    Deliberately NOT a byte hash of the database: autoincrement ids and insert order differ between
    runs and are not part of the determinism claim (spec decision 2). Same pack + same archetypes
    must yield one hash across repeated runs."""
    parts: list[str] = []
    for key in sorted(results):
        for payload in results[key]:
            caps = [
                {"capability": c["capability"], "terms": c["terms"], "realised": c["realised"]}
                for c in payload["capabilities"]
            ]
            parts.append(json.dumps(
                {
                    "archetype": key,
                    "round": payload["round"],
                    "firm_score": payload["firm_score"],
                    "scorecard": payload["scorecard"],
                    "capabilities": caps,
                },
                sort_keys=True,
            ))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

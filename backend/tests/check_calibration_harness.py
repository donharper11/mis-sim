#!/usr/bin/env python3
"""Calibration-harness invariant guards (1.7 spec section 6). Reachable from ``make check`` by glob
(QUALITY_PROTOCOL rung 2), so a regression is caught by the single gate, not only a by-hand run.

  I1  runs any pack unchanged -- no case-identity branching in app/calibrate/
  I2  deterministic over the computed scores -- 3 runs, one hash of the score fields only
  I3  no raw engine keys in the default printed report (business labels only)
  I4  instances torn down; no leak between archetypes, no read of an instance never run
  I5  never mutates the pack -- yaml md5 identical before/after a run
  I6  the gate is not asserted by code -- no dominance sys.exit(1) / spread assertion

I7 (the 1.4 pin is untouched) is guarded by the existing tests/test_engine_scoring.py, which
``make check`` already runs -- the harness reads RoundResult and scores nothing, so it cannot move
the pin. Each guard is falsifiable by a planted defect (spec section 4.3), noted at its check.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.calibrate import report  # noqa: E402
from app.calibrate.harness import load_archetypes, run_calibration, score_digest  # noqa: E402
from app.casepack.loader import load_casepack  # noqa: E402
from app.round import models as m  # noqa: E402
from app.round.db import make_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

PACK_DIR = REPO / "packs" / "riverside_grocery"
#: relative to REPO (= backend/), where the grep guards run (cwd=REPO). NOT "backend/app/..":
#: that would be backend/backend/app/.. and the grep would silently match nothing.
CALIBRATE_DIR = "app/calibrate"

failures: list[str] = []


def require(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{('  ' + detail) if detail and not ok else ''}")
    if not ok:
        failures.append(label)


def _grep(pattern: str, path: str) -> list[str]:
    proc = subprocess.run(["grep", "-rnE", pattern, path], cwd=REPO, capture_output=True, text=True)
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def main() -> int:
    pack = load_casepack(PACK_DIR)

    # I1: no case-identity branching in the harness (it must run any pack unchanged).
    # Falsify: add `if pack.metadata.pack_key == "riverside...":` -> grep is non-zero.
    i1 = _grep(r"riverside|grocer", CALIBRATE_DIR)
    require(not i1, "I1: no case-identity branching in app/calibrate/", "\n".join(i1))

    # I6: the harness encodes no build-failing gate (the gate is human, spec decision 5).
    # Falsify: add `if spread > 0.15: sys.exit(1)` -> grep hits.
    i6 = _grep(r"sys\.exit\(1\)|assert.*spread|<= *0\.15|>= *0\.15", CALIBRATE_DIR)
    require(not i6, "I6: no dominance assertion / build-failing exit in app/calibrate/", "\n".join(i6))

    with tempfile.TemporaryDirectory() as td:
        # I2: deterministic over the computed scores -- 3 runs on fresh DBs -> one hash.
        # Falsify: perturb an archetype estate value between runs -> hashes differ.
        digests = set()
        results_last = None
        for n in range(3):
            url = f"sqlite:///{Path(td) / f'run{n}.db'}"
            _, results = run_calibration(pack, db_url=url)
            digests.add(score_digest(results))
            results_last = results
        require(len(digests) == 1, "I2: deterministic over score fields (3 runs -> 1 hash)",
                f"hashes: {digests}")

        # I3: no raw engine keys (triple snake_case) in the DEFAULT report -- labels only.
        # Falsify: print a capability_key instead of its labels.yaml name -> grep hits.
        archetypes = load_archetypes()
        text = report.render(pack, PACK_DIR, archetypes, results_last, debug=False)
        import re
        i3 = [ln for ln in text.splitlines() if re.search(r"[a-z]+_[a-z]+_[a-z]+", ln)]
        require(not i3, "I3: no raw engine keys in the default report", "\n".join(i3))

        # I4: instances torn down; no leak, no read of an instance never run.
        # Falsify: drop the per-archetype wipe -> a re-run doubles rows / cross-reads appear.
        url = f"sqlite:///{Path(td) / 'iso.db'}"
        run_calibration(pack, db_url=url)
        run_calibration(pack, db_url=url)  # re-run: idempotent wipe must keep counts at 6, not 12
        session = sessionmaker(bind=make_engine(url), future=True)()
        try:
            expected_ids = {a.instance_id for a in archetypes}
            present_ids = {
                row.instance_id for row in session.query(m.RoundResult).all()
            }
            require(present_ids == expected_ids,
                    "I4: only the archetype instances have results (no leak)",
                    f"present={present_ids} expected={expected_ids}")
            counts_ok = all(
                session.query(m.RoundResult).filter(
                    m.RoundResult.instance_id == a.instance_id).count() == pack.metadata.rounds
                for a in archetypes
            )
            require(counts_ok, "I4: each archetype has exactly `rounds` results after a re-run (idempotent wipe)")
            never_run = session.query(m.RoundResult).filter(m.RoundResult.instance_id == 999).count()
            require(never_run == 0, "I4: an instance never run has zero results")
        finally:
            session.close()

        # I5: never mutates the pack -- yaml md5 identical before/after a run.
        # Falsify: plant a pack file write -> md5 differs.
        def _pack_md5() -> str:
            import hashlib
            h = hashlib.md5()
            for p in sorted(PACK_DIR.rglob("*.yaml")):
                h.update(p.read_bytes())
            return h.hexdigest()

        before = _pack_md5()
        run_calibration(pack, db_url=f"sqlite:///{Path(td) / 'i5.db'}")
        require(before == _pack_md5(), "I5: harness never mutates the pack (yaml md5 identical)")

    if failures:
        print(f"\n{len(failures)} calibration-harness guard(s) failed")
        return 1
    print("\nall calibration-harness guards green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

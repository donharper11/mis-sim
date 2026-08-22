"""CLI: ``python -m app.calibrate <pack_dir> [--debug] [--db-url URL]``.

Loads the pack through the same loader the ``--full`` seed uses (``load_casepack``), seeds the four
archetypes, runs each through the real round-runner for six rounds, and prints the score curves.
One command, clean DB, real engine (spec section 5.5). It NEVER exits non-zero on a dominance
condition and asserts no gate -- the gate is the calibration authority's (spec decision 5 / I6).

Runs headless: with no ``--db-url`` it uses the configured database (Postgres). In CI-less local dev
without Postgres, pass a SQLite URL, e.g. ``--db-url sqlite:////tmp/calibrate.db``; the round-runner
tables are created via the ``create_all`` fallback either way.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.calibrate import report
from app.calibrate.harness import run_calibration
from app.casepack.loader import load_casepack


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="app.calibrate")
    parser.add_argument("pack_dir", help="path to the casepack directory to calibrate against")
    parser.add_argument("--debug", action="store_true",
                        help="reveal raw pack sub-keys and per-capability decomposition detail")
    parser.add_argument("--db-url", default=None,
                        help="database URL (default: configured DB; use a sqlite:/// URL headless)")
    args = parser.parse_args(argv)

    pack_dir = Path(args.pack_dir)
    pack = load_casepack(pack_dir)
    archetypes, results = run_calibration(pack, db_url=args.db_url)
    print(report.render(pack, pack_dir, archetypes, results, debug=args.debug))
    # Report only: no dominance assertion, no build-failing exit (spec decision 5 / O3 / I6).
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

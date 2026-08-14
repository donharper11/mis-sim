#!/usr/bin/env python3
"""Assert every fixture pack raises the code it is named for, at the exit code it claims.

    python3 backend/tests/check_fixture_matrix.py

Exits 0 when the whole matrix holds, 1 otherwise. No test framework, so no new dependency.
This is the reproducible form of spec 1.2 section 8 step 5: a code with no fixture is
untested, and this file is what proves the fixture actually exercises its code.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKS = REPO / "backend/tests/fixtures/packs"
CLI = REPO / "backend/bin/validate_casepack"

# fixture -> (codes it must raise, exit code it must return)
MATRIX: dict[str, tuple[set[str], int]] = {
    "minimal_valid": (set(), 0),
    "broken_E00": ({"E00"}, 1),
    "broken_E01": ({"E01"}, 1),
    "broken_E02": ({"E02"}, 1),
    "broken_E03": ({"E03"}, 1),
    "broken_E04": ({"E04"}, 1),
    "broken_E05": ({"E05"}, 1),
    "broken_E06": ({"E06"}, 1),
    "broken_E07": ({"E07"}, 1),
    "broken_E08": ({"E08"}, 1),
    "broken_E09": ({"E09"}, 1),
    "broken_E10": ({"E10"}, 1),
    "broken_E11": ({"E11"}, 1),
    "broken_E20": ({"E20"}, 1),
    "broken_E21": ({"E21"}, 1),
    "broken_E22": ({"E22"}, 1),
    "broken_E23": ({"E23"}, 1),
    "broken_I3": ({"I3"}, 1),
    "warn_W01": ({"W01"}, 0),
    "warn_heuristics": ({"W02", "W03", "W04", "W05", "W06", "W07"}, 0),
}

# I8 (models.py dropping a value on reload) has no fixture: it is a property of the schema
# layer, not of authored content, so no pack can be written that provokes it. Recorded in
# handoffs/1.2-validator/dod.md rather than left silent.
NO_FIXTURE = {"I8"}


def main() -> int:
    failures: list[str] = []
    covered: set[str] = set()
    width = max(len(name) for name in MATRIX)
    print(f"{'fixture'.ljust(width)}  want  got  codes raised")
    for name, (wanted, wanted_exit) in MATRIX.items():
        proc = subprocess.run(
            [str(CLI), "--json", str(PACKS / name)], capture_output=True, text=True
        )
        findings = json.loads(proc.stdout) if proc.stdout.strip() else []
        raised = {finding["code"] for finding in findings}
        covered |= raised
        missing = wanted - raised
        ok = not missing and proc.returncode == wanted_exit
        print(
            f"{name.ljust(width)}  {wanted_exit:>4}  {proc.returncode:>3}  "
            f"{','.join(sorted(raised)) or '-'}   {'PASS' if ok else 'FAIL'}"
        )
        if missing:
            failures.append(f"{name}: did not raise {sorted(missing)}")
        if proc.returncode != wanted_exit:
            failures.append(f"{name}: exit {proc.returncode}, expected {wanted_exit}")

    sys.path.insert(0, str(REPO / "backend"))
    from app.casepack.validate import catalogue  # noqa: E402

    declared = set(catalogue()["codes"])
    untested = declared - covered - NO_FIXTURE
    if untested:
        failures.append(f"codes declared but never exercised by a fixture: {sorted(untested)}")

    print()
    if failures:
        for line in failures:
            print(f"FAIL  {line}")
        return 1
    print(f"all {len(MATRIX)} fixtures behave as named; "
          f"{len(covered)} of {len(declared)} codes exercised, {sorted(NO_FIXTURE)} recorded as unfixturable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Engine purity guards for the 1.5 event & signal engine (contract-spec CC8; 1.5 spec I1-I3, I8).

Run from the repo (make check invokes it by glob). It greps the tracked engine sources -- the
same `git ls-files` set the contract-spec CC8 row names -- and fails if any guard is violated:

  I1  no pack-identity branching (`riverside`, `grocer`)
  I2  pure: no I/O, clock, randomness, or session (`random.`, `datetime.now`, `session`, `open(`)
  I3  no displayed English in engine string literals
  I8  `metric_kind` is read ONLY in the watch-rule evaluator / ledger writer (ledger.py)

The CC8 row calls out that the v1.0 grep missed `open(` and `session`; both are included here,
so planting `open("x")`, a `session` access, or `if pack == "riverside"` makes this FAIL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = "backend/app/engine"

failures: list[str] = []


def _tracked_engine_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", ENGINE], cwd=REPO, capture_output=True, text=True, check=True
    )
    return [f for f in out.stdout.splitlines() if f.endswith(".py")]


def _grep(pattern: str, files: list[str], extra_filter: str | None = None) -> list[str]:
    proc = subprocess.run(
        ["grep", "-nE", pattern, *files], cwd=REPO, capture_output=True, text=True
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if extra_filter:
        keep = subprocess.run(
            ["grep", "-vE", extra_filter], input="\n".join(lines),
            capture_output=True, text=True,
        )
        lines = [ln for ln in keep.stdout.splitlines() if ln.strip()]
    return lines


def require(ok: bool, label: str, detail: list[str] | None = None) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        for d in detail or []:
            print(f"        {d}")
        failures.append(label)


def main() -> int:
    files = _tracked_engine_files()

    # I1 + I2 -- the CC8 grep, exactly as the contract-spec froze it.
    cc8 = _grep(r"riverside|grocer|random\.|datetime\.now|session|open\(", files)
    require(not cc8, "CC8/I1+I2: no identity-branching, I/O, clock, randomness, or session", cc8)

    # I3 -- no displayed English in string literals (docstrings, comments and raises excluded).
    i3 = _grep(r'"[A-Z][a-z]+ [a-z]+ [a-z]+', files, extra_filter=r'#|"""|raise')
    require(not i3, "I3: no displayed English in engine string literals", i3)

    # I8 -- metric_kind is read only in the watch-rule evaluator / ledger writer (ledger.py).
    mk = _grep(r"metric_kind", files)
    stray = [ln for ln in mk if not ln.startswith("backend/app/engine/ledger.py")]
    require(not stray, "I8: metric_kind confined to the evaluator / ledger writer (ledger.py)", stray)

    if failures:
        print(f"\n{len(failures)} engine purity guard(s) failed")
        return 1
    print("\nall engine purity guards green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

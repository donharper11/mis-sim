#!/usr/bin/env python3
"""Round-runner invariant guards (1.6 spec section 6). Reachable from `make check` by glob, so a
regression is caught by the single gate, not only by a by-hand run (QUALITY_PROTOCOL rung 2,
finding 1.5-RC-004 / CU-003).

Grep-shaped invariants over `backend/app/round/`:

  I1  no pack-identity branching (`riverside`, `grocer`) in the round package -- the pack-specific
      seed lives in `backend/seeds/`, so the runner stays casepack-agnostic (GOVERNANCE 4.6)
  I3  no displayed English in round string literals (business/engine language is not shown here)
  I4  every table read filters on instance_id: no `select(` line without `instance_id`
  I5  exactly one `rescore` marker in runner.py (the single step-12 re-entry; the real proof is
      the planted-second-rescore property test in test_round_runner.py, spec I5 note)
  I6  RoundResult is never UPDATEd (immutable; a re-run needs an unlock that deletes it, O1)
  I7  opex is recomputed, never accumulated: the in-place-increment idiom never appears in backend
  I9  the signal ledger is append-only: no UPDATE of a signal row, no `signal.status =` mutation

The engine-purity converse (I2: no session/IO under app/engine) is guarded by
check_engine_purity.py; this file guards the round package.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROUND = "backend/app/round"

failures: list[str] = []


def _grep(pattern: str, path: str, flags: str = "-rnE", inverse_filter: str | None = None) -> list[str]:
    proc = subprocess.run(["grep", flags, pattern, path], cwd=REPO, capture_output=True, text=True)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if inverse_filter:
        keep = subprocess.run(["grep", "-vE", inverse_filter], input="\n".join(lines),
                              capture_output=True, text=True)
        lines = [ln for ln in keep.stdout.splitlines() if ln.strip()]
    return lines


def require(ok: bool, label: str, detail: list[str] | None = None) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        for d in detail or []:
            print(f"        {d}")
        failures.append(label)


def main() -> int:
    i1 = _grep(r"riverside|grocer", ROUND, flags="-rniE")
    require(not i1, "I1: no pack-identity branching in app/round/", i1)

    i3 = _grep(r'"[A-Z][a-z]+ [a-z]+ [a-z]+', f"{ROUND}/", inverse_filter=r'#|"""|raise')
    # only *.py files
    i3 = [ln for ln in i3 if ln.split(":", 1)[0].endswith(".py")]
    require(not i3, "I3: no displayed English in round string literals", i3)

    i4 = [ln for ln in _grep(r"select\(", ROUND) if "instance_id" not in ln]
    require(not i4, "I4: every select() filters on instance_id", i4)

    rescore = _grep(r"rescore", f"{ROUND}/runner.py", flags="-nE")
    require(len(rescore) == 1, "I5: exactly one rescore marker in runner.py (single re-entry)", rescore)

    i6 = _grep(r"update\(RoundResult|round_result.*=.*", ROUND)
    require(not i6, "I6: RoundResult is never UPDATEd (immutable)", i6)

    i7 = _grep(r"opex_runrate \+=", "backend")
    require(not i7, "I7: opex is recomputed, never accumulated", i7)

    i9 = _grep(r"update\(.*signal|signal.*\.status *=", ROUND, flags="-rniE")
    require(not i9, "I9: signal ledger is append-only (no UPDATE / status mutation)", i9)

    if failures:
        print(f"\n{len(failures)} round invariant guard(s) failed")
        return 1
    print("\nall round invariant guards green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

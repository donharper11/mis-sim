"""The TODO:calibrate inventory (spec section 12) -- the calibration checklist, scanned live.

Printed at the top of the report BEFORE any curve is interpreted (spec pre-flight row 6): a curve
read while a load-bearing value is still a placeholder is confident nonsense. The scan is live, so
the printed count self-verifies against the pre-flight grep rather than drifting against a
hand-copied table.

Pack-agnostic (I1): the scanner reads whatever pack directory it is given and names no casepack.
The per-file "affects" notes are business-language descriptions of the curve each marker moves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_MARKER = "TODO: calibrate"

#: The convention-header line the pre-flight grep excludes (watch_rules.yaml line 7 describes the
#: marker convention; it is not itself a marker site).
_HEADER_EXCLUSION = ("watch_rules.yaml", 7)

#: Business-language note on what curve each file's markers move (spec section 12.1). Keyed by the
#: file's path relative to the pack root. Files with no note fall back to a generic line.
_AFFECTS: dict[str, str] = {
    "watch_rules.yaml": "signal raise / escalate thresholds -- the whole signal ledger and the responsiveness curve",
    "events.yaml": "scorecard deltas and option costs -- the customer and financial curves",
    "policies.yaml": "policy effect vectors and costs -- the Management policy factors",
    "catalog.yaml": "capex, opex, lead-times and outage duration -- the Technology term, cost of ownership and follow-through",
    "capabilities.yaml": "the agreed availability target -- the availability-shortfall metric",
    "platform.yaml": "placement capex / opex and IT staff load -- the Technology term",
    "preferences/platform.yaml": "stakeholder view weighting",
    "preferences/policies.yaml": "policy-preference weighting (Management)",
    "preferences/services.yaml": "service-tier preference weighting",
}

#: Register-owned calibration items 1.7 owns that are NOT pack-YAML markers (spec section 12.2).
#: Named by register code (no engine keys) with a business-language description and location.
REGISTER_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("B12 / F5", "lead-time values still at zero (the last sweep left 10 of 42)",
     "catalog and platform lead-times -- follow-through sharpness and in-flight arrival timing"),
    ("CC-D1", "the exact capacity-history figures for the signal demonstration",
     "the with-signals demonstration numbers (the formula itself is executable)"),
    ("1.6-A-003", "the per-node opex figures back-distributed to hit the ratchet targets",
     "the opex run-rate curve (the recompute path is real; the values are placeholders)"),
    ("1.6-A-004", "the people-affected counts still hand-authored in the seed",
     "the training denominator for the Organisation term"),
    ("J2", "the training-preference provenance overstates the harvest; change-management options unauthored",
     "training-preference content and its provenance claim"),
)


@dataclass
class FileMarkers:
    rel_path: str
    count: int
    affects: str
    #: (line_number, stripped_text) for each marker site -- shown only under --debug.
    sites: list[tuple[int, str]]


def scan(pack_dir: str | Path) -> list[FileMarkers]:
    """Every ``TODO: calibrate`` marker site under ``pack_dir/**.yaml``, grouped by file, with the
    convention-header line excluded. Returned in sorted path order for a stable report."""
    root = Path(pack_dir)
    out: list[FileMarkers] = []
    for path in sorted(root.rglob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        sites: list[tuple[int, str]] = []
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _MARKER not in line:
                continue
            if (rel, lineno) == _HEADER_EXCLUSION:
                continue
            sites.append((lineno, line.strip()))
        if sites:
            out.append(FileMarkers(
                rel_path=rel, count=len(sites),
                affects=_AFFECTS.get(rel, "calibration values"), sites=sites,
            ))
    return out


def total_sites(markers: list[FileMarkers]) -> int:
    return sum(fm.count for fm in markers)

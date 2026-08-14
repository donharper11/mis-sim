#!/usr/bin/env python3
"""The auditor's re-run artifact for module 1.2 — spec v1.2 section 9.2.

    python3 backend/tests/check_fixture_matrix.py

Exits 0 when everything holds, 1 otherwise. No test framework, so no new dependency.

Three things are asserted here, not one:

  MATRIX  every fixture pack raises the code it is named for, at the exit code it claims,
          and no code the spec names is left without a fixture. This is spec section 8
          step 5: a code with no fixture is untested.

  I1      SET EQUALITY between the codes this build implements and the codes spec.md
          sections 5.1-5.3 name. Added here in the v1.2 rework (finding 1.2-017). The old
          I1 counted `Fix:` prefixes in validate_messages.yaml against the ERROR-code count
          read from that same file, so adding a code incremented both sides and it could
          never fail on the dimension its name described. The two sides now come from two
          different documents, one of which this build does not own.

  I5      the text and JSON renderers emit the same findings in the same order, IN BOTH
          MODES. Added here in the v1.2 rework (finding 1.2-005): directory mode dropped
          pack attribution and reordered, and still satisfied "parseable".
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKS = REPO / "backend/tests/fixtures/packs"
CLI = REPO / "backend/bin/validate_casepack"
SPEC = REPO / "handoffs/1.2-validator/spec.md"

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
    "broken_E12": ({"E12"}, 1),
    "broken_E13": ({"E13"}, 1),
    "broken_E14": ({"E14"}, 1),
    "broken_E20": ({"E20"}, 1),
    "broken_E20_mute": ({"E20", "E12"}, 1),
    "broken_E21": ({"E21"}, 1),
    "broken_E22": ({"E22"}, 1),
    "broken_E23": ({"E23"}, 1),
    "broken_I3": ({"I3"}, 1),
    "warn_W01": ({"W01"}, 0),
    "warn_heuristics": ({"W02", "W03", "W04", "W05", "W06", "W07"}, 0),
}

# I8 (models.py dropping a value on reload) has no fixture: it is a property of the schema
# layer, not of authored content, so no pack can be written that provokes it. Accepted by
# the 1.2 audit as finding 1.2-019 after three failed falsification attempts.
NO_FIXTURE = {"I8"}

_LOCATOR = re.compile(r"^  (ERROR|WARN|INFO)\s+(\S+)\s+(.+?)\s{2,}(\S+)$")
_FIELD = re.compile(r"^         Field: (.+)$")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], capture_output=True, text=True)


# ---------------------------------------------------------------------------------------
# I1 -- implemented codes vs codes the spec names
# ---------------------------------------------------------------------------------------


def spec_named_codes() -> set[str]:
    """Codes spec.md names, read from the spec rather than from anything this build owns.

    The authority is the header's `Code list is versioned` line, which enumerates the list
    as ranges. Every code appearing at the head of a line inside sections 5.1-5.3's fenced
    blocks must fall inside it, which is checked too -- so the spec disagreeing with itself
    fails this check rather than passing it quietly.
    """
    text = SPEC.read_text(encoding="utf-8")

    header = next(line for line in text.splitlines() if "Code list is versioned" in line)
    named: set[str] = set()
    for low, high in re.findall(r"`([EWI]\d+)`–`([EWI]\d+)`", header):
        prefix = low[0]
        for number in range(int(low[1:]), int(high[1:]) + 1):
            named.add(f"{prefix}{number:0{len(low) - 1}d}")
    for single in re.findall(r"`([EWI]\d+)`(?!–)", header):
        named.add(single)

    listed: set[str] = set()
    for block in re.findall(r"```\n(.*?)```", text, re.S):
        for line in block.splitlines():
            match = re.match(r"^([EWI]\d+)\s{2,}\S", line)
            if match:
                listed.add(match.group(1))
    stray = listed - named
    if stray:
        raise SystemExit(f"spec.md disagrees with itself: {sorted(stray)} listed but not in the header range")
    return named


def check_i1() -> list[str]:
    sys.path.insert(0, str(REPO / "backend"))
    from app.casepack.validate import catalogue  # noqa: E402

    implemented = set(catalogue()["codes"])
    named = spec_named_codes()
    print("I1  implemented codes :", len(implemented), sorted(implemented))
    print("I1  spec-named codes  :", len(named), sorted(named))
    problems: list[str] = []
    missing = named - implemented
    extra = implemented - named
    if missing:
        problems.append(f"I1: spec names codes this build does not implement: {sorted(missing)}")
    if extra:
        problems.append(f"I1: this build implements codes the spec does not name: {sorted(extra)}")
    print(f"I1  set equality      : {'PASS' if not problems else 'FAIL'}")
    return problems


# ---------------------------------------------------------------------------------------
# I5 -- text and JSON carry the same findings in the same order, in every mode
# ---------------------------------------------------------------------------------------


def tuples_from_text(text: str) -> list[tuple[str, str, str]]:
    """(code, file, field) in the order the human renderer emitted them."""
    found: list[tuple[str, str, str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = _LOCATOR.match(line)
        if not match:
            continue
        _severity, code, _subject, where = match.groups()
        file = where.rsplit(":", 1)[0] if re.search(r":\d+$", where) else where
        field = ""
        for follow in lines[index + 1 : index + 6]:
            field_match = _FIELD.match(follow)
            if field_match:
                field = field_match.group(1)
                break
        found.append((code, file, field))
    return found


def tuples_from_json(payload: str) -> list[tuple[str, str, str]]:
    return [(item["code"], item["file"], item["field"]) for item in json.loads(payload)]


def check_i5(targets: list[Path]) -> list[str]:
    problems: list[str] = []
    for target in targets:
        text = run_cli(str(target))
        payload = run_cli("--json", str(target))
        from_text = tuples_from_text(text.stdout)
        from_json = tuples_from_json(payload.stdout)
        label = target.name if target != PACKS else f"{target.name}/  (directory mode)"
        ok = from_text == from_json
        print(f"I5  {label:<34} text={len(from_text):>3} json={len(from_json):>3} "
              f"identical={'yes' if ok else 'NO'}")
        if not ok:
            problems.append(f"I5: {target} text and json differ\n  text={from_text}\n  json={from_json}")
        if target == PACKS:
            unattributed = [
                item for item in json.loads(payload.stdout) if not item.get("pack")
            ]
            if unattributed:
                problems.append(f"I5: {len(unattributed)} directory-mode records carry no pack attribution")
            else:
                print(f"I5  {'directory-mode pack attribution':<34} every record names its pack")
    return problems


# ---------------------------------------------------------------------------------------


def check_matrix() -> tuple[list[str], set[str], set[str]]:
    problems: list[str] = []
    covered: set[str] = set()
    width = max(len(name) for name in MATRIX)
    print(f"{'fixture'.ljust(width)}  want  got  codes raised")
    for name, (wanted, wanted_exit) in MATRIX.items():
        proc = run_cli("--json", str(PACKS / name))
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
            problems.append(f"{name}: did not raise {sorted(missing)}")
        if proc.returncode != wanted_exit:
            problems.append(f"{name}: exit {proc.returncode}, expected {wanted_exit}")
    return problems, covered, set()


def main() -> int:
    problems, covered, _ = check_matrix()
    print()
    problems += check_i1()
    print()
    problems += check_i5([PACKS / "minimal_valid", PACKS / "warn_heuristics", REPO / "backend/packs/riverside_grocery", PACKS])
    print()

    sys.path.insert(0, str(REPO / "backend"))
    from app.casepack.validate import catalogue  # noqa: E402

    declared = set(catalogue()["codes"])
    untested = declared - covered - NO_FIXTURE
    if untested:
        problems.append(f"codes declared but never exercised by a fixture: {sorted(untested)}")

    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"all {len(MATRIX)} fixtures behave as named; "
          f"{len(covered)} of {len(declared)} codes exercised, {sorted(NO_FIXTURE)} recorded as unfixturable")
    print("I1 set-equal against the spec; I5 identical in single-pack and directory mode")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

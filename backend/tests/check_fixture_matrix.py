#!/usr/bin/env python3
"""The auditor's re-run artifact for module 1.2 — spec v1.2 section 9.2.

    python3 backend/tests/check_fixture_matrix.py

Exits 0 when everything holds, 1 otherwise. No test framework, so no new dependency.

Three things are asserted here, not one:

  MATRIX  every fixture pack raises the code it is named for, DOES NOT raise the codes it
          is named for not raising, returns the exit code it claims, and no code the spec
          names is left without a fixture. This is spec section 8 step 5: a code with no
          fixture is untested.

          The FORBIDDEN column is new in rework-2, and it is the point of that packet.
          Every item in it changes what the validator says about pack shapes that do not
          exist yet -- a presence watch rule, an entity held by a platform service, an
          optional section created before it is authored. A suite that only proves errors
          still fire cannot see any of it, so each of those items ships as a PAIR: the
          illegal shape, which must still fire, and the newly legal shape, which must now
          be silent. `ANY` forbids every code, which is what "passes clean" means.

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

#: forbid every code -- the fixture must produce no finding at all
ANY = "*"

# fixture -> (codes it must raise, codes it must NOT raise, exit code it must return)
MATRIX: dict[str, tuple[set[str], set[str], int]] = {
    "minimal_valid": (set(), {ANY}, 0),
    "broken_E00": ({"E00"}, set(), 1),
    "broken_E01": ({"E01"}, set(), 1),
    "broken_E02": ({"E02"}, set(), 1),
    "broken_E03": ({"E03"}, set(), 1),
    "broken_E04": ({"E04"}, set(), 1),
    "broken_E05": ({"E05"}, set(), 1),
    "broken_E06": ({"E06"}, set(), 1),
    "broken_E07": ({"E07"}, set(), 1),
    "broken_E08": ({"E08"}, set(), 1),
    "broken_E09": ({"E09"}, set(), 1),
    "broken_E10": ({"E10"}, set(), 1),
    "broken_E11": ({"E11"}, set(), 1),
    "broken_E12": ({"E12"}, {"E20"}, 1),
    "broken_E13": ({"E13"}, set(), 1),
    "broken_E14": ({"E14"}, set(), 1),
    # ---- 1.2-RA-003: policy value vocabulary ---------------------------------------
    "broken_E15": ({"E15"}, set(), 1),
    # E15's default variant: a malformed DEFAULT (not an option). Same code, but it must
    # locate the `default` field, not `options` -- finding 1.2-VR-002, asserted below.
    "broken_E15_default": ({"E15"}, set(), 1),
    "broken_E16": ({"E16"}, set(), 1),
    # broken_E17's default is outside its options, which makes models.py refuse the pack.
    # E00 is forbidden here: the whole point of E17 is that this no longer collapses into
    # the opaque unreadable-pack path (finding 1.2-RA-003).
    "broken_E17": ({"E17"}, {"E00"}, 1),
    # Aggregate diagnostics: a bad policy default AND an independent weight error. Both must
    # surface -- one invalid default must not hide E03 behind a single E00 (1.2-RA-003).
    "broken_policy_aggregate": ({"E17", "E03"}, {"E00"}, 1),
    # ---- 1.2-RA-001: obligation references -----------------------------------------
    "broken_E24": ({"E24"}, set(), 1),
    "broken_E25": ({"E25"}, set(), 1),
    "broken_E26": ({"E26"}, set(), 1),
    # E26 when the referenced policy declares NO options -- permissive_value names nothing
    # (finding 1.2-VR-001). Must fire, not pass clean.
    "broken_E26_no_options": ({"E26"}, set(), 1),
    "broken_E27": ({"E27"}, set(), 1),
    "broken_E28": ({"E28"}, set(), 1),
    # The paired valid half for the policy-vocab and obligation fixtures: a pack whose policy
    # declares options and whose obligation resolves against every one of them, clean.
    "ok_obligations_valid": (set(), {ANY}, 0),
    # ---- 1.2-RA-002: W01 sees the by_decision preference shape ----------------------
    "warn_W01_by_decision": ({"W01"}, set(), 0),
    "broken_E20": ({"E20"}, set(), 1),
    "broken_E20_mute": ({"E20", "E12"}, set(), 1),
    "broken_E21": ({"E21"}, {"E12", "E20"}, 1),
    "broken_E22": ({"E22"}, set(), 1),
    "broken_E23": ({"E23"}, set(), 1),
    "broken_I3": ({"I3"}, set(), 1),
    "warn_W01": ({"W01"}, set(), 0),
    "warn_heuristics": ({"W02", "W03", "W04", "W05", "W06", "W07"}, set(), 0),
    # ---- rework-2's four pairs, plus the one-line loader fix -----------------------
    # 3.1 E12 exempts presence · 3.2 E20 counts a presence rule as coverage.
    #     broken_E20_mute and broken_E12 above are the illegal halves: a THRESHOLD rule
    #     carrying no threshold, which stays an error and stays mute.
    "ok_presence_rule": (set(), {ANY}, 0),
    # 3.3 _raisable consults metric_kind. broken_E21 above is the unreachable half.
    #     ok_presence_rule is also the reachable half -- its deck waits on the presence
    #     rule at `critical` and E21 is silent. This fixture is decision 10's other edge:
    #     a presence rule reaches critical and NEVER warning, so an event waiting for a
    #     warning from one must still be reported.
    "broken_E21_presence_warning": ({"E21"}, {"E12", "E20"}, 1),
    # 3.4 Lens.owned unions the platform services. broken_E02 above is the unowned half:
    #     an entity nothing holds at any level, which stays an error.
    "ok_service_owns_entity": (set(), {ANY}, 0),
    # 3.5 W08. Seven cards for four rounds, so W05 is silent and only W08 can see that
    #     one strategy draws nothing -- CG-2's shape. minimal_valid is the silent half.
    "broken_W08": ({"W08"}, {"W05"}, 0),
    # 3.6 finding 1.1-r2-001: a comment-only optional section is "nothing authored yet",
    #     not a dead pack. minimal_valid, which has no such file at all, is the other half.
    "ok_obligations_empty": (set(), {ANY}, 0),
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


# fixture -> (code, the suffix its finding's `field` must end with). Finding 1.2-VR-002: a
# finding must locate the field an author should edit, so the code alone is not enough -- a
# malformed default reported against `options` sends the author to the wrong place.
FIELD_LOCATORS: list[tuple[str, str, str]] = [
    ("broken_E15", "E15", ".options"),
    ("broken_E15_default", "E15", ".default"),
    ("broken_E26", "E26", ".permissive_value"),
    ("broken_E26_no_options", "E26", ".permissive_value"),
]


def check_field_locators() -> list[str]:
    problems: list[str] = []
    for name, code, suffix in FIELD_LOCATORS:
        proc = run_cli("--json", str(PACKS / name))
        findings = json.loads(proc.stdout) if proc.stdout.strip() else []
        hits = [item for item in findings if item["code"] == code]
        ok = bool(hits) and all(str(item["field"]).endswith(suffix) for item in hits)
        print(f"FIELD  {name:<26} {code} field endswith '{suffix}'   {'PASS' if ok else 'FAIL'}")
        if not ok:
            problems.append(
                f"{name}: {code} field {[item['field'] for item in hits]} does not end with {suffix!r}"
            )
    return problems


def check_matrix() -> tuple[list[str], set[str], set[str]]:
    problems: list[str] = []
    covered: set[str] = set()
    width = max(len(name) for name in MATRIX)
    print(f"{'fixture'.ljust(width)}  want  got  must raise / must not raise / codes raised")
    for name, (wanted, forbidden, wanted_exit) in MATRIX.items():
        proc = run_cli("--json", str(PACKS / name))
        findings = json.loads(proc.stdout) if proc.stdout.strip() else []
        raised = {finding["code"] for finding in findings}
        covered |= raised
        missing = wanted - raised
        leaked = raised if ANY in forbidden else raised & forbidden
        ok = not missing and not leaked and proc.returncode == wanted_exit
        print(
            f"{name.ljust(width)}  {wanted_exit:>4}  {proc.returncode:>3}  "
            f"+[{','.join(sorted(wanted)) or '-'}] "
            f"-[{','.join(sorted(forbidden)) or '-'}] "
            f"got[{','.join(sorted(raised)) or '-'}]   {'PASS' if ok else 'FAIL'}"
        )
        if missing:
            problems.append(f"{name}: did not raise {sorted(missing)}")
        if leaked:
            problems.append(f"{name}: raised {sorted(leaked)}, which this fixture forbids")
        if proc.returncode != wanted_exit:
            problems.append(f"{name}: exit {proc.returncode}, expected {wanted_exit}")
    return problems, covered, set()


def main() -> int:
    problems, covered, _ = check_matrix()
    print()
    problems += check_field_locators()
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

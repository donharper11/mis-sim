"""Casepack validator: one producer of findings, two renderers, one exit code."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from app.casepack import checks as base_checks
from app.casepack.loader import SECTION_FILES, CasepackLoadError, load_casepack
from app.casepack.models import Casepack

# --------------------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------------------

#: highest schema_version this build knows how to read (spec 5.1, E11)
SUPPORTED_SCHEMA_VERSION = 1

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

#: ARCHETYPES and REVIEW_AREAS now live in checks.py beside ACTION_TYPES -- spec v1.2
#: section 3 decision 9. They are schema vocabulary, and 1.4/1.5 will want them.

#: W01 threshold. design/01 section 4 records `business_process_mapping` rows 71-76 --
#: six stakeholders sharing one ideal_value and one weight -- as the shape W01 exists to
#: catch, so six identical rows is the smallest group that must fire.
W01_MIN_IDENTICAL_ROWS = 6

#: W02 threshold, taken verbatim from spec 5.3 ("no strategy weights above 0.05").
W02_MIN_WEIGHT = 0.05

_SECTION_FILE = {
    "metadata": "pack.yaml",
    "strategies": "strategies.yaml",
    "capabilities": "capabilities.yaml",
    "catalog": "catalog.yaml",
    "platform": "platform.yaml",
    "entities": "entities.yaml",
    "watch_rules": "watch_rules.yaml",
    "events": "events.yaml",
    "stakeholders": "stakeholders.yaml",
    "policies": "policies.yaml",
    "questions": "questions.yaml",
    "labels": "labels.yaml",
}

_LIST_SECTIONS = (
    "strategies",
    "capabilities",
    "catalog",
    "entities",
    "watch_rules",
    "events",
    "stakeholders",
    "policies",
    "questions",
)

_MESSAGES_PATH = Path(__file__).with_name("validate_messages.yaml")

_JSON_FLAG = "--json"


# --------------------------------------------------------------------------------------
# message catalogue
# --------------------------------------------------------------------------------------

_catalogue_cache: dict[str, Any] | None = None


def catalogue() -> dict[str, Any]:
    """Load validate_messages.yaml once."""
    global _catalogue_cache
    if _catalogue_cache is None:
        with _MESSAGES_PATH.open("r", encoding="utf-8") as handle:
            _catalogue_cache = yaml.safe_load(handle)
    return _catalogue_cache


def _render(key: str, **params: Any) -> str:
    return str(catalogue()["render"][key]).format(**params)


def _subject(section: str) -> str:
    return str(catalogue()["subjects"][section])


def _reason(key: str, **params: Any) -> str:
    return str(catalogue()["reasons"][key]).format(**params)


def error_codes() -> list[str]:
    """Every code this validator can raise at ERROR severity."""
    codes = catalogue()["codes"]
    return sorted(code for code, entry in codes.items() if entry["severity"] == ERROR)


# --------------------------------------------------------------------------------------
# Finding
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One thing wrong with a pack. A Finding without a fix cannot be constructed."""

    code: str
    severity: str
    subject: str
    file: str
    field: str
    message: str
    fix: str
    line: int | None = None
    pack: str | None = None

    def __post_init__(self) -> None:
        # spec 3.1: I1 holds because a fix-less ERROR is unconstructible, not discouraged
        if not self.fix.strip():
            raise ValueError(f"{self.code}: fix is empty")
        if not self.file.strip():
            raise ValueError(f"{self.code}: file is empty")
        if not self.field.strip():
            raise ValueError(f"{self.code}: field is empty")
        if not self.subject.strip():
            raise ValueError(f"{self.code}: subject is empty")

    def with_pack(self, pack: str) -> Finding:
        return replace(self, pack=pack)

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "pack": self.pack,
            "subject": self.subject,
            "file": self.file,
            "line": self.line,
            "field": self.field,
            "message": self.message,
            "fix": self.fix,
        }


def make_finding(
    code: str,
    relative: str,
    field: str,
    line: int | None = None,
    variant: str | None = None,
    **params: Any,
) -> Finding:
    entry = catalogue()["variants"][variant] if variant else catalogue()["codes"][code]
    return Finding(
        code=code,
        severity=catalogue()["codes"][code]["severity"],
        subject=str(entry["subject"]).format(**params),
        file=relative,
        field=field,
        message=str(entry["message"]).format(**params),
        fix=str(entry["fix"]).format(**params),
        line=line,
    )


# --------------------------------------------------------------------------------------
# source location -- so a finding can name file AND line, per spec 5.4
# --------------------------------------------------------------------------------------


class PackSource:
    """Reads the pack's raw text so findings can cite a line number."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._cache: dict[str, list[str]] = {}

    def lines(self, relative: str) -> list[str]:
        if relative not in self._cache:
            path = self._root / relative
            try:
                self._cache[relative] = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                self._cache[relative] = []
        return self._cache[relative]

    def find(self, relative: str, pattern: str) -> int | None:
        matcher = re.compile(pattern)
        for index, line in enumerate(self.lines(relative), start=1):
            if matcher.search(line):
                return index
        return None

    def key_line(self, relative: str, key: str) -> int | None:
        return self.find(relative, rf"\bkey:\s*['\"]?{re.escape(key)}['\"]?\s*(?:[,}}]|$)")

    def field_line(self, relative: str, key: str, name: str) -> int | None:
        start = self.key_line(relative, key)
        if start is None:
            return None
        matcher = re.compile(rf"\b{re.escape(name)}\s*:")
        for offset, line in enumerate(self.lines(relative)[start - 1 :]):
            if matcher.search(line):
                return start + offset
        return start

    def token_line(self, relative: str, token: str) -> int | None:
        return self.find(relative, rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])")


# --------------------------------------------------------------------------------------
# raw stage -- runs before pydantic, because models.py rejects some packs outright
# --------------------------------------------------------------------------------------


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_raw(root: Path) -> tuple[dict[str, Any], list[Finding]]:
    """Parse every pack file as plain YAML. Unreadable files become E00 findings."""
    raw: dict[str, Any] = {}
    findings: list[Finding] = []
    for section, relative in _SECTION_FILE.items():
        path = root / relative
        if not path.exists():
            findings.append(
                make_finding("E00", relative, section, detail=_missing(relative), file=relative)
            )
            continue
        try:
            raw[section] = _read_yaml(path) or {}
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            findings.append(
                make_finding(
                    "E00",
                    relative,
                    section,
                    line=None if mark is None else mark.line + 1,
                    detail=_unparseable(relative),
                    file=relative,
                )
            )
    prefs = root / "preferences"
    raw["preferences"] = {}
    if not prefs.is_dir():
        findings.append(
            make_finding("E00", "preferences", "preferences", detail=_missing("preferences"), file="preferences")
        )
    else:
        for path in sorted(prefs.glob("*.yaml")):
            try:
                raw["preferences"][path.stem] = _read_yaml(path) or {}
            except yaml.YAMLError:
                relative = f"preferences/{path.name}"
                findings.append(
                    make_finding("E00", relative, path.stem, detail=_unparseable(relative), file=relative)
                )
    return raw, findings


def _missing(relative: str) -> str:
    return _render("detail_missing", file=relative)


def _unparseable(relative: str) -> str:
    return _render("detail_unparseable", file=relative)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def check_duplicate_keys(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E10 -- the same key declared twice in one collection."""
    findings: list[Finding] = []
    collections: list[tuple[str, str, list[Any]]] = [
        (_SECTION_FILE[name], name, _as_list(raw.get(name))) for name in _LIST_SECTIONS
    ]
    platform = raw.get("platform")
    if isinstance(platform, dict):
        for name in ("services", "support_tiers", "integration_tiers"):
            collections.append(("platform.yaml", f"platform.{name}", _as_list(platform.get(name))))
    for relative, field, rows in collections:
        counts: dict[str, int] = {}
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("key"), str):
                counts[row["key"]] = counts.get(row["key"], 0) + 1
        for key, count in counts.items():
            if count > 1:
                findings.append(
                    make_finding(
                        "E10",
                        relative,
                        f"{field}.{key}",
                        line=source.key_line(relative, key),
                        key=key,
                        count=count,
                        file=relative,
                    )
                )
    return findings


def check_schema_version(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E11 -- the pack is newer than this validator."""
    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        return []
    given = metadata.get("schema_version")
    if isinstance(given, int) and given > SUPPORTED_SCHEMA_VERSION:
        return [
            make_finding(
                "E11",
                "pack.yaml",
                "schema_version",
                line=source.find("pack.yaml", r"^schema_version\s*:"),
                given=given,
                supported=SUPPORTED_SCHEMA_VERSION,
            )
        ]
    return []


def check_weights_raw(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E03 from raw YAML -- reached only when models.py refused to build the pack."""
    findings: list[Finding] = []
    for row in _as_list(raw.get("strategies")):
        if not isinstance(row, dict):
            continue
        weights = row.get("capability_weights")
        key = row.get("key")
        if not isinstance(weights, dict) or not isinstance(key, str):
            continue
        total = sum(float(value) for value in weights.values())
        if abs(total - 1.0) > 0.001:
            findings.append(_weight_finding(key, total, source))
    return findings


def _weight_finding(key: str, total: float, source: PackSource) -> Finding:
    return make_finding(
        "E03",
        "strategies.yaml",
        f"{key}.capability_weights",
        line=source.field_line("strategies.yaml", key, "capability_weights"),
        strategy=key,
        total=f"{total:.3f}",
    )


def check_demand_raw(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E04 from raw YAML -- reached only when models.py refused to build the pack."""
    metadata = raw.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("rounds"), int):
        return []
    rounds = metadata["rounds"]
    findings: list[Finding] = []
    for row in _as_list(raw.get("capabilities")):
        if not isinstance(row, dict):
            continue
        curve = row.get("demand_curve")
        key = row.get("key")
        if not isinstance(curve, list) or not isinstance(key, str):
            continue
        if len(curve) != rounds:
            findings.append(_demand_finding(key, key, len(curve), rounds, source))
    return findings


def _demand_finding(key: str, label: str, given: int, rounds: int, source: PackSource) -> Finding:
    return make_finding(
        "E04",
        "capabilities.yaml",
        f"{key}.demand_curve",
        line=source.field_line("capabilities.yaml", key, "demand_curve"),
        capability=label,
        given=given,
        rounds=rounds,
    )


def _show(value: Any) -> str:
    """A readable rendering of an option value for a finding message -- empty and
    non-string values would otherwise vanish into the copy."""
    if isinstance(value, str):
        return value if value else "(empty)"
    return repr(value)


def check_policy_vocab(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E15..E17 -- a policy's value vocabulary is malformed, checked on RAW YAML.

    Runs before the pydantic load (like check_weights_raw / check_demand_raw), and for the
    same reason: a policy whose `default` is not among its `options` makes models.py refuse
    to build the whole pack (`PolicyOption.default_is_a_declared_option`). That refusal was
    reaching the instructor as a single opaque E00 that hid every other finding in the pack
    (finding 1.2-RA-003). Reported here as precise codes, these co-report with the other
    raw-stage checks (E03, E04, E10, E11, E15, E16) instead of collapsing into E00.

    E15/E16 are not model-enforced at all -- `options` is a plain `list[str]` -- so they are
    the validator's only line on empty, non-snake, or duplicated option vocabularies.
    """
    findings: list[Finding] = []
    for row in _as_list(raw.get("policies")):
        if not isinstance(row, dict):
            continue
        key = row.get("key")
        if not isinstance(key, str):
            continue
        options = row.get("options")
        options = options if isinstance(options, list) else []
        default = row.get("default")
        key_line = source.key_line("policies.yaml", key)

        # E15 -- an option value that is not a valid snake_case key (an empty string fails
        # the same rule). Options must be machine keys the ordering in CONTRACTS.md
        # `PolicyOption.options` can index.
        for opt in options:
            if not (isinstance(opt, str) and base_checks.SNAKE_RE.fullmatch(opt)):
                findings.append(
                    make_finding(
                        "E15",
                        "policies.yaml",
                        f"{key}.options",
                        line=key_line,
                        policy=key,
                        value=_show(opt),
                        file="policies.yaml",
                    )
                )
        # E15, default variant -- a malformed default is reported against `default`, not
        # `options`, with a default-specific message and fix (finding 1.2-VR-002). Lumping it
        # into the options list pointed the author at the wrong field.
        default_malformed = default is not None and not (
            isinstance(default, str) and base_checks.SNAKE_RE.fullmatch(default)
        )
        if default_malformed:
            findings.append(
                make_finding(
                    "E15",
                    "policies.yaml",
                    f"{key}.default",
                    line=source.field_line("policies.yaml", key, "default"),
                    variant="E15_default",
                    policy=key,
                    value=_show(default),
                    file="policies.yaml",
                )
            )

        # E16 -- the same value listed twice in one options vocabulary
        seen: set[str] = set()
        duplicated: list[str] = []
        for opt in options:
            if isinstance(opt, str):
                if opt in seen and opt not in duplicated:
                    duplicated.append(opt)
                seen.add(opt)
        for dup in duplicated:
            findings.append(
                make_finding(
                    "E16",
                    "policies.yaml",
                    f"{key}.options",
                    line=key_line,
                    policy=key,
                    value=dup,
                    file="policies.yaml",
                )
            )

        # E17 -- a WELL-FORMED default outside its own options. Mirrors the models.py load
        # failure (options non-empty, default not None, default not a member), so it reaches
        # the instructor as E17 rather than the opaque E00 the failure used to collapse to. A
        # malformed default is E15's default variant above, not this -- the snake guard keeps
        # the two from both firing on one default (finding 1.2-VR-002).
        string_options = [opt for opt in options if isinstance(opt, str)]
        if (
            string_options
            and isinstance(default, str)
            and base_checks.SNAKE_RE.fullmatch(default)
            and default not in string_options
        ):
            findings.append(
                make_finding(
                    "E17",
                    "policies.yaml",
                    f"{key}.default",
                    line=source.field_line("policies.yaml", key, "default"),
                    policy=key,
                    default=_show(default),
                    options=", ".join(string_options),
                    file="policies.yaml",
                )
            )
    return findings


def check_precondition_vocab_raw(raw: dict[str, Any], source: PackSource) -> list[Finding]:
    """E29, vocabulary variant -- a precondition field set outside its closed vocabulary.

    Runs on RAW YAML, before the pydantic load, for exactly the reason `check_policy_vocab`
    does. `placement` and `severity` are `Literal` fields on `EventPrecondition`, so an
    out-of-vocabulary value makes `models.py` refuse the WHOLE pack, and that refusal
    reached the instructor as a bare `E00 "This pack could not be read"` naming no field,
    against an `events.yaml` that parsed perfectly and whose one wrong value the author
    could not see (finding `B7`; `GOVERNANCE 4.10` -- users may not see our errors).

    Reported as `E29` rather than a new code: `E29` is already *"every event precondition
    has one known, exact field shape"*, a value outside a closed vocabulary is that same
    defect, and inventing a code here would break `I1`'s set equality against the 1.2 spec.
    The vocabularies are read off the model in `checks.PRECONDITION_VOCABULARIES` -- this
    check must not become a second home for them.
    """
    findings: list[Finding] = []
    for event in _as_list(raw.get("events")):
        if not isinstance(event, dict):
            continue
        key = event.get("key")
        if not isinstance(key, str):
            continue
        line = source.field_line("events.yaml", key, "preconditions")
        for index, condition in enumerate(_as_list(event.get("preconditions"))):
            if not isinstance(condition, dict):
                continue
            for field_name, allowed in base_checks.PRECONDITION_VOCABULARIES.items():
                value = condition.get(field_name)
                if value is None or value in allowed:
                    continue
                findings.append(
                    make_finding(
                        "E29",
                        "events.yaml",
                        f"{key}.preconditions.{index}.{field_name}",
                        line=line,
                        variant="E29_vocab",
                        event=key,
                        number=index + 1,
                        field_name=field_name,
                        value=_show(value),
                        allowed=", ".join(allowed),
                    )
                )
    return findings


#: The pydantic error types that mean "a value outside a closed vocabulary": `Literal`
#: fields report `literal_error`, `StrEnum` fields report `enum`. Both carry the offending
#: input and the expected set in the error record, which is all E18 needs.
_CLOSED_VOCAB_ERRORS = frozenset({"literal_error", "enum"})


def _readable_field(loc: tuple[Any, ...], raw: dict[str, Any]) -> str:
    """Turn a pydantic error `loc` into a field path an author can find in their file.

    `('entities', 3, 'sensitivity')` becomes `<row-key>.sensitivity` when the raw row at
    index 3 carries a `key`, and `entities.3.sensitivity` when it does not. The section
    itself is dropped -- E18 already names the file it maps to.
    """
    parts: list[str] = []
    cursor: Any = raw.get(str(loc[0])) if isinstance(raw, dict) else None
    for step in loc[1:]:
        if isinstance(step, int) and isinstance(cursor, list) and step < len(cursor):
            element = cursor[step]
            if isinstance(element, dict) and isinstance(element.get("key"), str):
                parts.append(element["key"])
            else:
                parts.append(str(step))
            cursor = element
        else:
            parts.append(str(step))
            cursor = cursor.get(step) if isinstance(cursor, dict) else None
    return ".".join(parts) if parts else str(loc[-1]) if loc else "casepack"


def check_closed_vocab_load(
    exc: CasepackLoadError, raw: dict[str, Any], source: PackSource
) -> list[Finding]:
    """E18 -- every closed model vocabulary reports the field, not a blanket E00.

    A `Literal` or `StrEnum` field set outside its vocabulary makes `models.py` refuse the
    whole pack, and that refusal used to reach the instructor as a single opaque
    `E00 "This pack could not be read"` naming no field, against a file that parsed
    perfectly (finding CU-001; `GOVERNANCE 4.10`). `check_policy_vocab` and
    `check_precondition_vocab_raw` each pre-empt ONE such family before the load; this
    closes the CLASS by reading pydantic's own error report -- which knows the exact field
    path, the bad value and the expected set for every enum failure, present or future,
    however deeply nested -- so no closed vocabulary can collapse to E00 again.

    The vocabularies are never restated here: `expected` comes straight off the pydantic
    error, so this cannot become a second home for values the model already owns.
    """
    validation_error = exc.validation_error
    if validation_error is None:
        return []
    findings: list[Finding] = []
    for error in validation_error.errors():
        if error.get("type") not in _CLOSED_VOCAB_ERRORS:
            continue
        loc = tuple(error.get("loc", ()))
        if not loc:
            continue
        # Precondition placement/severity are closed vocabularies too, but they are already
        # pre-empted before the load by `check_precondition_vocab_raw` as `E29_vocab` -- the
        # event engine's own contract. E18 must not also fire on them, or one bad value would
        # report twice under two codes.
        if "preconditions" in loc and str(loc[-1]) in base_checks.PRECONDITION_VOCABULARIES:
            continue
        section = str(loc[0])
        relative = SECTION_FILES.get(section, section)
        field = _readable_field(loc, raw)
        leaf = str(loc[-1])
        value = error.get("input")
        allowed = str((error.get("ctx") or {}).get("expected") or error.get("msg", ""))
        findings.append(
            make_finding(
                "E18",
                relative,
                field,
                line=source.token_line(relative, str(value)),
                path=field,
                field_leaf=leaf,
                value=_show(value),
                allowed=allowed,
                file=relative,
            )
        )
    return findings


# --------------------------------------------------------------------------------------
# typed stage helpers
# --------------------------------------------------------------------------------------


def _can_raise(rule: Any) -> bool:
    """Can this watch rule ever put a signal on the ledger?

    Rework-2 items 3.2 and 3.3, from 1.5 spec section 5.1a and decision 10. There are two
    evaluation paths, not one:

      presence   the metric is a boolean. It raises at `critical` the moment the condition
                 is present, and carries no threshold at all -- so it can always raise, and
                 the absence of thresholds is its correct shape rather than a defect.
      threshold  the metric is a float. It can raise only across a threshold that has
                 actually been authored.
    """
    if rule.metric_kind == "presence":
        return True
    return rule.warn_above is not None or rule.critical_above is not None


def _raisable_severities(rule: Any) -> set[str]:
    """The severities this rule can actually attain.

    Rework-2 item 3.3, finding 1.1-r2-006. 1.5 decision 10: a presence condition is true or
    it is not, so it reaches `critical` and NEVER `warning` -- there is no magnitude to be
    mildly concerned about and no tier below critical to fall to.
    """
    if rule.metric_kind == "presence":
        return {"critical"}
    severities: set[str] = set()
    if rule.warn_above is not None:
        severities.add("warning")
    if rule.critical_above is not None:
        severities.add("critical")
    return severities


class Lens:
    """Derived views over a loaded pack, shared by the typed checks."""

    def __init__(self, pack: Casepack, source: PackSource) -> None:
        self.pack = pack
        self.source = source
        self.labels = pack.labels.model_dump()
        self.capability_keys = {item.key for item in pack.capabilities}
        self.entity_levels: dict[str, list[str]] = {
            entity.key: list(entity.levels_of_detail) for entity in pack.entities
        }
        self.watched = {rule.capability for rule in pack.watch_rules}
        self.rules = {rule.key: rule for rule in pack.watch_rules}
        # spec v1.2 section 3 decision 7: a rule carrying neither threshold can never fire,
        # so it does not count as watching anything. Rework-2 item 3.1 narrows that to
        # `threshold` rules only -- 1.5 section 5.1a makes carrying no threshold the CORRECT
        # shape for a `presence` rule, so E12 must exempt them or it fires on exactly the
        # rules 1.5 decision 8 makes legal.
        self.thresholdless = [
            rule
            for rule in pack.watch_rules
            if rule.metric_kind == "threshold"
            and rule.warn_above is None
            and rule.critical_above is None
        ]
        # Rework-2 item 3.2: E20's predicate is "no watch rule that CAN RAISE A SIGNAL".
        # A presence rule raises at critical with no threshold to cross (1.5 decision 10),
        # so it is coverage; a threshold rule is coverage only once it carries a threshold.
        self.mute_rules = [rule for rule in pack.watch_rules if not _can_raise(rule)]
        self.signal_covered = {rule.capability for rule in pack.watch_rules if _can_raise(rule)}
        self.catalog_keys = {item.key for item in pack.catalog}
        self.strategy_keys = {strategy.key for strategy in pack.strategies}
        # A capability IS a value chain activity (1.1 O1); `chain_position` is authored as
        # "primary/operations", so the activity vocabulary is the segment after the slash.
        self.chain_positions = {
            capability.chain_position.split("/")[-1] for capability in pack.capabilities
        }
        self.filled_roles = {role for item in pack.catalog for role in item.roles_filled}
        self.filled_roles |= {
            role for service in pack.platform.services for role in service.roles_filled
        }
        self.required_roles = {
            role for capability in pack.capabilities for role in capability.required_roles
        }
        # Rework-2 item 3.4, from 1.1 rework-2 R2. `owned` is what E02 and E23 consult, and
        # it was built from pack.catalog alone -- so PlatformService.owns_entities was inert
        # and no pack could satisfy an entity requirement through a shared platform service.
        # The asymmetry was visible two lines up: `filled_roles` already unions the services.
        self.owned: dict[str, int] = {}
        for item in [*pack.catalog, *pack.platform.services]:
            for held in item.owns_entities:
                rank = self.rank(held.entity, held.level_of_detail)
                if rank is None:
                    continue
                self.owned[held.entity] = max(self.owned.get(held.entity, -1), rank)

    def rank(self, entity: str, level: str) -> int | None:
        levels = self.entity_levels.get(entity)
        if levels is None or level not in levels:
            return None
        return levels.index(level)

    def satisfiable(self, entity: str, level: str) -> bool:
        needed = self.rank(entity, level)
        if needed is None:
            return False
        return self.owned.get(entity, -1) >= needed

    def label(self, section: str, key: str) -> str:
        return str(self.labels.get(section, {}).get(key) or key)


# --------------------------------------------------------------------------------------
# typed stage -- structural (E01, E02, E05..E09) plus the inherited 1.1 invariants
# --------------------------------------------------------------------------------------


def check_inherited(lens: Lens) -> list[Finding]:
    """Wraps 1.1's checks.py -- I3->I3, I4->E01, I5->E03, I6->E05, I7->E04, I8->I8."""
    results = base_checks.run_all_checks(lens.pack)
    findings: list[Finding] = []

    for key in results["I3"]:
        findings.append(
            make_finding("I3", "labels.yaml", f"key.{key}", line=None, key=key)
        )

    for entry in results["I4"]:
        capability, _, role = entry.partition(".")
        findings.append(
            make_finding(
                "E01",
                "capabilities.yaml",
                f"{capability}.required_roles.{role}",
                line=lens.source.field_line("capabilities.yaml", capability, "required_roles"),
                capability=lens.label("capabilities", capability),
                role=lens.label("roles", role),
                role_key=role,
            )
        )

    for entry in results["I5"]:
        key, _, total = entry.rpartition(":")
        findings.append(_weight_finding(key, float(total), lens.source))

    for entry in results["I6"]:
        rule, _, action = entry.partition(".")
        findings.append(
            make_finding(
                "E05",
                "watch_rules.yaml",
                f"{rule}.cleared_by.{action}",
                line=lens.source.field_line("watch_rules.yaml", rule, "cleared_by"),
                rule_name=lens.label("watch_rules", rule),
                rule=rule,
                action=action,
                known=", ".join(sorted(base_checks.ACTION_TYPES)),
            )
        )

    for entry in results["I7"]:
        key, _, given = entry.rpartition(":")
        findings.append(
            _demand_finding(
                key,
                lens.label("capabilities", key),
                int(given),
                lens.pack.metadata.rounds,
                lens.source,
            )
        )

    for _ in results["I8"]:
        findings.append(make_finding("I8", "pack.yaml", "casepack"))

    return findings


def check_entity_detail(lens: Lens) -> list[Finding]:
    """E02 -- a capability needs information at a detail nothing can hold."""
    findings: list[Finding] = []
    for capability in lens.pack.capabilities:
        for need in capability.required_entities:
            if not lens.satisfiable(need.entity, need.min_level_of_detail):
                findings.append(
                    make_finding(
                        "E02",
                        "capabilities.yaml",
                        f"{capability.key}.required_entities.{need.entity}",
                        line=lens.source.field_line(
                            "capabilities.yaml", capability.key, "required_entities"
                        ),
                        capability=lens.label("capabilities", capability.key),
                        entity_name=lens.label("entities", need.entity),
                        entity=need.entity,
                        level=need.min_level_of_detail,
                    )
                )
    return findings


def check_event_references(lens: Lens) -> list[Finding]:
    """E06 -- an event waits on something the pack does not declare."""
    findings: list[Finding] = []
    for event in lens.pack.events:
        for condition in event.preconditions:
            unknown: list[str] = []
            if condition.signal is not None and condition.signal not in lens.rules:
                unknown.append(condition.signal)
            if condition.capability is not None and condition.capability not in lens.capability_keys:
                unknown.append(condition.capability)
            for reference in unknown:
                findings.append(
                    make_finding(
                        "E06",
                        "events.yaml",
                        f"{event.key}.preconditions.{reference}",
                        line=lens.source.field_line("events.yaml", event.key, "preconditions"),
                        event=event.key,
                        reference=reference,
                    )
                )
    return findings


def check_precondition_shapes(lens: Lens) -> list[Finding]:
    """E29 -- every event precondition has one known, exact field shape."""
    findings: list[Finding] = []
    known = ", ".join(sorted(base_checks.PRECONDITION_TYPES))
    for event in lens.pack.events:
        for index, condition in enumerate(event.preconditions):
            known_type, missing_fields, extra_fields = base_checks.check_precondition_shape(
                condition.type, set(condition.model_fields_set), condition.model_dump()
            )
            if not known_type:
                problem = f"uses unknown type '{condition.type}'"
            else:
                missing = sorted(missing_fields)
                extra = sorted(extra_fields)
                if not missing and not extra:
                    continue
                parts: list[str] = []
                if missing:
                    parts.append(f"is missing {', '.join(missing)}")
                if extra:
                    parts.append(f"also carries {', '.join(extra)}")
                problem = f"type '{condition.type}' " + " and ".join(parts)
            findings.append(make_finding(
                "E29", "events.yaml", f"{event.key}.preconditions.{index}",
                line=lens.source.field_line("events.yaml", event.key, "preconditions"),
                event=event.key, number=index + 1, problem=problem, known=known,
            ))
    return findings


def _label_references(lens: Lens) -> list[tuple[str, str, str, str]]:
    """(section, key, file, field) for every label the pack expects to display."""
    references: list[tuple[str, str, str, str]] = []
    for capability in lens.pack.capabilities:
        references.append(("capabilities", capability.key, "capabilities.yaml", capability.key))
    for role in sorted(lens.required_roles | lens.filled_roles):
        references.append(("roles", role, "labels.yaml", f"roles.{role}"))
    for strategy in lens.pack.strategies:
        references.append(("strategies", strategy.key, "strategies.yaml", strategy.key))
    for person in lens.pack.stakeholders:
        references.append(
            ("stakeholders", person.display_name_key, "stakeholders.yaml", f"{person.key}.display_name_key")
        )
        references.append(("misc", person.role_key, "stakeholders.yaml", f"{person.key}.role_key"))
    for event in lens.pack.events:
        references.append(("events", event.body_key, "events.yaml", f"{event.key}.body_key"))
    for policy in lens.pack.policies:
        references.append(("policies", policy.key, "policies.yaml", policy.key))
    for item in lens.pack.catalog:
        if item.process_option is not None:
            references.append(
                ("misc", item.process_option.label_key, "catalog.yaml", f"{item.key}.process_option.label_key")
            )
    return references


def check_labels(lens: Lens) -> list[Finding]:
    """E07 -- a key that reaches a screen with no authored wording behind it."""
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for section, key, relative, field in _label_references(lens):
        if (section, key) in seen:
            continue
        seen.add((section, key))
        # A label is accepted in the section its reference names, and nowhere else.
        #
        # `misc` used to fall back to a union of EVERY section, which meant the fix line
        # ("add '{key}' under misc in labels.yaml") named one of eight accepted answers,
        # and every section 1.1 rework-2 added made it one of twelve (finding 1.1-r2-004).
        # A check whose Fix: text is not the thing the check tests teaches the author the
        # wrong file. Narrowed so the two agree: `misc` means `misc`.
        if key in lens.labels.get(section, {}):
            continue
        findings.append(
            make_finding(
                "E07",
                relative,
                field,
                line=lens.source.token_line(relative, key),
                subject=_subject(section),
                key=key,
                section=section,
            )
        )
    return findings


def check_archetypes(lens: Lens) -> list[Finding]:
    """E08 -- a persona cast as an archetype the platform does not have."""
    findings: list[Finding] = []
    for person in lens.pack.stakeholders:
        if person.archetype not in base_checks.ARCHETYPES:
            findings.append(
                make_finding(
                    "E08",
                    "stakeholders.yaml",
                    f"{person.key}.archetype",
                    line=lens.source.key_line("stakeholders.yaml", person.key),
                    stakeholder=lens.label("stakeholders", person.display_name_key),
                    archetype=person.archetype,
                    count=len(base_checks.ARCHETYPES),
                    known=", ".join(sorted(base_checks.ARCHETYPES)),
                )
            )
    return findings


def check_data_flows(lens: Lens) -> list[Finding]:
    """E09 -- must_feed / must_be_fed_by naming a capability that does not exist."""
    findings: list[Finding] = []
    for item in lens.pack.catalog:
        for flow, name in ((item.must_feed, "must_feed"), (item.must_be_fed_by, "must_be_fed_by")):
            for edge in flow:
                for capability in (edge.from_capability, edge.to_capability):
                    if capability is None or capability in lens.capability_keys:
                        continue
                    findings.append(
                        make_finding(
                            "E09",
                            "catalog.yaml",
                            f"{item.key}.{name}.{capability}",
                            line=lens.source.field_line("catalog.yaml", item.key, name),
                            item_name=lens.label("catalog", item.key),
                            capability=capability,
                        )
                    )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- coherence (E20..E23)
# --------------------------------------------------------------------------------------


def check_unwatched_capabilities(lens: Lens) -> list[Finding]:
    """E20 -- a capability with no watch rule that can raise a signal.

    Widened in v1.2 (finding 1.2-001). The old predicate was "appears in no watch rule",
    which is a different test from the rationale E20 has always carried -- "it can never
    raise a signal". A capability watched only by a thresholdless rule is exactly as mute
    as one watched by nothing, and the narrow predicate let CG-1's closure condition be
    satisfied by authoring more rules that cannot fire.

    Widened again in rework-2 (item 3.2). v1.2's predicate read the thresholds directly,
    which made a correctly-authored `presence` rule read as mute -- so 1.3 could close CG-1
    exactly as 1.5 decision 8 tells it to and E20 would still fire. Coverage is now
    `_can_raise`, which is the rationale itself rather than a proxy for it.
    """
    findings: list[Finding] = []
    for capability in lens.pack.capabilities:
        if capability.key in lens.signal_covered:
            continue
        mute_rules = sorted(
            rule.key for rule in lens.mute_rules if rule.capability == capability.key
        )
        if mute_rules:
            reason = _reason("only_thresholdless", rules=", ".join(mute_rules))
        else:
            reason = _reason("no_watch_rule")
        findings.append(
            make_finding(
                "E20",
                "watch_rules.yaml",
                f"capability.{capability.key}",
                line=lens.source.token_line("watch_rules.yaml", mute_rules[0]) if mute_rules else None,
                capability=lens.label("capabilities", capability.key),
                reason=reason,
            )
        )
    return findings


def check_thresholdless_rules(lens: Lens) -> list[Finding]:
    """E12 -- a THRESHOLD watch rule carrying neither warn_above nor critical_above.

    Spec v1.2 section 3 decision 7, ruled by the user 2026-08-14. Such a rule can never
    fire, so it is not a watch rule -- it is the appearance of one, which is worse than its
    absence because it satisfies a coverage count while watching nothing.

    Rework-2 item 3.1 exempts `metric_kind: presence`: carrying no threshold is that kind's
    correct shape (1.5 section 5.1a), and models.py already refuses to construct a presence
    rule that carries one, so the exemption cannot hide a real defect. The predicate lives
    in `Lens.thresholdless`.
    """
    return [
        make_finding(
            "E12",
            "watch_rules.yaml",
            rule.key,
            line=lens.source.key_line("watch_rules.yaml", rule.key),
            rule_name=lens.label("watch_rules", rule.key),
            rule=rule.key,
            capability=lens.label("capabilities", rule.capability),
        )
        for rule in lens.thresholdless
    ]


def _raisable(lens: Lens, signal: str) -> set[str]:
    rule = lens.rules.get(signal)
    if rule is None:
        return set()
    return _raisable_severities(rule)


_THRESHOLD_FIELD = {"warning": "warn_above", "critical": "critical_above"}


def check_impossible_events(lens: Lens) -> list[Finding]:
    """E21 -- preconditions that can never all be true at once."""
    findings: list[Finding] = []
    for event in lens.pack.events:
        reasons: list[str] = []
        wanted: dict[str, set[str]] = {}
        for condition in event.preconditions:
            if condition.signal is None or condition.severity is None:
                continue
            wanted.setdefault(condition.signal, set()).add(condition.severity)
            if condition.signal not in lens.rules:
                continue  # E06 already reports the dangling reference
            if condition.severity not in _raisable(lens, condition.signal):
                # A presence rule is unreachable for a different reason than a threshold
                # rule is, and telling an author to "set the warn_above threshold" on one
                # is telling them to author a shape models.py rejects. Rework-2 item 3.3.
                if lens.rules[condition.signal].metric_kind == "presence":
                    reasons.append(
                        _reason(
                            "severity_unreachable_presence",
                            signal=condition.signal,
                            severity=condition.severity,
                        )
                    )
                else:
                    reasons.append(
                        _reason(
                            "severity_unreachable",
                            signal=condition.signal,
                            severity=condition.severity,
                            threshold_field=_THRESHOLD_FIELD[condition.severity],
                        )
                    )
        for signal, severities in wanted.items():
            if len(severities) > 1:
                first, second = sorted(severities)
                reasons.append(_reason("severity_conflict", signal=signal, first=first, second=second))
        for reason in reasons:
            findings.append(
                make_finding(
                    "E21",
                    "events.yaml",
                    f"{event.key}.preconditions",
                    line=lens.source.field_line("events.yaml", event.key, "preconditions"),
                    # E21 still leads with the machine key, deliberately. `labels.events` maps
                    # an event's `body_key` to a paragraph of in-world prose, NOT its name
                    # (docs/casepack-schema.md: "`events` is not a name map"), so routing this
                    # subject through it would print a persona's message as a locator line.
                    # There is nowhere to author an event NAME -- open item R1, a schema
                    # change, reported by this packet rather than improvised here.
                    event=event.key,
                    reason=reason,
                )
            )
    return findings


def _fully_coverable(lens: Lens, capability_key: str) -> bool:
    capability = next((c for c in lens.pack.capabilities if c.key == capability_key), None)
    if capability is None:
        return False
    if any(role not in lens.filled_roles for role in capability.required_roles):
        return False
    return all(
        lens.satisfiable(need.entity, need.min_level_of_detail)
        for need in capability.required_entities
    )


def check_strategy_reachability(lens: Lens) -> list[Finding]:
    """E22 -- the capability a strategy leans on hardest cannot be fully covered."""
    findings: list[Finding] = []
    for strategy in lens.pack.strategies:
        if not strategy.capability_weights:
            continue
        top = max(strategy.capability_weights.values())
        for capability_key in sorted(
            key for key, weight in strategy.capability_weights.items() if weight == top
        ):
            if _fully_coverable(lens, capability_key):
                continue
            findings.append(
                make_finding(
                    "E22",
                    "strategies.yaml",
                    f"{strategy.key}.capability_weights.{capability_key}",
                    line=lens.source.field_line("strategies.yaml", strategy.key, "capability_weights"),
                    strategy=lens.label("strategies", strategy.key),
                    capability=lens.label("capabilities", capability_key),
                )
            )
    return findings


def check_questions(lens: Lens) -> list[Finding]:
    """E23 -- a management question nothing in the catalog can answer."""
    findings: list[Finding] = []
    for question in lens.pack.questions:
        for need in question.requires_entities:
            if lens.satisfiable(need.entity, need.min_level_of_detail):
                continue
            findings.append(
                make_finding(
                    "E23",
                    "questions.yaml",
                    f"{question.key}.requires_entities.{need.entity}",
                    line=lens.source.key_line("questions.yaml", question.key),
                    question_name=lens.label("questions", question.key),
                    entity_name=lens.label("entities", need.entity),
                    entity=need.entity,
                    level=need.min_level_of_detail,
                )
            )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- obligation references (E24..E28)
#
# Added for finding 1.2-RA-001. obligation_rules.yaml loads (loader.py:27,89) but nothing
# validated it, so a nonexistent entity, policy, permissive value, action or armed event
# could reach the event and scoring engines while validate_casepack stayed green. Obligations
# reuse the signal machinery (1.5 decision 7), so a dangling reference is the same class of
# defect E05/E06/E09 already catch for watch rules and events -- just in the file that had no
# checks at all.
#
# obligation_rules.yaml is OPTIONAL: a pack without it loads clean and pack.obligation_rules
# is the empty list, so this loop simply does not run (finding 1.1-r2-001).
# --------------------------------------------------------------------------------------


def check_obligation_references(lens: Lens) -> list[Finding]:
    """E24..E28 -- an obligation names something the pack does not define."""
    findings: list[Finding] = []
    pack = lens.pack
    entity_keys = {entity.key for entity in pack.entities}
    policies = {policy.key: policy for policy in pack.policies}
    event_keys = {event.key for event in pack.events}
    relative = "obligation_rules.yaml"
    for rule in pack.obligation_rules:
        line = lens.source.key_line(relative, rule.key)
        policy = policies.get(rule.policy)

        # E24 -- the policy switch it reads
        if policy is None:
            findings.append(
                make_finding(
                    "E24", relative, f"{rule.key}.policy", line=line,
                    obligation=rule.key, policy=rule.policy, file=relative,
                )
            )

        # E25 -- the entity it protects
        if rule.entity not in entity_keys:
            findings.append(
                make_finding(
                    "E25", relative, f"{rule.key}.entity", line=line,
                    obligation=rule.key, entity=rule.entity, file=relative,
                )
            )

        # E26 -- permissive_value must name a DECLARED option of that policy (CONTRACTS.md
        # PolicyOption.options / obligation_rules.permissive_value). Checked whenever the
        # policy resolves: a policy that declares NO options gives permissive_value no
        # vocabulary to name, which is the dangling reference E26 exists to catch, not a
        # reason to stay silent (finding 1.2-VR-001). Two shapes, one code:
        if policy is not None:
            if not policy.options:
                findings.append(
                    make_finding(
                        "E26", relative, f"{rule.key}.permissive_value", line=line,
                        variant="E26_no_options",
                        obligation=rule.key, value=rule.permissive_value, policy=rule.policy,
                        file=relative,
                    )
                )
            elif rule.permissive_value not in policy.options:
                findings.append(
                    make_finding(
                        "E26", relative, f"{rule.key}.permissive_value", line=line,
                        obligation=rule.key, value=rule.permissive_value, policy=rule.policy,
                        options=", ".join(policy.options), file=relative,
                    )
                )

        # E27 -- the actions that clear it, against the same ACTION_TYPES set as E05
        for action in rule.cleared_by:
            if action not in base_checks.ACTION_TYPES:
                findings.append(
                    make_finding(
                        "E27", relative, f"{rule.key}.cleared_by.{action}", line=line,
                        obligation=rule.key, action=action,
                        known=", ".join(sorted(base_checks.ACTION_TYPES)), file=relative,
                    )
                )

        # E28 -- the events it arms while it stays open
        for event in rule.arms:
            if event not in event_keys:
                findings.append(
                    make_finding(
                        "E28", relative, f"{rule.key}.arms.{event}", line=line,
                        obligation=rule.key, event=event, file=relative,
                    )
                )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- initial_state (E13, E14)
#
# Added v1.2 for finding 1.2-014: initial_state is fourteen fields deep and, before this,
# not one check read any of it. A pack naming a strategy that does not exist and holding
# more capital than it has validated clean.
#
# `initial_state` is optional. A pack without one is a pack a section has not started, so
# absence is not a defect and neither code fires -- rework.md section 1, ruling 3.
# --------------------------------------------------------------------------------------


def _initial_state(lens: Lens) -> Any:
    return getattr(lens.pack.metadata, "initial_state", None)


def check_initial_state_references(lens: Lens) -> list[Finding]:
    """E13 -- a key inside initial_state that names a pack object the pack does not define.

    Scope per rework.md section 1, ruling 2, MINUS `value_chain_coverage`'s keys and
    `needs_attention`, both of which are declared in dod.md as a partial decline with
    evidence: the first is keyed by Porter value-chain activity rather than by capability,
    and the second holds authored prose. See dod.md section 10.
    """
    state = _initial_state(lens)
    if state is None:
        return []
    findings: list[Finding] = []

    def report(kind: str, key: str, field: str, line: int | None) -> None:
        findings.append(
            make_finding(
                "E13",
                "pack.yaml",
                f"initial_state.{field}",
                line=line,
                kind=_subject(kind),
                key=key,
                section=kind,
            )
        )

    strategy_line = lens.source.find("pack.yaml", r"^\s*declared_strategy\s*:")
    if state.declared_strategy not in lens.strategy_keys:
        report("strategies", state.declared_strategy, "declared_strategy", strategy_line)

    for unit in state.unit_responses:
        for item in unit.running:
            if item not in lens.catalog_keys:
                report("catalog", item, f"unit_responses.{unit.unit}.running", lens.source.token_line("pack.yaml", item))
        # `contributing` names a value chain activity; a capability IS one (1.1 O1), so
        # either vocabulary resolves it.
        if unit.contributing not in lens.chain_positions | lens.capability_keys:
            report(
                "capabilities",
                unit.contributing,
                f"unit_responses.{unit.unit}.contributing",
                lens.source.token_line("pack.yaml", unit.contributing),
            )

    for index, row in enumerate(state.review.lines):
        if row.area not in base_checks.REVIEW_AREAS:
            report("review_areas", row.area, f"review.lines.{index}.area", lens.source.token_line("pack.yaml", row.area))

    return findings


def _derivations(state: Any, metadata: Any) -> list[tuple[str, str, int, int]]:
    """(field, derivation key, authored value, derived value) for every checkable figure.

    Tolerance is ZERO -- rework.md section 1, ruling 1. These are authored integers; a
    derived figure and an authored one either match or they do not.
    """
    review = state.review
    budget = state.budget
    line_capital = sum(row.capital for row in review.lines)
    line_run_rate = sum(row.run_rate_effect for row in review.lines)
    rows: list[tuple[str, str, int, int]] = [
        ("review.capital_committed", "review_lines_capital", review.capital_committed, line_capital),
        # `review.capital_remaining` used to be checked here as well. The field was removed by
        # the catch-up rework (CG-6 / finding `1.3-001`): it was a second schema-required home
        # for the fact the row below already checks, against the identical derivation. The
        # invariant is unchanged -- one row now enforces what two used to enforce twice.
        (
            "review.run_rate_after",
            "review_run_rate",
            review.run_rate_after,
            review.run_rate_before + line_run_rate,
        ),
        (
            "budget.capital_remaining",
            "budget_remaining",
            budget.capital_remaining,
            review.capital_available - review.capital_committed,
        ),
        (
            "budget.capital_available",
            "budget_available",
            budget.capital_available,
            review.capital_available,
        ),
        ("budget.run_rate", "budget_run_rate", budget.run_rate, review.run_rate_before),
    ]
    capex = metadata.budget.capex_per_round
    if 0 < budget.round <= len(capex):
        rows.append(
            ("budget.capital_available", "capex_for_round", budget.capital_available, capex[budget.round - 1])
        )
    return rows


def check_initial_state_figures(lens: Lens) -> list[Finding]:
    """E14 -- an authored initial_state figure contradicting one derived from the pack."""
    state = _initial_state(lens)
    if state is None:
        return []
    findings: list[Finding] = []
    seen: set[tuple[str, int, int]] = set()
    for field, derivation, authored, derived in _derivations(state, lens.pack.metadata):
        if authored == derived:
            continue
        signature = (field, authored, derived)
        if signature in seen:
            continue
        seen.add(signature)
        findings.append(
            make_finding(
                "E14",
                "pack.yaml",
                f"initial_state.{field}",
                line=lens.source.find("pack.yaml", rf"^\s*{re.escape(field.split('.')[-1])}\s*:"),
                field_name=field,
                authored=authored,
                derived=derived,
                derivation=_reason(derivation),
            )
        )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- seed-quality heuristics (W01..W07)
# --------------------------------------------------------------------------------------


#: The fields that name a preference's ideal position, across every supported preference
#: shape: `ideal_value` (legacy numeric -- catalog/platform/training overrides),
#: `ideal_posture` (policies -- an ordinal option key) and `ideal_tier` (services -- a
#: support/integration tier). W01 counts identical (ideal, weight) rows regardless of which
#: of these carries the ideal, so it sees placeholder seeding in every preference domain
#: rather than only the one legacy shape it read before (finding 1.2-RA-002).
_PREFERENCE_IDEAL_FIELDS = ("ideal_value", "ideal_posture", "ideal_tier")


def _preference_rows(node: Any) -> Iterable[tuple[str, Any, Any]]:
    """Every preference row anywhere in a domain file, found by its semantic fields.

    A row is any mapping that names an ideal position -- `ideal_value`, `ideal_posture` or
    `ideal_tier`. Its weight is the `weight` in that SAME mapping (the per-decision weight in
    the `by_decision` shape, the per-row weight in the legacy `overrides` shape), never the
    archetype-level aggregate weight one level up: that mapping carries no ideal field and so
    is not itself a row. Yields (ideal_field, ideal, weight).
    """
    if isinstance(node, dict):
        for field in _PREFERENCE_IDEAL_FIELDS:
            if field in node:
                yield field, node[field], node.get("weight")
                break
        for child in node.values():
            yield from _preference_rows(child)
    elif isinstance(node, list):
        for child in node:
            yield from _preference_rows(child)


def check_placeholder_preferences(lens: Lens, raw: dict[str, Any]) -> list[Finding]:
    """W01 -- rows sharing one ideal and one weight look seeded, not authored.

    Rewritten for finding 1.2-RA-002. The previous check read only `defaults_by_archetype`
    rows carrying `ideal_value`, so it was blind to `preferences/policies.yaml` and
    `preferences/services.yaml`, which nest ideals under `by_decision` as `ideal_posture` /
    `ideal_tier`. It now walks every domain by the ideal fields themselves, so the same
    placeholder-seeding shape is caught in all five preference domains, not one.
    """
    findings: list[Finding] = []
    domains = raw.get("preferences")
    if not isinstance(domains, dict):
        return findings
    for domain in sorted(domains):
        body = domains[domain]
        groups: dict[tuple[str, Any, Any], int] = {}
        for field, ideal, weight in _preference_rows(body):
            signature = (field, ideal, weight)
            groups[signature] = groups.get(signature, 0) + 1
        relative = f"preferences/{domain}.yaml"
        for (field, ideal, weight), count in sorted(groups.items(), key=lambda pair: str(pair[0])):
            if count < W01_MIN_IDENTICAL_ROWS:
                continue
            findings.append(
                make_finding(
                    "W01",
                    relative,
                    f"{domain}.{field}",
                    line=lens.source.find(relative, rf"\b{field}\s*:"),
                    count=count,
                    domain=domain.replace("_", " ").title(),
                    ideal=ideal,
                    weight=weight,
                    file=relative,
                )
            )
    return findings


def check_unweighted_capabilities(lens: Lens) -> list[Finding]:
    """W02 -- a capability no strategy cares about."""
    findings: list[Finding] = []
    for capability in lens.pack.capabilities:
        best = max(
            (strategy.capability_weights.get(capability.key, 0.0) for strategy in lens.pack.strategies),
            default=0.0,
        )
        if best > W02_MIN_WEIGHT:
            continue
        findings.append(
            make_finding(
                "W02",
                "strategies.yaml",
                f"capability_weights.{capability.key}",
                line=None,
                capability=lens.label("capabilities", capability.key),
                threshold=W02_MIN_WEIGHT,
            )
        )
    return findings


def check_untargeted_events(lens: Lens) -> list[Finding]:
    """W03 -- an event with no strategy affinity fires whatever a team declared."""
    return [
        make_finding(
            "W03",
            "events.yaml",
            f"{event.key}.strategy_affinity",
            line=lens.source.field_line("events.yaml", event.key, "strategy_affinity"),
            event=event.key,
        )
        for event in lens.pack.events
        if not event.strategy_affinity
    ]


def check_dead_catalog(lens: Lens) -> list[Finding]:
    """W04 -- a catalog item no capability can use."""
    return [
        make_finding(
            "W04",
            "catalog.yaml",
            f"{item.key}.roles_filled",
            line=lens.source.key_line("catalog.yaml", item.key),
            item_name=lens.label("catalog", item.key),
        )
        for item in lens.pack.catalog
        if not (set(item.roles_filled) & lens.required_roles)
    ]


def check_deck_depth(lens: Lens) -> list[Finding]:
    """W05 -- fewer cards than rounds, so some round has nothing to deal."""
    rounds = lens.pack.metadata.rounds
    count = len(lens.pack.events)
    if count >= rounds:
        return []
    return [
        make_finding(
            "W05",
            "events.yaml",
            "events",
            line=None,
            count=count,
            rounds=rounds,
        )
    ]


def check_strategy_draws(lens: Lens) -> list[Finding]:
    """W08 -- a strategy too few cards in the deck can ever be dealt to.

    1.5 spec section 5.2a, at N = pack.metadata.rounds (its O4). W05's
    deck-DEPTH proxy cannot see this: a six-card deck all affine to one strategy passes it,
    and that is CG-2's actual shape -- "strategies that draw nothing".

        draws(S) = events whose strategy_affinity includes S, or is empty

    An event with no affinity is drawn by everyone, which is why it counts for every
    strategy here and is separately reported by W03.

    WARN, not ERROR (1.5 section 5.2a): a thin deck is authorable content rather than a
    broken pack, and 1.7's calibration is where a deck that starves a strategy actually
    fails.
    """
    findings: list[Finding] = []
    minimum = lens.pack.metadata.rounds
    for strategy in lens.pack.strategies:
        draws = [
            event
            for event in lens.pack.events
            if not event.strategy_affinity or strategy.key in event.strategy_affinity
        ]
        if len(draws) >= minimum:
            continue
        findings.append(
            make_finding(
                "W08",
                "events.yaml",
                f"strategy_affinity.{strategy.key}",
                line=None,
                strategy=lens.label("strategies", strategy.key),
                strategy_key=strategy.key,
                count=len(draws),
                minimum=minimum,
            )
        )
    return findings


def check_training_choice(lens: Lens) -> list[Finding]:
    """W06 -- every training tier reaching everybody is not a choice."""
    return [
        make_finding(
            "W06",
            "catalog.yaml",
            f"{item.key}.training_options",
            line=lens.source.field_line("catalog.yaml", item.key, "training_options"),
            item_name=lens.label("catalog", item.key),
        )
        for item in lens.pack.catalog
        if item.training_options
        and all(option.coverage == 1.0 for option in item.training_options.values())
    ]


def check_cost_decoys(lens: Lens) -> list[Finding]:
    """W07 -- no decoy costs means the cost forecast is trivially winnable."""
    return [
        make_finding(
            "W07",
            "catalog.yaml",
            f"{item.key}.decoy_cost_categories",
            line=lens.source.field_line("catalog.yaml", item.key, "decoy_cost_categories"),
            item_name=lens.label("catalog", item.key),
        )
        for item in lens.pack.catalog
        if not item.decoy_cost_categories
    ]


# --------------------------------------------------------------------------------------
# the one producer
# --------------------------------------------------------------------------------------

_SEVERITY_ORDER = {ERROR: 0, WARN: 1, INFO: 2}


def validate(pack: Casepack, source: PackSource, raw: dict[str, Any]) -> list[Finding]:
    """Every check that needs a loaded pack."""
    lens = Lens(pack, source)
    findings: list[Finding] = []
    findings += check_inherited(lens)
    findings += check_entity_detail(lens)
    findings += check_event_references(lens)
    findings += check_precondition_shapes(lens)
    findings += check_labels(lens)
    findings += check_archetypes(lens)
    findings += check_data_flows(lens)
    findings += check_thresholdless_rules(lens)
    findings += check_initial_state_references(lens)
    findings += check_initial_state_figures(lens)
    findings += check_unwatched_capabilities(lens)
    findings += check_impossible_events(lens)
    findings += check_strategy_reachability(lens)
    findings += check_questions(lens)
    findings += check_obligation_references(lens)
    findings += check_placeholder_preferences(lens, raw)
    findings += check_unweighted_capabilities(lens)
    findings += check_untargeted_events(lens)
    findings += check_dead_catalog(lens)
    findings += check_deck_depth(lens)
    findings += check_strategy_draws(lens)
    findings += check_training_choice(lens)
    findings += check_cost_decoys(lens)
    return findings


def exit_code_for(findings: list[Finding]) -> int:
    """Spec 3.1's one expression, in one place.

    The v1.1 build carried a second copy inside directory mode, which the audit flagged
    against SPEC_PROTOCOL section 3 ("one source of truth per fact"). Both callers now
    share this.
    """
    return 1 if any(item.severity == ERROR for item in findings) else 0


@dataclass
class Report:
    findings: list[Finding]
    pack: Casepack | None
    raw: dict[str, Any]

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == WARN]

    @property
    def exit_code(self) -> int:
        return exit_code_for(self.findings)


@dataclass
class Run:
    """One invocation: one pack, or a directory of them. The single producer both
    renderers consume, so they cannot drift -- spec 3.1, invariant I5 as widened in v1.2.
    """

    packs: list[tuple[Path, Report]]
    shared: list[Finding]
    directory: bool

    @property
    def findings(self) -> list[Finding]:
        """Every finding, pack-attributed, in the one canonical order."""
        ordered: list[Finding] = []
        for path, report in self.packs:
            ordered.extend(item.with_pack(str(path)) for item in report.findings)
        ordered.extend(self.shared)
        return ordered

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == WARN]

    @property
    def exit_code(self) -> int:
        return exit_code_for(self.findings)


def validate_pack_dir(pack_dir: str | Path) -> Report:
    """Load a pack directory and run every check that its state allows."""
    root = Path(pack_dir)
    source = PackSource(root)
    raw, findings = read_raw(root)
    findings += check_duplicate_keys(raw, source)
    findings += check_schema_version(raw, source)
    # Raw-stage policy vocabulary (E15..E17). Runs BEFORE the load so that a policy whose
    # default is outside its options -- which makes models.py refuse the pack -- is reported
    # as a precise code that co-reports with the other raw checks below, rather than being
    # collapsed into the opaque E00 the load failure used to produce (finding 1.2-RA-003).
    findings += check_policy_vocab(raw, source)
    # Raw-stage precondition vocabulary (E29, vocab variant). Same reason, same stage: a
    # `placement` or `severity` outside its Literal makes models.py refuse the pack, and
    # that refusal used to surface as a bare E00 against a file that parsed (finding B7).
    findings += check_precondition_vocab_raw(raw, source)

    pack: Casepack | None = None
    try:
        pack = load_casepack(root)
    except CasepackLoadError as exc:
        # models.py refuses to build a pack whose weights or demand curves are wrong, so
        # those two checks have to run against raw YAML on this path.
        findings += check_weights_raw(raw, source)
        findings += check_demand_raw(raw, source)
        # A closed-vocabulary value (a Literal or StrEnum field set out of range) is the
        # other family that refuses the load; E18 names the field instead of collapsing the
        # whole pack into E00 (finding CU-001).
        findings += check_closed_vocab_load(exc, raw, source)
        if not any(item.severity == ERROR for item in findings):
            findings.append(
                make_finding("E00", _blamed_file(exc), "casepack", detail=str(exc), file=_blamed_file(exc))
            )
    else:
        findings += validate(pack, source, raw)

    findings.sort(key=lambda item: (_SEVERITY_ORDER[item.severity], item.code, item.file, item.field))
    return Report(findings=findings, pack=pack, raw=raw)


def _blamed_file(exc: CasepackLoadError) -> str:
    head = str(exc).split(":", 1)[0].strip()
    return head or "pack.yaml"


# --------------------------------------------------------------------------------------
# renderer one -- text (spec 5.4)
# --------------------------------------------------------------------------------------


def _count_phrase(count: int, one: str, many: str, zero: str) -> str:
    if count == 0:
        return _render(zero)
    if count == 1:
        return _render(one)
    return _render(many, count=count)


def _clean_lines(report: Report) -> list[str]:
    """The tick lines from spec 5.4, each shown only when its own check came back clean."""
    pack = report.pack
    if pack is None:
        return []
    raised = {item.code for item in report.findings}
    lines: list[str] = []
    if "E01" not in raised:
        lines.append(_render("ok_roles", count=len(pack.capabilities)))
    if "E03" not in raised:
        lines.append(_render("ok_weights", count=len(pack.strategies)))
    if "E06" not in raised and "E21" not in raised:
        lines.append(_render("ok_events", count=len(pack.events)))
    if "E04" not in raised:
        lines.append(_render("ok_demand", rounds=pack.metadata.rounds))
    return lines


#: Column width for the business name on a locator line. Wider subjects push the locator
#: right; the parity check in check_fixture_matrix.py splits on two-or-more spaces.
_SUBJECT_WIDTH = 30


def _finding_block(finding: Finding) -> list[str]:
    """One finding, in the v1.2 section 5.4 shape.

    Business name leads, code is shown, `Fix:` prints at EVERY severity (section 3
    decision 3), and the schema field path moves below the fix -- kept, not deleted.

    The v1.2 sample omits the `Field:` line on two of its four blocks. The prose above it
    is explicit that the path "is kept -- moved, not deleted", so it prints on all of them.
    Where the sample and the written decision disagree, the decision governs: that is the
    lesson of findings 1.2-009 and 1.2-010, where the v1.1 build followed the picture.
    """
    where = finding.file if finding.line is None else f"{finding.file}:{finding.line}"
    # Two spaces minimum before the locator, even when the subject overruns its column, so
    # the separator stays unambiguous for I5's text-vs-JSON parity check.
    return [
        f"  {finding.severity:<6} {finding.code:<4} {finding.subject:<{_SUBJECT_WIDTH}}  {where}",
        f"         {finding.message}",
        f"         {finding.fix}",
        f"         {_render('field_prefix')} {finding.field}",
        "",
    ]


def _summary_line(errors: int, warnings: int, exit_code: int) -> str:
    return "  " + _render(
        "summary",
        errors=_count_phrase(errors, "one_error", "many_errors", "no_errors"),
        warnings=_count_phrase(warnings, "one_warning", "many_warnings", "no_warnings"),
        exit_code=exit_code,
    )


def _report_block(report: Report) -> list[str]:
    out: list[str] = [""]
    pack = report.pack
    if pack is not None:
        meta = pack.metadata
        out.append(
            "  "
            + _render(
                "header",
                pack_key=meta.pack_key,
                pack_version=meta.pack_version,
                schema_version=meta.schema_version,
                vertical=meta.vertical,
                rounds=meta.rounds,
            )
        )
        out.append("")
    clean = _clean_lines(report)
    for line in clean:
        out.append(f"  ✓  {line}")
    if clean:
        out.append("")
    for finding in report.findings:
        out.extend(_finding_block(finding))
    return out


def render_text(run: Run) -> str:
    out: list[str] = []
    for path, report in run.packs:
        if run.directory:
            out.append("")
            out.append(f"  {path}")
        out.extend(_report_block(report))
        if not run.directory:
            out.append(_summary_line(len(report.errors), len(report.warnings), report.exit_code))
            out.append("")
    if run.directory:
        for finding in run.shared:
            out.extend(_finding_block(finding))
        out.append(_summary_line(len(run.errors), len(run.warnings), run.exit_code))
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# renderer two -- json (spec 3.1: the same list, in the same order, in every mode)
# --------------------------------------------------------------------------------------


def render_json(run: Run) -> str:
    return json.dumps([finding.as_dict() for finding in run.findings], indent=2)


# --------------------------------------------------------------------------------------
# O2 -- a directory of packs
# --------------------------------------------------------------------------------------


def _is_pack(path: Path) -> bool:
    return (path / "pack.yaml").is_file()


def _pack_dirs(root: Path) -> list[Path]:
    return sorted(child for child in root.iterdir() if child.is_dir() and _is_pack(child))


def check_pack_key_uniqueness(reports: list[tuple[Path, Report]]) -> list[Finding]:
    """O2 default -- pack_key must be unique across a directory of packs.

    Still code E10 (the spec's code list is E00-E14, so a new code would break I1's set
    equality), but its own message and fix. Finding 1.2-006: reusing E10's wording told the
    reader to "give every entry in pack.yaml its own key", which is not an action that
    exists when the condition is N separate pack.yaml files in N separate directories.
    """
    homes: dict[str, list[str]] = {}
    for path, report in reports:
        if report.pack is not None:
            homes.setdefault(report.pack.metadata.pack_key, []).append(str(path))
    return [
        make_finding(
            "E10",
            "pack.yaml",
            f"pack_key.{key}",
            variant="E10_pack_key",
            key=key,
            count=len(paths),
            paths=", ".join(sorted(paths)),
        )
        for key, paths in sorted(homes.items())
        if len(paths) > 1
    ]


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = _JSON_FLAG in args
    args = [item for item in args if item != _JSON_FLAG]
    if len(args) != 1:
        print(_render("usage"), file=sys.stderr)
        return 2

    root = Path(args[0])
    if not root.is_dir():
        print(_render("usage"), file=sys.stderr)
        return 2

    try:
        if _is_pack(root):
            run = Run(packs=[(root, validate_pack_dir(root))], shared=[], directory=False)
        else:
            # O2 -- a directory of packs: validate each, then check pack_key uniqueness
            children = _pack_dirs(root)
            if not children:
                print(_render("usage"), file=sys.stderr)
                return 2
            reports = [(child, validate_pack_dir(child)) for child in children]
            run = Run(
                packs=reports,
                shared=[item.with_pack(str(root)) for item in check_pack_key_uniqueness(reports)],
                directory=True,
            )
        print(render_json(run) if as_json else render_text(run))
        return run.exit_code
    except Exception as exc:  # the validator itself failed -- spec 3 decision 2
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

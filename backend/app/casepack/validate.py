"""Casepack validator: one producer of findings, two renderers, one exit code."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.casepack import checks as base_checks
from app.casepack.loader import CasepackLoadError, load_casepack
from app.casepack.models import Casepack

# --------------------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------------------

#: highest schema_version this build knows how to read (spec 5.1, E11)
SUPPORTED_SCHEMA_VERSION = 1

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

#: The 14 platform stakeholder archetypes.
#: Source: design/05-implementation-plan.md section 1.4.1 (the platform layer) and
#: design/01-mis_lite-harvest.md section 2 (`stakeholders`, 14 rows, 7 internal +
#: 7 external). Unlike ACTION_TYPES this set had no existing home in checks.py; see
#: handoffs/1.2-validator/dod.md for the note recording that it was introduced here.
ARCHETYPES = frozenset(
    {
        "c_suite",
        "finance",
        "employees",
        "operations",
        "it",
        "hr",
        "marketing",
        "investor",
        "customer",
        "vendor",
        "security_auditor",
        "regulator",
        "general_public",
        "media",
    }
)

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
    file: str
    field: str
    message: str
    fix: str
    line: int | None = None

    def __post_init__(self) -> None:
        # spec 3.1: I1 holds because a fix-less ERROR is unconstructible, not discouraged
        if not self.fix.strip():
            raise ValueError(f"{self.code}: fix is empty")
        if not self.file.strip():
            raise ValueError(f"{self.code}: file is empty")
        if not self.field.strip():
            raise ValueError(f"{self.code}: field is empty")

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
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
    **params: Any,
) -> Finding:
    entry = catalogue()["codes"][code]
    return Finding(
        code=code,
        severity=entry["severity"],
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


# --------------------------------------------------------------------------------------
# typed stage helpers
# --------------------------------------------------------------------------------------


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
        self.filled_roles = {role for item in pack.catalog for role in item.roles_filled}
        self.filled_roles |= {
            role for service in pack.platform.services for role in service.roles_filled
        }
        self.required_roles = {
            role for capability in pack.capabilities for role in capability.required_roles
        }
        self.owned: dict[str, int] = {}
        for item in pack.catalog:
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
    everywhere = {key for section in lens.labels.values() for key in section}
    for section, key, relative, field in _label_references(lens):
        if (section, key) in seen:
            continue
        seen.add((section, key))
        # `misc` is the catch-all section, so accept the key anywhere in labels.yaml
        found = key in lens.labels.get(section, {})
        if not found and section == "misc":
            found = key in everywhere
        if found:
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
        if person.archetype not in ARCHETYPES:
            findings.append(
                make_finding(
                    "E08",
                    "stakeholders.yaml",
                    f"{person.key}.archetype",
                    line=lens.source.key_line("stakeholders.yaml", person.key),
                    stakeholder=lens.label("stakeholders", person.display_name_key),
                    archetype=person.archetype,
                    count=len(ARCHETYPES),
                    known=", ".join(sorted(ARCHETYPES)),
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
                            item=item.key,
                            capability=capability,
                        )
                    )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- coherence (E20..E23)
# --------------------------------------------------------------------------------------


def check_unwatched_capabilities(lens: Lens) -> list[Finding]:
    """E20 -- a capability nothing watches can never raise a signal."""
    findings: list[Finding] = []
    for capability in lens.pack.capabilities:
        if capability.key in lens.watched:
            continue
        findings.append(
            make_finding(
                "E20",
                "watch_rules.yaml",
                f"capability.{capability.key}",
                line=None,
                capability=lens.label("capabilities", capability.key),
            )
        )
    return findings


def _raisable(lens: Lens, signal: str) -> set[str]:
    rule = lens.rules.get(signal)
    if rule is None:
        return set()
    severities: set[str] = set()
    if rule.warn_above is not None:
        severities.add("warning")
    if rule.critical_above is not None:
        severities.add("critical")
    return severities


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
                    question=question.key,
                    entity=need.entity,
                    level=need.min_level_of_detail,
                )
            )
    return findings


# --------------------------------------------------------------------------------------
# typed stage -- seed-quality heuristics (W01..W07)
# --------------------------------------------------------------------------------------


def check_placeholder_preferences(lens: Lens, raw: dict[str, Any]) -> list[Finding]:
    """W01 -- rows sharing one ideal_value and one weight look seeded, not authored."""
    findings: list[Finding] = []
    domains = raw.get("preferences")
    if not isinstance(domains, dict):
        return findings
    for domain in sorted(domains):
        body = domains[domain]
        if not isinstance(body, dict):
            continue
        rows: list[dict[str, Any]] = []
        defaults = body.get("defaults_by_archetype")
        if isinstance(defaults, dict):
            rows.extend(row for row in defaults.values() if isinstance(row, dict))
        rows.extend(row for row in _as_list(body.get("overrides")) if isinstance(row, dict))
        groups: dict[tuple[Any, Any], int] = {}
        for row in rows:
            if "ideal_value" not in row:
                continue
            signature = (row.get("ideal_value"), row.get("weight"))
            groups[signature] = groups.get(signature, 0) + 1
        relative = f"preferences/{domain}.yaml"
        for (ideal_value, weight), count in sorted(groups.items(), key=lambda pair: str(pair[0])):
            if count < W01_MIN_IDENTICAL_ROWS:
                continue
            findings.append(
                make_finding(
                    "W01",
                    relative,
                    "overrides.ideal_value",
                    line=lens.source.find(relative, r"^overrides\s*:"),
                    count=count,
                    ideal_value=ideal_value,
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
            item=item.key,
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


def check_training_choice(lens: Lens) -> list[Finding]:
    """W06 -- every training tier reaching everybody is not a choice."""
    return [
        make_finding(
            "W06",
            "catalog.yaml",
            f"{item.key}.training_options",
            line=lens.source.field_line("catalog.yaml", item.key, "training_options"),
            item=item.key,
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
            item=item.key,
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
    findings += check_labels(lens)
    findings += check_archetypes(lens)
    findings += check_data_flows(lens)
    findings += check_unwatched_capabilities(lens)
    findings += check_impossible_events(lens)
    findings += check_strategy_reachability(lens)
    findings += check_questions(lens)
    findings += check_placeholder_preferences(lens, raw)
    findings += check_unweighted_capabilities(lens)
    findings += check_untargeted_events(lens)
    findings += check_dead_catalog(lens)
    findings += check_deck_depth(lens)
    findings += check_training_choice(lens)
    findings += check_cost_decoys(lens)
    return findings


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
        return 1 if self.errors else 0


def validate_pack_dir(pack_dir: str | Path) -> Report:
    """Load a pack directory and run every check that its state allows."""
    root = Path(pack_dir)
    source = PackSource(root)
    raw, findings = read_raw(root)
    findings += check_duplicate_keys(raw, source)
    findings += check_schema_version(raw, source)

    pack: Casepack | None = None
    try:
        pack = load_casepack(root)
    except CasepackLoadError as exc:
        # models.py refuses to build a pack whose weights or demand curves are wrong, so
        # those two checks have to run against raw YAML on this path.
        findings += check_weights_raw(raw, source)
        findings += check_demand_raw(raw, source)
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


def render_text(report: Report) -> str:
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
        where = finding.file if finding.line is None else f"{finding.file}:{finding.line}"
        out.append(f"  {finding.severity:<6} {where}  {finding.field}")
        out.append(f"         {finding.message}")
        if finding.severity == ERROR:
            out.append(f"         {finding.fix}")
        out.append("")

    out.append(
        "  "
        + _render(
            "summary",
            errors=_count_phrase(len(report.errors), "one_error", "many_errors", "no_errors"),
            warnings=_count_phrase(len(report.warnings), "one_warning", "many_warnings", "no_warnings"),
            exit_code=report.exit_code,
        )
    )
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# renderer two -- json (spec 3.1: the same list)
# --------------------------------------------------------------------------------------


def render_json(report: Report) -> str:
    return json.dumps([finding.as_dict() for finding in report.findings], indent=2)


# --------------------------------------------------------------------------------------
# O2 -- a directory of packs
# --------------------------------------------------------------------------------------


def _is_pack(path: Path) -> bool:
    return (path / "pack.yaml").is_file()


def _pack_dirs(root: Path) -> list[Path]:
    return sorted(child for child in root.iterdir() if child.is_dir() and _is_pack(child))


def check_pack_key_uniqueness(reports: list[tuple[Path, Report]]) -> list[Finding]:
    """O2 default -- pack_key must be unique across a directory of packs."""
    counts: dict[str, int] = {}
    for _, report in reports:
        if report.pack is not None:
            key = report.pack.metadata.pack_key
            counts[key] = counts.get(key, 0) + 1
    return [
        make_finding("E10", "pack.yaml", f"pack_key.{key}", key=key, count=count, file="pack.yaml")
        for key, count in sorted(counts.items())
        if count > 1
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
            report = validate_pack_dir(root)
            print(render_json(report) if as_json else render_text(report))
            return report.exit_code

        # O2 -- given a directory of packs, validate each and check pack_key uniqueness
        children = _pack_dirs(root)
        if not children:
            print(_render("usage"), file=sys.stderr)
            return 2
        reports = [(child, validate_pack_dir(child)) for child in children]
        shared = check_pack_key_uniqueness(reports)
        collected: list[Finding] = list(shared)
        for _, report in reports:
            collected.extend(report.findings)
        if as_json:
            print(json.dumps([finding.as_dict() for finding in collected], indent=2))
        else:
            for child, report in reports:
                print(f"  {child}")
                print(render_text(report))
            for finding in shared:
                print(f"  {finding.severity:<6} {finding.file}  {finding.field}")
                print(f"         {finding.message}")
                print(f"         {finding.fix}")
        return 1 if any(item.severity == ERROR for item in collected) else 0
    except Exception as exc:  # the validator itself failed -- spec 3 decision 2
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""YAML directory loader for casepacks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.casepack.models import Casepack


class CasepackLoadError(ValueError):
    """Raised when a casepack file cannot be parsed or validated."""


def _read_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f":{mark.line + 1}" if mark is not None else ""
        raise CasepackLoadError(f"{path.name}{location}: yaml parse error") from exc


def _required(pack_dir: Path, relative: str) -> Any:
    path = pack_dir / relative
    if not path.exists():
        raise CasepackLoadError(f"{relative}: missing file")
    return _read_yaml(path)


def _load_preferences(pack_dir: Path) -> dict[str, Any]:
    pref_dir = pack_dir / "preferences"
    if not pref_dir.exists():
        raise CasepackLoadError("preferences: missing directory")
    data: dict[str, Any] = {}
    for path in sorted(pref_dir.glob("*.yaml")):
        data[path.stem] = _read_yaml(path)
    if not data:
        raise CasepackLoadError("preferences: no yaml files")
    return data


def load_casepack(pack_dir: str | Path) -> Casepack:
    root = Path(pack_dir)
    raw = {
        "metadata": _required(root, "pack.yaml"),
        "strategies": _required(root, "strategies.yaml"),
        "capabilities": _required(root, "capabilities.yaml"),
        "catalog": _required(root, "catalog.yaml"),
        "platform": _required(root, "platform.yaml"),
        "entities": _required(root, "entities.yaml"),
        "watch_rules": _required(root, "watch_rules.yaml"),
        "events": _required(root, "events.yaml"),
        "stakeholders": _required(root, "stakeholders.yaml"),
        "preferences": _load_preferences(root),
        "policies": _required(root, "policies.yaml"),
        "questions": _required(root, "questions.yaml"),
        "labels": _required(root, "labels.yaml"),
    }
    try:
        return Casepack.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first["loc"])
        raise CasepackLoadError(f"{field}: {first['msg']}") from exc

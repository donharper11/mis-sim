"""Validated, immutable runtime casepack registry."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.platform import Casepack
from app.simulation.content import load_runtime_pack
from app.simulation.types import RuntimePackV1
from .validate import ERROR, validate_pack_dir


class RegistryError(ValueError):
    """A pack cannot be registered or no longer matches its registry pin."""


class RegistryIntegrityError(RegistryError):
    pass


_CACHE: dict[tuple[str, str], RuntimePackV1] = {}


def pack_root(root: str | Path | None = None) -> Path:
    configured = root or os.environ.get("CASEPACK_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path(__file__).resolve().parents[2] / "packs"


def _path(path: str | Path, root: str | Path | None) -> Path:
    candidate = Path(path).expanduser().resolve()
    base = pack_root(root)
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise RegistryError(f"casepack path must be beneath configured pack root {base}") from exc
    if not candidate.is_dir():
        raise RegistryError(f"casepack directory does not exist: {candidate}")
    return candidate


def _finding_json(item: Any) -> dict[str, Any]:
    return item.as_dict() if hasattr(item, "as_dict") else dict(item)


def _report_json(report: Any) -> dict[str, Any]:
    findings = [_finding_json(item) for item in report.findings]
    return {
        "findings": findings,
        "errors": [item for item in findings if item["severity"] == ERROR],
        "warnings": [item for item in findings if item["severity"] == "WARN"],
        "exit_code": report.exit_code,
    }


def register_casepack(
    session: Session,
    path: str | Path,
    *,
    registered_by: int | None = None,
    root: str | Path | None = None,
) -> Casepack:
    """Validate and atomically stage a runtime-capable pack in the registry.

    The caller owns the surrounding transaction; ``flush`` makes the operation
    atomic with its cohort setup transaction while preserving normal SQLAlchemy
    commit/rollback semantics.
    """
    directory = _path(path, root)
    report = validate_pack_dir(directory)
    report_json = _report_json(report)
    if report.errors:
        raise RegistryError("casepack validation failed: " + "; ".join(item["code"] for item in report_json["errors"]))
    if report.pack is None:
        raise RegistryError("casepack validation produced no typed casepack")
    try:
        runtime_pack = load_runtime_pack(directory)
    except Exception as exc:
        raise RegistryError(f"runtime supplement is invalid: {exc}") from exc
    metadata = runtime_pack.casepack.metadata
    identity = (metadata.pack_key, metadata.pack_version)
    existing = session.scalar(select(Casepack).where(Casepack.pack_key == identity[0], Casepack.pack_version == identity[1]))
    if existing is not None:
        raise RegistryError(f"casepack version {identity[0]} {identity[1]} is already registered; bump pack_version")
    row = Casepack(
        pack_key=identity[0], pack_version=identity[1], pack_digest=runtime_pack.pack_digest,
        schema_version=metadata.schema_version, display_name=metadata.display_name,
        vertical=metadata.vertical, rounds=metadata.rounds, path=str(directory),
        validation_json=report_json, registered_by=registered_by,
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise RegistryError(f"casepack version {identity[0]} {identity[1]} is already registered; bump pack_version") from exc
    return row


def resolve_runtime_pack(session: Session, pack_key: str, pack_version: str) -> RuntimePackV1:
    """Resolve a registered tuple and verify its immutable on-disk digest."""
    identity = (pack_key, pack_version)
    row = session.scalar(select(Casepack).where(Casepack.pack_key == pack_key, Casepack.pack_version == pack_version))
    if row is None:
        raise RegistryError(f"casepack {pack_key} {pack_version} is not registered")
    cached = _CACHE.get(identity)
    if cached is None:
        try:
            loaded = load_runtime_pack(row.path)
        except Exception as exc:
            raise RegistryIntegrityError(f"registered casepack cannot be resolved: {exc}") from exc
        if (loaded.casepack.metadata.pack_key, loaded.casepack.metadata.pack_version) != identity or loaded.pack_digest != row.pack_digest:
            raise RegistryIntegrityError(f"registered casepack {pack_key} {pack_version} failed identity or digest verification")
        _CACHE[identity] = loaded
        cached = loaded
    elif cached.pack_digest != row.pack_digest or (cached.casepack.metadata.pack_key, cached.casepack.metadata.pack_version) != identity:
        raise RegistryIntegrityError(f"registered casepack {pack_key} {pack_version} failed registry integrity verification")
    return cached


def clear_cache() -> None:
    _CACHE.clear()


async def aresolve_runtime_pack(session: AsyncSession, pack_key: str, pack_version: str) -> RuntimePackV1:
    row = await session.scalar(select(Casepack).where(Casepack.pack_key == pack_key, Casepack.pack_version == pack_version))
    if row is None:
        raise RegistryError(f"casepack {pack_key} {pack_version} is not registered")
    identity = (pack_key, pack_version)
    cached = _CACHE.get(identity)
    if cached is None:
        try:
            loaded = load_runtime_pack(row.path)
        except Exception as exc:
            raise RegistryIntegrityError(f"registered casepack cannot be resolved: {exc}") from exc
        if loaded.pack_digest != row.pack_digest or (loaded.casepack.metadata.pack_key, loaded.casepack.metadata.pack_version) != identity:
            raise RegistryIntegrityError(f"registered casepack {pack_key} {pack_version} failed identity or digest verification")
        _CACHE[identity] = loaded
        cached = loaded
    if cached.pack_digest != row.pack_digest:
        raise RegistryIntegrityError(f"registered casepack {pack_key} {pack_version} failed registry integrity verification")
    return cached


class CasepackRegistry:
    register_casepack = staticmethod(register_casepack)
    resolve_runtime_pack = staticmethod(resolve_runtime_pack)
    clear_cache = staticmethod(clear_cache)

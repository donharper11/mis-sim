"""M2 packet 2.5 registry and runtime binding tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.casepack.registry import RegistryError, RegistryIntegrityError, clear_cache, register_casepack, resolve_runtime_pack
from app.models.platform import Casepack, User

ROOT = Path(__file__).resolve().parents[1]
RIVERSIDE = ROOT / "packs" / "riverside_grocery"
ISOLATION = ROOT / "packs" / "m2_isolation_fixture"


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'registry.db'}")
    User.__table__.create(engine)
    Casepack.__table__.create(engine)
    clear_cache()
    yield engine
    clear_cache()
    engine.dispose()


def test_registers_two_runtime_packs_and_retains_warnings(db):
    with Session(db) as session:
        first = register_casepack(session, RIVERSIDE)
        second = register_casepack(session, ISOLATION)
        session.commit()
        assert (first.pack_key, first.pack_version) == ("riverside_grocery", "0.1.0")
        assert (second.pack_key, second.pack_version) == ("m2_isolation_fixture", "0.1.1")
        assert first.validation_json["exit_code"] == 0
        assert first.validation_json["warnings"] == []
        assert resolve_runtime_pack(session, first.pack_key, first.pack_version).pack_digest == first.pack_digest
        assert resolve_runtime_pack(session, second.pack_key, second.pack_version).casepack.metadata.pack_key == second.pack_key


def test_refuses_errors_duplicates_and_path_escape(db, tmp_path):
    broken = tmp_path / "broken"
    shutil.copytree(ROOT / "tests" / "fixtures" / "packs" / "broken_E19", broken)
    with Session(db) as session:
        with pytest.raises(RegistryError, match="validation failed"):
            register_casepack(session, broken, root=tmp_path)
        with pytest.raises(RegistryError, match="beneath"):
            register_casepack(session, RIVERSIDE, root=tmp_path)
        register_casepack(session, RIVERSIDE)
        session.commit()
        with pytest.raises(RegistryError, match="already registered.*bump pack_version"):
            register_casepack(session, RIVERSIDE)


def test_cache_is_reused_and_digest_mismatch_is_rejected(db, monkeypatch):
    with Session(db) as session:
        row = register_casepack(session, RIVERSIDE)
        session.commit()
        clear_cache()
        import app.casepack.registry as registry
        original = registry.load_runtime_pack
        calls = []
        monkeypatch.setattr(registry, "load_runtime_pack", lambda path: (calls.append(path), original(path))[1])
        assert resolve_runtime_pack(session, row.pack_key, row.pack_version).pack_digest == row.pack_digest
        assert resolve_runtime_pack(session, row.pack_key, row.pack_version).pack_digest == row.pack_digest
        assert len(calls) == 1
        row.pack_digest = "0" * 64
        session.commit()
        with pytest.raises(RegistryIntegrityError):
            resolve_runtime_pack(session, row.pack_key, row.pack_version)

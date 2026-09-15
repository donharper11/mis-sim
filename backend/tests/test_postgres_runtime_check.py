"""Unit checks for the disposable PostgreSQL verifier's strict boundary."""

import pytest

from scripts.check_postgres_runtime import VerificationError, disposable_url


def test_disposable_url_requires_loopback_and_scoped_database():
    url = disposable_url("postgresql://verify_user:verify_pass@127.0.0.1:5432/mis_sim_verify_p5")
    assert url.drivername == "postgresql+asyncpg"
    assert url.database == "mis_sim_verify_p5"
    with pytest.raises(VerificationError):
        disposable_url("postgresql://verify_user:verify_pass@db:5432/mis_sim_verify_p5")
    with pytest.raises(VerificationError):
        disposable_url("postgresql://verify_user:verify_pass@127.0.0.1:5432/other")


def test_disposable_url_rejects_connection_overrides():
    with pytest.raises(VerificationError):
        disposable_url("postgresql://verify_user:verify_pass@127.0.0.1:5432/mis_sim_verify_p5?sslmode=disable")


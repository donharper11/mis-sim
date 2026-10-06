"""Enforce host/member instance integrity without changing assignment semantics."""
from contextlib import contextmanager

from alembic import op
import sqlalchemy as sa

revision = "20261006_0012"
down_revision = "20261004_0011"
branch_labels = None
depends_on = None
NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}


def _preflight(bind):
    checks = (
        ("host_platform", "SELECT h.id FROM host_platform h LEFT JOIN simulation_instance i ON i.instance_id=h.instance_id LEFT JOIN team t ON t.id=h.team_id WHERE i.instance_id IS NULL OR t.id IS NULL OR t.instance_id<>h.instance_id LIMIT 5"),
        ("host_platform_member", "SELECT m.id FROM host_platform_member m LEFT JOIN host_platform h ON h.id=m.platform_id WHERE h.id IS NULL LIMIT 5"),
    )
    for table, sql in checks:
        bad = list(bind.execute(sa.text(sql)).scalars())
        if bad:
            raise RuntimeError(f"Host scope preflight failed: {table} inconsistent IDs {bad}; no rows repaired")


def _fk_name(bind, table, columns):
    matches = [fk for fk in sa.inspect(bind).get_foreign_keys(table) if fk["constrained_columns"] == columns]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {table} FK on {columns}")
    fk = matches[0]
    return fk["name"] or f"fk_{table}_{columns[0]}_{fk['referred_table']}"


@contextmanager
def _sqlite_batch_mode(bind):
    if bind.dialect.name != "sqlite":
        yield
        return
    # PRAGMA changes inside a transaction are silently ignored. Alembic's block
    # commits before entering; preflight has already succeeded, without any DDL.
    with op.get_context().autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=OFF")
        assert bind.exec_driver_sql("PRAGMA foreign_keys").scalar() == 0
    try:
        yield
    finally:
        with op.get_context().autocommit_block():
            bind.exec_driver_sql("PRAGMA foreign_keys=ON")
            assert bind.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            violations = bind.exec_driver_sql("PRAGMA foreign_key_check").fetchmany(5)
            if violations:
                raise RuntimeError(f"Host scope migration left foreign-key violations: {violations}")


def upgrade():
    if op.get_context().as_sql:
        raise RuntimeError("Host scope backfill requires an online migration")
    bind = op.get_bind()
    _preflight(bind)
    team_fk = _fk_name(bind, "host_platform", ["team_id"])
    parent_fk = _fk_name(bind, "host_platform_member", ["platform_id"])
    with _sqlite_batch_mode(bind):
        with op.batch_alter_table("host_platform", naming_convention=NAMING) as batch:
            batch.create_unique_constraint("uq_host_platform_instance_identity", ["id", "instance_id"])
            batch.drop_constraint(team_fk, type_="foreignkey")
            batch.create_foreign_key("fk_host_platform_team_instance", "team", ["team_id", "instance_id"], ["id", "instance_id"], ondelete="CASCADE")
        op.add_column("host_platform_member", sa.Column("instance_id", sa.Integer(), nullable=True))
        bind.execute(sa.text("UPDATE host_platform_member SET instance_id=(SELECT h.instance_id FROM host_platform h WHERE h.id=host_platform_member.platform_id)"))
        with op.batch_alter_table("host_platform_member", naming_convention=NAMING) as batch:
            batch.alter_column("instance_id", existing_type=sa.Integer(), nullable=False)
            batch.drop_constraint(parent_fk, type_="foreignkey")
            batch.create_foreign_key("fk_host_platform_member_instance", "simulation_instance", ["instance_id"], ["instance_id"], ondelete="CASCADE")
            batch.create_foreign_key("fk_host_platform_member_platform_instance", "host_platform", ["platform_id", "instance_id"], ["id", "instance_id"], ondelete="CASCADE")


def downgrade():
    bind = op.get_bind()
    with _sqlite_batch_mode(bind):
        with op.batch_alter_table("host_platform_member", naming_convention=NAMING) as batch:
            batch.drop_constraint("fk_host_platform_member_platform_instance", type_="foreignkey")
            batch.drop_constraint("fk_host_platform_member_instance", type_="foreignkey")
            batch.drop_column("instance_id")
            batch.create_foreign_key("fk_host_platform_member_platform", "host_platform", ["platform_id"], ["id"], ondelete="CASCADE")
        with op.batch_alter_table("host_platform", naming_convention=NAMING) as batch:
            batch.drop_constraint("fk_host_platform_team_instance", type_="foreignkey")
            batch.create_foreign_key("fk_host_platform_team", "team", ["team_id"], ["id"], ondelete="CASCADE")
            batch.drop_constraint("uq_host_platform_instance_identity", type_="unique")

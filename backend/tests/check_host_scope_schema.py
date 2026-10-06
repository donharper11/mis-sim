"""Host-only extension; original nineteen-table restrictive guard stays unchanged."""
import ast
from pathlib import Path

from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import visitors
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql import operators
from app.models.host_platform import HostPlatform
from app.models.base import Base
import app.models.platform  # register FK targets


def assert_metadata(metadata):
    for name in ("host_platform", "host_platform_member"):
        table = metadata.tables[name]
        column = table.c.get("instance_id")
        assert column is not None and not column.nullable, f"{name}: non-null instance scope required"
        fks = {(tuple(c.name for c in fk.columns), tuple(e.target_fullname for e in fk.elements), fk.ondelete) for fk in table.foreign_key_constraints}
        assert (("instance_id",), ("simulation_instance.instance_id",), "CASCADE") in fks, f"{name}: direct instance FK missing"
        expected = (("team_id", "instance_id"), ("team.id", "team.instance_id"), "CASCADE") if name == "host_platform" else (("platform_id", "instance_id"), ("host_platform.id", "host_platform.instance_id"), "CASCADE")
        assert expected in fks, f"{name}: composite instance FK missing"
    host = metadata.tables["host_platform"]
    assert any(isinstance(c, UniqueConstraint) and tuple(x.name for x in c.columns) == ("id", "instance_id") for c in host.constraints), "host identity unique missing"


def assert_member_join(join):
    pairs = {frozenset((str(node.left), str(node.right))) for node in visitors.iterate(join) if isinstance(node, BinaryExpression) and node.operator is operators.eq}
    assert frozenset(("host_platform.id", "host_platform_member.platform_id")) in pairs
    assert frozenset(("host_platform.instance_id", "host_platform_member.instance_id")) in pairs


def assert_query_scope(source, function):
    tree = ast.parse(source)
    node = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function)
    comparisons = [n for n in ast.walk(node) if isinstance(n, ast.Compare) and any(isinstance(op, ast.Eq) for op in n.ops)]
    assert any(ast.unparse(c.left) == "HostPlatformMember.instance_id" for c in comparisons), f"{function}: explicit member instance predicate missing"


def main():
    assert_metadata(Base.metadata)
    assert_member_join(HostPlatform.members.property.primaryjoin)
    api = Path(__file__).parents[1] / "app" / "api"
    assert_query_scope((api / "runtime_host_platform.py").read_text(), "remove_member")
    assert_query_scope((api / "runtime_rollout.py").read_text(), "_build_platform_map")
    print("host scope guard green: two host tables, scoped member queries and composite ORM join")


if __name__ == "__main__":
    main()

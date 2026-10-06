"""The host guard must reject structural defects, not just invalid data."""
from pathlib import Path
import pytest
from sqlalchemy import MetaData
from app.models.host_platform import HostPlatform, HostPlatformMember
from app.models.base import Base
from check_host_scope_schema import assert_metadata, assert_member_join, assert_query_scope, main


def test_current_host_guard():
    main()


@pytest.mark.parametrize('plant', ['column', 'nullable', 'direct', 'composite'])
def test_metadata_guard_rejects_planted_defect(plant):
    metadata = MetaData()
    for table in Base.metadata.tables.values():
        table.to_metadata(metadata)
    member = metadata.tables['host_platform_member']
    if plant == 'column':
        member._columns.remove(member.c.instance_id)
    elif plant == 'nullable':
        member.c.instance_id.nullable = True
    else:
        target = 'simulation_instance' if plant == 'direct' else 'host_platform'
        fk = next(fk for fk in member.foreign_key_constraints if fk.referred_table.name == target)
        member.constraints.remove(fk)
        for element in fk.elements:
            member.foreign_keys.remove(element)
            element.parent.foreign_keys.remove(element)
    with pytest.raises(AssertionError):
        assert_metadata(metadata)


@pytest.mark.parametrize('file,function,removed', [
    ('runtime_host_platform.py', 'remove_member', 'HostPlatformMember.instance_id == instance.instance_id,'),
    ('runtime_rollout.py', '_build_platform_map', 'HostPlatformMember.instance_id == instance_id,'),
])
def test_query_guard_rejects_removed_predicate(file, function, removed):
    source = (Path(__file__).parents[1] / 'app' / 'api' / file).read_text()
    assert removed in source
    assert_query_scope(source, function)
    with pytest.raises(AssertionError):
        assert_query_scope(source.replace(removed, ''), function)


@pytest.mark.parametrize('join', [HostPlatform.id == HostPlatformMember.platform_id, HostPlatform.instance_id == HostPlatformMember.instance_id])
def test_join_guard_rejects_either_missing_equality(join):
    with pytest.raises(AssertionError):
        assert_member_join(join)

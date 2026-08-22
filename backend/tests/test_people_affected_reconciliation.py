"""Reconciliation guard for `people_affected` (finding CU-004).

`people_affected` had three homes: `catalog.yaml` (`<item>.people_affected.count`, the
authored population), the R3 seed (`seeds/riverside_r3.py`, one per `DeploymentState`), and
`PROVENANCE.md §11`. The seed's copy is **the value the org scorer actually divides by** --
`organisation.py`: `training = trained_count / people_affected` -- so if the seed and the
catalog drift, the score is computed against a number the authored pack does not carry, and
nothing catches it.

The reconciliation rule (1.6 spec §3 decision 8, `SPEC_PROTOCOL §3`): the catalog is
authoritative, and every seeded deployment's `people_affected` must equal the count of its
`catalog_key`'s catalog item. 1.6 is to DERIVE the deployment figure from the catalog and
delete the duplicate home; until then this guard fails on any drift.

It exercises the real loaded pack and seed via `app.seed.demo.load_scenario`, the same
fixture the 1.4 pin and raw-fit tests use.
"""
from __future__ import annotations

from app.seed.demo import load_scenario


def test_seed_people_affected_matches_the_catalog():
    pack, state = load_scenario("riverside_r3")
    catalog = {item.key: item for item in pack.catalog}

    mismatches: list[str] = []
    for dep in state.deployments:
        item = catalog.get(dep.catalog_key)
        assert item is not None, f"{dep.key} names catalog_key '{dep.catalog_key}', not in the catalog"
        authoritative = item.people_affected.count
        if dep.people_affected != authoritative:
            mismatches.append(
                f"{dep.key}: seed people_affected={dep.people_affected} but catalog "
                f"'{dep.catalog_key}'.people_affected.count={authoritative}"
            )

    assert not mismatches, (
        "seeded people_affected disagrees with the authoritative catalog (finding CU-004); "
        "the org scorer would divide by a number the pack does not carry:\n  " + "\n  ".join(mismatches)
    )


def test_guard_is_non_vacuous():
    """There are deployments to check, and each carries a catalog_key -- so the assertion
    above is exercised, not passing over an empty set."""
    _pack, state = load_scenario("riverside_r3")
    assert state.deployments, "no deployments seeded; the reconciliation guard would be vacuous"
    assert all(dep.catalog_key for dep in state.deployments)

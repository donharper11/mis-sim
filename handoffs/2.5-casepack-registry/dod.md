# M2 packet 2.5 — casepack registry DoD

Implementation is bounded by `handoffs/recovery/m2-registry-amendment.md` and
`handoffs/recovery/m2-registry-dispatch.md`.

| Requirement | Evidence | Status |
|---|---|---|
| Metadata-only registry, unique tuple, no `instance_id` | `check_casepack_registry_schema.py` | PASS |
| Reversible migration | SQLite upgrade → downgrade → upgrade | PASS |
| Riverside and copied runtime-capable isolation pack | `test_casepack_registry.py` | PASS |
| Error, duplicate, path, cache and digest negatives | `test_casepack_registry.py` | PASS |
| Numeric E19 diagnostics and no E00 collapse | `broken_E19`, fixture matrix | PASS |
| Operations rule documented | `docs/casepack-operations.md` | PASS |
| Full repository gate and independent audit | supervisor evidence | pending |

The copied isolation pack is a distinct fixture tuple, not a substantive Phase 6
vertical. Auth, scheduling, UI, and pack authoring remain out of scope.

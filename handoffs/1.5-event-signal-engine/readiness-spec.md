# 1.5 readiness closeout — schema and validator prerequisite

**Role:** prerequisite build, not the 1.5 event engine  
**Base:** `main` after merge commit `cedd61f`  
**Governing spec:** `handoffs/1.5-event-signal-engine/spec.md` v1.2

## Purpose

Close the last structural gate before the 1.5 builder is dispatched. Do not implement
signals, events, metrics, blast radius, or seed history in this packet.

## Frozen changes

1. Add `placement: Literal["on_prem", "cloud", "saas"] | None` and
   `other_policy: SnakeKey | None` to `EventPrecondition`.
2. Define one canonical `PRECONDITION_TYPES` set containing exactly the eleven names in
   1.5 §5.2.
3. Validate each type's required fields and reject fields belonging to another type.
   `placement_count` requires `placement` and `count`; `policy_contradiction` requires
   `policy` and `other_policy`. A missing, unknown or extra-for-type field is an error.
4. Change W08 from a global six-card constant to `pack.metadata.rounds`. Empty
   `strategy_affinity` continues to count for every strategy and continues to raise W03.
5. Update the validator spec/code list, messages, fixtures, `docs/casepack-schema.md`, and
   `findings/OPEN-REGISTER.md` in the same change. Do not add a Riverside-only branch.

## Pre-flight

Run from the repository root and stop on any failure:

```bash
git rev-parse --verify main
sed -n '/class EventPrecondition/,/class EventOutcome/p' backend/app/casepack/models.py
grep -n 'W08_MIN_DRAWS' backend/app/casepack/validate.py
cd backend && PYTHONPATH=. bin/validate_casepack packs/riverside_grocery
```

Expected: the model has the ten pre-closeout fields but lacks `placement` and
`other_policy`; W08 is still a flat constant; Riverside is 0 errors / 0 warnings.

## Verification and DoD

| Item | Required evidence |
|---|---|
| Both fields load and round-trip | focused model test |
| All eleven valid shapes load and validate | table-driven positive test |
| Unknown type rejected | negative fixture/test with stable code |
| Missing required field rejected | one case per type |
| Field from another type rejected | table-driven negative test |
| W08 uses `pack.metadata.rounds` | a four-round pack with four draws passes and three draws warns |
| Empty affinity semantics unchanged | counts for every strategy and still emits W03 |
| Existing validator contract preserved | fixture matrix passes; I1/I5 set equality passes |
| Riverside remains clean | text 0/0 and JSON `[]` |
| Full backend suite | all tests pass |
| Scope | `git diff --check`; no engine implementation files changed |

The corrected branch requires an independent audit before merge. Only after it merges may
the 1.5 engine builder run spec v1.2 pre-flight rows 1–11.

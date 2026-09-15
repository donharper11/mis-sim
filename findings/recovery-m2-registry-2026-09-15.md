# M2 packet 2.5 casepack-registry independent audit

- Candidate: `67a034d0a86c978b1acc0b9566a29555e94b93d2`
- Amended base: `443d606` (cumulative M2 registry dispatch from merged M2.2)
- Verdict: **PASS**

## Scope

The candidate changes are within the amended registry allowlist: migration,
platform metadata/service binding, registry and simulation adapter, validator
E19 follow-up, the copied runtime-capable isolation pack, E19 fixture, focused
registry/schema/matrix tests, operations documentation, quality gate, validator
spec, and registry DoD. `git diff --check 443d606..2774f4b` passed. No auth,
scheduling, frontend, engine/scoring, transition, or runtime-scope migration
paths changed.

## Independent evidence

- `backend/tests/test_casepack_registry.py`: **3 passed**. Riverside and the
  copied `m2_isolation_fixture` register and resolve as distinct tuples; ERROR,
  duplicate, and path-escape registration attempts refuse; cache parse-once
  behavior is proven; registry digest mismatch raises `RegistryIntegrityError`.
- `backend/tests/check_casepack_registry_schema.py` passed: metadata-only
  `casepack` schema, unique `(pack_key, pack_version)`, no `instance_id`, and
  `simulation_instance.pack_digest` present.
- `backend/tests/check_fixture_matrix.py` passed all 45 fixture cases. The
  implemented/spec code sets and four variants are equal; E19 reports the
  field path and does not collapse to E00; directory and single-pack JSON/text
  outputs are identical.
- Fresh SQLite Alembic `upgrade head`, `downgrade 20260915_0005`, and
  `upgrade head` all passed. Final head was `20260915_0006`; the casepack table
  had the exact metadata columns and the instance digest column was present.
- Fresh migrated SQLite `python -m app.seed.demo --cohort` registered and
  bound both runtime-capable tuples. Persisted registry and instance rows had
  64-character digests; instances were
  `riverside_grocery@0.1.0` and `m2_isolation_fixture@0.1.1`; counts were
  2 sections, 2 instances, 4 teams, and 16 enrollments.
- Direct binding probe confirmed setup binding copies a semantic digest and
  setup rebinding changes the pinned tuple. Binding after round 1 is refused.
  Unregistered resolution is refused by the registry; digest and identity
  checks occur before cache insertion.
- Existing 2.2 guards remained green: the 19-table instance-scope schema guard
  passed and `test_instance_isolation.py` passed (**1 passed**).

The registry stores no pack content, resolves through the typed immutable
`RuntimePackV1`, caches by tuple, verifies the semantic digest, and keeps the
instance binding digest alongside the existing pack identity. No implementation
or shared contract files were modified by this audit.


## Final successor audit — `67a034d0a86c978b1acc0b9566a29555e94b93d2`

**Final verdict: PASS.** Relative to `2774f4b`, this successor changes only
the allowlisted `backend/app/seed/demo.py`. It makes the migrated `--cohort`
seed register Riverside and the copied isolation pack before creating the two
instances, while retaining synthetic tuples for pre-registry isolated fixtures.
No non-allowlisted path changed.

Independent reruns on this exact HEAD found:

- registry focused tests: **3 passed**;
- registry schema guard: **PASS**;
- validator fixture matrix: all **45** fixtures passed with I1/I1v set
  equality and E19 field diagnostics;
- fresh migrated SQLite `--cohort`: registry and instance rows for both
  runtime-capable tuples, each with a 64-character digest, and counts of
  2 sections, 2 instances, 4 teams, and 16 enrollments.

`git diff --check 443d606..67a034d` passed. The final candidate was clean
before this report update.

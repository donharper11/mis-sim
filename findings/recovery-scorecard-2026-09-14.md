# Recovery scorecard implementation audit

Date: 2026-09-14. Dispatch base: `c7283dc27eb0d0bf5178765d81274e5bf66ad546`.
Implementation: `5f5b09eef6e5159595d69a8858807c44db760ed5`.
Final candidate: `ad5de38a5aa5a79106c984b6038c1df62faecf98` (only DoD added).
Spec author: `scorecard_author`; independent spec reviewer: `report_auditor`.
Builder: `scorecard_builder`; fresh independent build auditor: `scorecard_auditor`.
Supervisor independently reviews and integrates; it does not claim to supply the
fresh auditor's independent role. Reviewed R1–R4 authority and exact scope:
[contract](../handoffs/recovery/scorecard-contract/spec.md),
[review](../handoffs/recovery/scorecard-contract/review.md),
[dispatch](../handoffs/recovery/scorecard-contract/dispatch.md).

## Independent verdict — ACCEPT

The fresh auditor accepted final candidate `ad5de38` and the exact eight-document
living patch, with no open build findings. Its complete returned record is preserved
in [audit.md](../handoffs/recovery/scorecard-contract/audit.md); this summary is a
supervisor transcription, not a substitute for that independent role.

Independently reproduced: **311 tests, all guards, 44 fixtures**; the historical base
from a fresh exact-commit archive; 251 compatible shipped event rows; 24 newly persisted
results and all 96 scorecard values; actual PostgreSQL migrations/six committed rows;
historical JSON immutability; unchanged bytes for all 1,021 other tracked candidate
files. It reran all **34** builder regression plants and authored **three** additional
plants (invalid base, omitted unbound-event points, skipped unfired-event validation).
Every plant caused a named behavior-test failure, with no collection/import error
accepted as proof. An additional 1,000 deterministic arithmetic/permutation cases passed.

The auditor also verified DoD artifact hashes and the living §7 patch, including
independent closure/falsification of the two corrected schema links (SC-A-001).

## Supervisor reproduction and integration

The supervisor read every production change and the regression tests against the
reviewed contract. Only EventOutcome validation, the runner's scorecard boundary,
one existing event-once test, the new contract tests and the DoD changed on the
builder branch. Shared §7 documents are supervisor-owned and accompany integration.
No pure-engine, casepack, seed, migration, dependency, UI or auth change is included.

Before product edits, the supervisor separately captured the actual engine bases/status
and all **24 persisted results** across four scripted teams and six rounds. It reran
the actual persistence path on frozen `5f5b09e`, comparing every non-scorecard payload
field exactly and computing all **96** corrected perspective values from the retained
old base and raw event evidence. All comparisons pass. The supervisor also compared
**44 protected engine/pack/seed/pin files** against its pre-edit hashes: unchanged.
This is additional independent evidence; the builder's larger protected-file inventory
and before/after comparison are separately recorded in its DoD.

A new supervisor-owned PostgreSQL database was migrated before seeding. The actual
runtime verifier confirmed PostgreSQL **16.15**, Alembic head **20260822_0002**, **16**
scoped runtime tables and **six committed round results**. A separate psycopg2 reader
verified all 24 perspective values are finite/bounded, metadata version/types/units,
actual partial status, and reconciliation with base/raw points. Only that newly created
database was dropped after capture; no application database or shared service was used.

Independent supervisor commands (declared-dependency interpreter):

```bash
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-supervisor.py \
  /home/ubuntu/projects/mis-sim before /tmp/mis-sim-scorecard-supervisor-evidence
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-supervisor.py \
  /tmp/mis-sim-scorecard-build candidate /tmp/mis-sim-scorecard-supervisor-evidence
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-pg-audit.py \
  /tmp/mis-sim-scorecard-build /tmp/mis-sim-scorecard-supervisor-evidence/postgres-candidate.log
```

The first command captured the unchanged `c7283dc` runtime before product edits;
rerun that revision in a fresh checkout when reproducing baseline evidence. Before artifacts are never overwritten.
For durable candidate regression checks, run `make check` or
`PYTHONPATH=backend python -m pytest backend/tests/test_scorecard_contract.py -q`.
The new test's unaffected-payload hash was independently confirmed against the
supervisor's pre-edit artifact, rather than derived from the corrected implementation.
The actual PostgreSQL setup/verifier recipe remains in `docs/backend-development.md`;
its disposable database must be new and empty. Builder detail and mutation mapping:
[DoD](../handoffs/recovery/scorecard-contract/dod.md).

Supervisor artifact SHA256:

| Artifact | SHA256 |
|---|---|
| `before.json` | `ad8a72559a74825cfe0c3121419d1c7292925d8b87bff497f09de519bb785209` |
| `candidate.json` | `39a597b358f4dae0521dea7b781bce3d25f8e15f2925a850987811c1f3e65445` |
| `postgres-candidate.log` | `0868b85fbdfb2dd733c167bd9023b08c76d13a2ebfb1a60fef8471176830b6b2` |

On the combined checkout, `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check`
passed: **311 pytest tests, every guard and all 44 fixtures**. Log:
`/tmp/mis-sim-scorecard-supervisor-evidence/make-check-integrated.log`.
The supervisor also compared all five candidate files byte-for-byte with `ad5de38` and
all eight living documents against the fresh auditor's accepted SHA256 records: exact
matches. The SC-A-001 closing assertion passes on this checkout. Status/register/audit
updates accompany that exact code and contract patch in the same integration commit.

Cleanup completed after all PostgreSQL proofs: supervisor and auditor each removed
only their own database; the builder removed its two retained verification databases,
verified their absence, stopped/removed only its private cluster and deleted its private
metadata/password. The supervisor independently confirmed the cluster path and private
metadata are absent and port 53037 is closed. Non-secret evidence, clean candidate
worktree and declared-dependency interpreter remain available. No shared service,
application database, main branch or remote was changed.

## Numerical result and compatibility

| Balanced R1 | Engine base | Event points | Historical stored value | Corrected fraction |
|---|---:|---:|---:|---:|
| Financial | 0.966932 | -27 | -26.033068 | **0.696932** |
| Customer | 0.6083 | 0 | 0.6083 | **0.6083** |
| Internal Process | 0.493523 | -18 | -17.506477 | **0.313523** |
| Learning & Growth | 0.439272 | -7 | -6.560728 | **0.369272** |

The formula is `round(clamp(base + sum(points)/100, 0, 1), 6)`; conversion and bounds
apply once after aggregation. Raw event outcomes remain unchanged, including outcomes
of fired events with no bound node. Firm realised value remains **0.35825**. Every
other field across all 24 payloads is unchanged. New metadata preserves actual base,
point totals and `financial_partial`; old unversioned stored JSON is unchanged.

- Historical full score digest: `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`.
- Corrected v1 full score digest: `0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`.

The digest still includes every BSC value, so the correction necessarily changes it.
Its formula and historical evidence are preserved; this is not a new calibration ruling.

## Findings and retained limits

During early supervisor review, omitting the private helper's event-record argument
raised TypeError instead of the contract's required ValueError. The builder supplied
its explicit absent-input default and regression before code freeze; the test and
its corresponding mutation both cover that correction.

**SC-A-001 — Report — CLOSED before integration.** The initial supervisor schema
changelogs named CONTRACTS without the links required by §7. Both relative links now
point to its scorecard entry. The fresh auditor independently verified the links and
detected removal of each; its executable closing command is in the preserved audit.
This closed finding is recorded alongside NS-003 in the open register.

NS-003 closes with the audited code, living contracts and this record in one integration
commit. SC-SR-001/002 are verified in implementation as well as spec. M0's runtime,
reporting and numeric-boundary exits are complete on `build/north-star-foundation`.

M1 still owns missing decision validation/state evolution, atomic advance/retry/unlock,
and event-to-estate/cash semantics. Invalid derived output stops result/ledger/pointer
publication, but earlier arrivals/debt still depend on caller rollback; no new atomicity
claim is made. The Financial proxy remains partial, with full scoring owned by M4.
Numeric load diagnostics remain OS-D1/M2; fixture coverage remains 38/39 codes with
I8 explicitly unfixturable. All four scripted archetypes declare Cost Leadership;
no all-strategy balance, live decision-driven game, browser/auth or pilot readiness is
claimed. Browser/visual rungs are N-A for this headless numerical boundary.

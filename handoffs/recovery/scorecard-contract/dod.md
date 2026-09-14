# Recovery scorecard contract — builder evidence

Date: 2026-09-14. Builder: `scorecard_builder`. Branch: `build/recovery-scorecard`.
Dispatch base: `c7283dc27eb0d0bf5178765d81274e5bf66ad546`.
Tested implementation candidate: **`5f5b09eef6e5159595d69a8858807c44db760ed5`**.
This report is the only subsequent builder change; its containing commit is the final
submitted candidate. The supervisor receives that exact SHA separately after commit.
No independent build-audit or integration PASS is claimed by the builder.

R1–R4 are APPROVED in [review.md](review.md). Independent spec reviewer
`report_auditor` returned PASS on `0716eb9e49f9dbe38d0505dca81f42a8c3ee3ca8` after
SC-SR-001/002 corrections. Dispatch explicitly authorized implementation, including the
supplied runtime path. The existing applicable CONTRACTS rule is: **“every query that
reads or writes game state filters on it.”** No query or persistence key was added or
changed. The new scorecard contract is the reviewed §7 integration delta, owned by the
supervisor; this builder does not claim it is already LIVE in the shared documents.

Read directly: root governance, quality/spec protocols and CONTRACTS; north-star plan;
the approved scorecard spec/review and independent review findings; the engine rollup,
score record, runner, round JSON model/session, event models/loader, vocabulary/load-error
dispatch, all scorecard consumers, report/harness and their guards/tests, scoring/round
pins, seed helpers, Riverside event outcomes/initial scorecard, Makefile, and the audited
runtime recipe/verifier. The integrated report's new consumers index the same four
numeric fields. No unidentified consumer or unresolved scoring semantics was found.

Evidence directory (retained for audit):
`/tmp/mis-sim-scorecard-evidence-5sicqch4/`.
Interpreter: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`.
Commands below were run from `/tmp/mis-sim-scorecard-build` unless noted.
The before artifact was captured **before any implementation edits** and never regenerated.

## Preflight — reported to supervisor before edits

| Row | Result | Actual evidence |
|---|---|---|
| PF1 | PASS | Spec probe A: `PF1/PF4 source assertions PASS; 6 source/consumer plants detected`. Read complete producer/runner functions and JSON storage. `pf1.sh`, `pf1.log`. |
| PF2 | PASS | Spec probe B: 24 old results; historical digest `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`; two corrupt-result plants detected. Saved `before.json`; no overwrite/recreation. `pf2.sh`, `pf2.log`. |
| PF3 | PASS | Spec probe C: **251** existing event rows compatible; **8** invalid input plants rejected with the expected Pydantic error type. Existing Literal/enum dispatch yields E18; numeric E00 remains the accepted OS-D1/M2 residue. `pf3.sh`, `pf3.log`. |
| PF4 | PASS | Exact spec `rg` over backend/app, frontend/src and tests saved as `pf4-consumers.log`. No frontend consumer; the six source/consumer plants include a frontend-consumer plant. Integrated report/harness explicitly read the four dimensions; the one raw-addition test is the only existing test changed. |
| PF5 | PASS | `cd backend && PYTHONPATH=. /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest tests/test_engine_scoring.py tests/test_round_pin.py -q`: **14 passed**. `pf5.log`. |
| PF6 | PASS | Audited runtime `4adafd8` and report `94b85e7` included in exact base. Ran actual docs cluster recipe and supplied verifier, not an application DB default. Python **3.12.3**, pip check **No broken requirements found**, PostgreSQL **16.15**; migrated head **20260822_0002**, verified all **16** non-null integer instance-scoped runtime tables and six committed results from a new reader session. `pf6.sh`, `pf6.log`. |

Old Balanced R1 engine base was `{financial: 0.966932, customer: 0.6083,
internal_process: 0.493523, learning_growth: 0.439272}`, with partial flag True.
Old scorecard was `{financial: -26.033068, customer: 0.6083,
internal_process: -17.506477, learning_growth: -6.560728}`.
The spec's small acceptance probe was also run before edits: exit **1**, specifically
`AssertionError: expected scorecard + metadata` (`acceptance.log`). This is the expected
red probe, not a failed preflight dependency.

Recorded preflight invocations were `bash <evidence>/pf1.sh`, `pf2.sh`, `pf3.sh`, and
`pf6.sh`, with the declared interpreter's bin prepended to PATH. The first three scripts
are verbatim spec probes, apart from the fresh before-artifact path in B. A/B assert the
**old** implementation and must be reproduced on the dispatch base, not on the candidate.

PF6 followed `docs/backend-development.md` exactly with task-specific directory/role:

```bash
export PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH
python --version
python -m pip check
runtime_pg_bin=/usr/lib/postgresql/16/bin
"$runtime_pg_bin/initdb" --version
runtime_pg_root=$(mktemp -d /tmp/mis-sim-scorecard-pg.XXXXXX)
mkdir "$runtime_pg_root/socket"
runtime_pg_user=scorecard_verify
runtime_pg_password=$(python -c 'import secrets; print(secrets.token_hex(16))')
runtime_pg_port=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
runtime_pg_database="mis_sim_verify_$(python -c 'import secrets; print(secrets.token_hex(8))')"
printf '%s\n' "$runtime_pg_password" > "$runtime_pg_root/password"
chmod 600 "$runtime_pg_root/password"
for runtime_pg_key in ${!PG@}; do unset "$runtime_pg_key"; done
"$runtime_pg_bin/initdb" -D "$runtime_pg_root/data" -U "$runtime_pg_user" \
  --auth-local=scram-sha-256 --auth-host=scram-sha-256 \
  --pwfile="$runtime_pg_root/password"
"$runtime_pg_bin/pg_ctl" -D "$runtime_pg_root/data" -l "$runtime_pg_root/postgres.log" \
  -o "-h 127.0.0.1 -p $runtime_pg_port -k $runtime_pg_root/socket" -w start
PGPASSWORD="$runtime_pg_password" "$runtime_pg_bin/createdb" \
  -h 127.0.0.1 -p "$runtime_pg_port" -U "$runtime_pg_user" -T template0 "$runtime_pg_database"
runtime_database_url="postgresql+asyncpg://$runtime_pg_user:$runtime_pg_password@127.0.0.1:$runtime_pg_port/$runtime_pg_database"
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python backend/scripts/check_postgres_runtime.py \
  --database-url "$runtime_database_url"
```

Passwords are generated locally and read from the private password file; no secret is
included in this report or logs. This command creates a **new** cluster/database when
reproduced. Never rerun the verifier on either populated evidence database.

## Implementation and verification

`EventOutcome.scorecard` now uses the closed `ScorecardPerspective` Literal and strict
integers, with a finite-point validator. The runner reconstructs raw mappings and checks
every pack event before sheet validation/writes, including events that will not fire.
It validates the base, status, records and aggregate; sums current-event integer points,
divides once by 100, clamps once, rounds to six decimals, and persists the four-number
result plus version/base/totals/partial-status evidence. The omitted helper argument
explicitly follows the reviewed absent-input ValueError path (supervisor clarified its
implementation during review). All fired events contribute, including unbound events.

| DoD item | Result | Evidence |
|---|---|---|
| R1–R4, PF1–PF6, independent spec review | PASS | Ruling, reviewed candidate and per-row outputs above. |
| N1–N4 units/bounds/nulls/invalids/once | PASS | **179 new parameterized cases** in `test_scorecard_contract.py`, plus the updated existing event-once test and unchanged re-entry test. Focused run: **190 passed**. Literal cases exercise each perspective, both mixed-sign orders, endpoints/precision, money-only/empty outcomes, and finite extreme points. Invalid cases cover every §3.3 class, overflowing totals, missing records argument, and all three mutated-model bypasses on unfired events before writes. Duplicate records fail; inputs remain unchanged. Late invalid base/aggregate refuses result/ledger/pointer publication and caller rollback restores earlier writes. |
| N5 evidence/status/JSON | PASS | Synthetic False **and** True persisted in a fresh reader session; all 24 real results retain actual True status. Metadata is compared with captured engine output and independently summed events. Strict JSON serializes all valid outputs. `test_n5_persisted_status_copies_actual_engine_boolean`, `test_n5_n7_seeded_24_results_metadata_and_business_values`, `compare.py`, and PostgreSQL evidence below. |
| N6–N8 compatibility/core/seeded outcomes | PASS | Two instance/team history cases compare stored JSON text byte-for-byte before/after a new result; no unlock/backfill. All **24** candidate persisted payloads compared exactly against retained `before.json`, excluding only `scorecard` and new `scorecard_meta`. The independently captured unaffected-field hash remains `3ce39114a7c2fb4bce1add36b6e738ce4d553b15505dabdfca68b137457f4e41`; supervisor independently confirmed this against its separate pre-edit capture. |
| Real report and digest | PASS | Actual integrated report rendered from fresh-session persisted results; tests parse **all 96 perspective cells** across four teams/six rounds and compare source values at the existing three-decimal display scale. No rescaling or strict root-payload assumption. Digest sensitivity checks change each of those 96 values individually. `report.txt`, `test_n8_real_report_reads_persisted_fractions_with_metadata`, `test_n8_digest_includes_every_scorecard_value`. |
| Valid packs and diagnostics | PASS | Riverside **0 errors / 0 warnings**; all **44 fixtures** pass. Temporary copied event YAML with unknown dimension yields exactly E18; all tested invalid numerics/null maps refuse loading and retain accepted E00 diagnostics. No shipped pack bytes changed. |
| Required regression gate | PASS | `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check`: **311 pytest tests**, every guard, all 44 fixtures, existing isolation canary and pins PASS. `make-check.log`. Fixture coverage still reports **38 of 39 codes**, with I8 recorded as unfixturable; no new coverage claim. |
| Disposable PostgreSQL | PASS | Before-code and after-code verifier runs use different new databases. The after-code six stored payloads additionally match a separately seeded/captured actual engine run, with base/status and event-total reconciliation from a new PostgreSQL reader. `postgres-after.log`, `postgres-readback.log`, `postgres-after.json`, `postgres-engine-captures.json`. |
| Exact file boundary | PASS | Exact-base §6 scope check passes and detects its protected-file plant. **674** engine/pack/seed/fixture/pin/historical-audit files were compared byte-for-byte with dispatch base; all identical. Three additional real edits to pack, seed and historical-audit files in a detached disposable worktree each made the scope command exit 1. Worktree removed after restoring plants. `protected-bytes.log`, `protected-plants.json`. |
| Living §7 deltas/register reconciliation | PENDING, supervisor | Only five allowed files are in this builder packet. Supervisor applies exact living-document deltas and transitions NS-003 only after fresh audit and its own N7 reproduction. SC-SR-001/002 closing checks are present; OS-D1/M2 and full-Financial M4 ownership remains. |
| Heavy independent build audit | PENDING | Separate fresh auditor; builder does not audit/approve its own packet. |
| Browser/auth/UI/visual rungs | N-A | Headless numerical/persistence boundary; no browser workflow, API route or visual surface added. No browser/screenshot claims. |

Commands and artifacts:

```bash
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest \
  backend/tests/test_scorecard_contract.py backend/tests/test_round_runner.py -q
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH \
  bash /tmp/mis-sim-scorecard-evidence-5sicqch4/acceptance.sh
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python \
  /tmp/mis-sim-scorecard-evidence-5sicqch4/compare.py
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python \
  /tmp/mis-sim-scorecard-evidence-5sicqch4/mutations.py
bash /tmp/mis-sim-scorecard-evidence-5sicqch4/postgres-after.sh
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python \
  /tmp/mis-sim-scorecard-evidence-5sicqch4/postgres-readback.py
bash /tmp/mis-sim-scorecard-evidence-5sicqch4/scope.sh
git diff --check
```

`compare.py` and `postgres-readback.py` intentionally refuse existing local evidence DB
paths; an audit rerun must choose fresh paths and retain the original before artifact.
`postgres-after.sh` always creates a new database; save its new database metadata separately
when auditing. The scripts and their logged original outputs remain available for inspection.
The small probe now prints `unit/bounds/status smoke PASS; 5 evidence plants detected`.

Runtime versions additionally verified: Pydantic 2.10.4, SQLAlchemy 2.0.36, Alembic 1.14.1,
psycopg2-binary 2.9.11, asyncpg 0.30.0, pytest 8.3.5, PyYAML 6.0.2.
Existing capability evidence tuples become JSON arrays on persistence. Full returned-versus-
stored comparisons use the existing JSON representation; scorecard/metadata compare directly.
This is not a changed runtime payload field or codec.

## Actual before/after business reproduction

| Balanced R1 perspective | Engine base | Event points | Old stored value | New stored fraction | New headline points |
|---|---:|---:|---:|---:|---:|
| Financial | 0.966932 | -27 (-12, -15) | -26.033068 | **0.696932** | 69.6932 |
| Customer | 0.6083 | 0 | 0.6083 | **0.6083** | 60.83 |
| Internal Process | 0.493523 | -18 (-8, -4, -6) | -17.506477 | **0.313523** | 31.3523 |
| Learning & Growth | 0.439272 | -7 | -6.560728 | **0.369272** | 36.9272 |

Financial remains partial; firm realised value remains **0.35825**. Ransomware and
staff-account phishing have `node=None`, and their authored scorecard outcomes still
contribute. The ransomware money loss remains separate **100000** outcome evidence.
Do Nothing and All Tech, No Org retain firm realised value **0.0** in all six rounds and
zero Org terms; no ranking requirement is imposed on every BSC perspective.

- Historical full score digest, preserved:
  `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`.
- Corrected v1 full score digest:
  `0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`.

The full hash changes because `score_digest` still includes the corrected four BSC
numbers; capability terms/realised values, firm score, events, financials and **every other
payload field** are unchanged over all 24 results. Metadata is additional evidence and is
not inserted into the historical hash formula. No old expectations/audit findings were edited.

Artifact SHA256:

| Artifact | SHA256 |
|---|---|
| `before.json` | `0f4a68cf3698dde2069cba6a280424ac86c0242f475e8063237c49d3965edab6` |
| `after.json` | `6bb4ca8e05fbf9db601c19a8197cc08d4a80b735149bd54ee4c7cb0eba1e262f` |
| `base-captures.json` | `3808993cef25d7be59bf07862df2f50ac628b18cf95829d74f297e21a4b7300d` |
| `report.txt` | `bb704290d971406ff51553454f5559bade4220e977071f62b3f17af48d6720e4` |
| 674 protected files (path + NUL + bytes + NUL, sorted `git ls-files`) | `dbf1bf594ddd0cfe50fba4ecf1d0e300180ac443a64688d50a68d62fd93320c7` |

## Mutation proof

`mutations.py` copied the actual candidate backend to
`/tmp/mis-sim-scorecard-mutations-i1oqjx_1`, changed one implementation site per run,
ran the named test, required pytest exit **1** with a failed assertion, and restored
that file before the next mutation. No mutation touched the builder worktree.
**34/34 detected**, with individual `mutation-<name>.log` outputs and `mutations.json`.

| Actual regressions planted | Named failing checks |
|---|---|
| Raw addition; divide by 10; divide by 100 twice; sequential clamp; remove lower/upper bound; duplicate application | `test_n1_n2_literal_point_arithmetic` |
| Penalty on absent dimensions | `test_n2_empty_points_and_money_do_not_change_scores` |
| Trust existing Pydantic model; remove early validation | `test_n3_unfired_invalid_outcomes_fail_before_writes` |
| Accept bool; accept unknown key; ignore invalid base; omit argument default | `test_n3_invalid_delta_rejected_by_model_and_runtime`, `test_n3_invalid_delta_map`, `test_n3_invalid_base_rejected`, `test_n3_absent_event_records_refused` |
| Accept duplicate records; mutate input map | `test_n4_duplicate_events_refused_and_inputs_unchanged` |
| Missing/forced-False/forced-True flag; changed base/total; changed either unit string; changed version | `test_n5_persisted_status_copies_actual_engine_boolean` |
| Discard metadata at write; original raw-addition helper behavior | `test_n5_n7_seeded_24_results_metadata_and_business_values` |
| Backfill historical metadata; remove result scope | `test_n6_unversioned_history_remains_byte_identical` |
| Change capability term; firm score; raw event evidence | `test_n6_all_24_unaffected_payload_fields_match_precorrection` |
| Remove BSC from digest | `test_n8_digest_includes_every_scorecard_value` |
| Introduce strict root-payload reader; rescale report values | `test_n8_real_report_reads_persisted_fractions_with_metadata` |

Additionally: the retained-artifact comparison rejected four corrupted payload families
(capability term, firm score, event outcome, financials). The exact-base scope check rejected
three actual protected-file edits (pack, seed, historical audit) and the §6 synthetic path plant.
Historical pin files were never edited. Mutation reports describe detected regressions, not
an independent audit of the builder's own implementation.

## Audit resources and remaining limits

Non-secret PostgreSQL metadata is also saved in `postgres-public.json`:

- Host **127.0.0.1**, port **53037**, role **scorecard_verify**.
- Cluster root `/tmp/mis-sim-scorecard-pg.2Lv4lU`.
- Password file `/tmp/mis-sim-scorecard-pg.2Lv4lU/password` (mode 0600; do not print).
- Before-code database `mis_sim_verify_985451a3ebaced69`.
- After-code database recorded in `after-database.txt` and `postgres-public.json`.
- Private shell metadata `/tmp/mis-sim-scorecard-evidence-5sicqch4/cluster.env` (0600).

The cluster and both databases remain running/intact for audit. The supervisor will create
its own new audit databases; cleanup is coordinated after integration. Do not stop the
cluster or remove the shared supervisor interpreter while another audit needs it. Scoped
cleanup uses the exact documented `dropdb`/`pg_ctl -D <this cluster>/...` targets.

This packet does not implement full Financial scoring, event-to-estate/cash mutation,
decision-driven evolution, transaction/retry/unlock redesign, new schemas or UI/auth.
Invalid pack outcomes fail before any round writes. Invalid derived bases/totals fail before
ledger/result/pointer publication, but earlier arrivals/debt writes still rely on caller
rollback; M1 retains that transaction work. Numeric diagnostic refinement remains
OS-D1/M2; the existing Financial discipline proxy remains explicitly partial under M4.
No calibration tuning, cross-strategy balance verdict, new substantive casepack, push,
main merge or deployment was performed.

# Independent build audit — recovery scorecard contract

Date: 2026-09-14. Auditor: `scorecard_auditor`, fresh and independent of author, spec reviewer, and builder. **Verdict: ACCEPT** for the exact candidate and reviewed living-document patch below. No open build findings. One Report finding was corrected and independently closed before integration.

Dispatch base: `c7283dc27eb0d0bf5178765d81274e5bf66ad546`.
Frozen code commit: `5f5b09eef6e5159595d69a8858807c44db760ed5`.
Final builder commit: **`ad5de38a5aa5a79106c984b6038c1df62faecf98`**.
Independent evidence: `/tmp/mis-sim-scorecard-audit-y6dhzom6/`.

The final commit differs from the frozen code commit only by the new `handoffs/recovery/scorecard-contract/dod.md`. Against the exact dispatch base there are exactly the five allowed files. The candidate worktree is clean. An independent byte comparison verified **all 1,021 other tracked files** against that base, including every pure engine, pack, seed, fixture, historical audit, dependency, and migration file. The separately retained supervisor's 44 protected hashes also match. The builder's 674-file selection was independently reconstructed, including its reported combined SHA256 `dbf1bf594ddd0cfe50fba4ecf1d0e300180ac443a64688d50a68d62fd93320c7`.

The eight supervisor-owned living-document diffs were read completely against recovery spec §7: `CONTRACTS.md`, `design/02-traceability-matrix.md`, `design/03-scoring-frame-options.md`, `docs/casepack-schema.md`, and the 1.1/1.4/1.5/1.6 living specs. Their accepted exact contents and root HEAD are captured in `reviewed-documents.patch` and `reviewed-documents.json` (per-file SHA256). The separately integrated M1 inventory is outside this scorecard build scope. This acceptance does not claim the supervisor's subsequent integration or register reconciliation has already occurred.

Direct review covered `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, relevant `SPEC_PROTOCOL.md` evidence/gate requirements, the authoritative recovery spec/review/dispatch, the complete product diff, complete new test module, changed existing test, complete runner advance/validation/persistence boundaries, pure base/status producers, JSON storage/session and actual PostgreSQL verifier, scorecard consumers, final DoD, and the eight living-document diffs. `AGENTS.md` and `QUALITY.md` are absent; the repository's actual mandatory quality file is `QUALITY_PROTOCOL.md`.

The implementation matches the accepted R1–R4 behavior. Event deltas use strict integer points and the single closed Literal vocabulary. The finite check permits large representable points while rejecting overflow. Every pack outcome is reconstructed into a raw mapping and revalidated before sheet validation or round writes, including mutable-map, model-copy, and model-construct corruption on unfired events. The rollup independently rejects malformed records, missing records, duplicates, invalid bases/status, invalid deltas, and invalid aggregates. It sums integers, divides once by 100, adds the supplied base, clamps once, and rounds to six decimals. It copies the actual engine status, including synthetic False, and persists the four-number result and metadata together. Pure capability scoring, event selection/timing, original evidence and other payload fields remain unchanged.

Independent executable results:

| Obligation | Command/evidence and observed result |
|---|---|
| Required gate; N1–N8 shipped tests, pins, isolation, fixtures | From `/tmp/mis-sim-scorecard-build`: `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check`. Exit 0; **311 passed in 24.69s**, every `check_*.py` guard green, **44 fixtures** behaved as named. Existing coverage is accurately retained as 38 of 39 codes, with I8 unfixturable. Full output: `make-check.log`. |
| PF1/PF4 old producer and consumer facts | Archived the exact dispatch commit into `dispatch-base/`; reran the supplied PF1 script there. **PASS**, six source/consumer plants detected. Inspected production consumers and preserved the distinction between authored initial 0–100 context and runtime scorecard output. |
| PF2 historical result provenance | Ran copied `pf2.sh` against the archived exact base, writing only a new `independent-baseline.json`. **PASS**, two baseline plants detected. Fresh old results equal the builder's retained pre-edit results exactly. Historical digest reproduced. `pf2.log`. Neither retained pre-edit artifact was overwritten. |
| PF3 shipped authoring compatibility | Reran `pf3.sh` with the declared interpreter: **251 shipped event rows compatible; eight invalid plants rejected**. Loader/E18 and accepted numeric-E00 behavior additionally passed the candidate's substantive tests. |
| Expected old failure / new acceptance | The same `acceptance.sh` exits **1** on the exact dispatch archive with `AssertionError: expected scorecard + metadata`; it exits **0** on the candidate with `unit/bounds/status smoke PASS; 5 evidence plants detected`. |
| Fresh independent persisted game proof; N5–N8 | `PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-audit-y6dhzom6/independent.py`. **PASS**. Separately authored script seeds a new SQLite database, captures actual `score_team` output on all 48 calls, verifies all **24** committed payloads from a new session and all **96** final perspectives, compares each authoritative second-pass base/status with retained pre-edit captures, and compares every unaffected payload field with the independently captured supervisor baseline. `independent.log`, `independent-results.json`. |
| Historical immutability | The independent script inserts a real pre-correction payload into another scope before the new game, then compares stored SQL JSON text before/after: **byte-identical**, still unversioned. Shipped tests additionally cover separate instance and team scopes and immutable-result refusal. |
| Additional arithmetic proof | The independent script passes **1,000** deterministic generated examples with independently computed totals, all dimensions, both status values, event-order permutations, input immutability, and saturation. This supplements literal business tests rather than replacing them. |
| Real report and digest | The actual report renders the independently persisted game (`independent-report.txt`). Shipped tests independently verify all 96 report cells and digest sensitivity to each numeric field. The report and digest remain unchanged consumers. |
| PF6 / real PostgreSQL | `PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-audit-y6dhzom6/postgres.py`. **PASS**. Created only `mis_sim_verify_auditor_394cac315d56` on supplied loopback PG16.15; invoked the actual `backend/scripts/check_postgres_runtime.py` with its explicit private URL; migrations reached `20260822_0002`; verified all **16** scoped tables and **six committed rounds**. A separate reader reconciled JSON with actual captured second-pass engine bases, partial status, independent event totals, capabilities and firm score. `postgres.log`, `postgres-results.json`, `postgres-public.json`. |
| PostgreSQL cleanup | The auditor dropped only its own named database and queried the catalog to verify absence. No credentials were printed, sourced, or committed. The auditor left the shared cluster intact; the supervisor subsequently reported the builder's scoped cluster cleanup after all PG proofs completed. |
| DoD provenance | Read final DoD completely; independently matched all four stated artifact SHA256 values, reconstructed the 674-file digest, and compared fresh old/new outputs with the retained builder artifacts. Gate counts, literal values, limits and pending supervisor responsibilities are accurate. DoD's retained-cluster statement records its handoff-time state; later cleanup is separately recorded by the supervisor. |

The actual business reproduction is:

| Balanced R1 | Engine base | Fired points | Persisted result |
|---|---:|---:|---:|
| Financial | 0.966932 | -27 | **0.696932** |
| Customer | 0.6083 | 0 | **0.6083** |
| Internal Process | 0.493523 | -18 | **0.313523** |
| Learning & Growth | 0.439272 | -7 | **0.369272** |

Firm realised value remains **0.35825**, Financial is actually **partial=True**, and unbound ransomware/phishing events still contribute. Money evidence remains separate. The negligent archetypes retain zero firm realised value and zero Org terms across six rounds. The old full digest remains `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`; the corrected v1 digest is `0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`.

Mutation proof was rerun, not accepted from builder logs. After reading `mutations.py`, the auditor copied it with only its evidence destination changed, preserving the original evidence. The script mutated a fresh copy of the actual final candidate. **All 34 plants** exited pytest **1** with the expected named failed test; every resulting log was checked for that named failure and absence of collection/import failures. These cover wrong conversion, sequential clipping, missing bounds, missing-dimension penalties, bypassed validation, malformed acceptance, duplicate application, mutation of inputs, every metadata/status field, persistence, history, scope, pure score/evidence, digest and report regressions. Command: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-audit-y6dhzom6/mutations.py`; evidence: `mutations-run.log`, `mutations.json`, all `mutation-*.log`.

The auditor additionally authored **three distinct implementation plants**, all detected by named behavior failures: return a NaN base instead of rejecting it (**6 failed**); omit scorecard points for unbound events (**1 failed**); skip early validation of unfired round-six events (**6 failed**). Command: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-scorecard-audit-y6dhzom6/extra_mutations.py`; evidence: `extra-mutations.json`, `extra-mutations-run.log`, individual logs. No product worktree was mutated by either mutation run.

**SC-A-001 — Report — CLOSED before integration.** Recovery §7 explicitly requires the two schema changelog entries to link to the living CONTRACTS entry. The initial supervisor diff used only backticked filenames at `docs/casepack-schema.md:680` and `handoffs/1.1-casepack-schema/spec.md:411`. The supervisor supplied actual relative Markdown links. The auditor verified both links, their relative targets and the target heading, then removed each link in memory and observed its closing assertion fail. Both accepted files are included in the saved document hashes. A compact executable closing check is:

```bash
python3 - <<'PY'
from pathlib import Path
root = Path('/home/ubuntu/projects/mis-sim')
for name, prefix in [('docs/casepack-schema.md', '../'),
                     ('handoffs/1.1-casepack-schema/spec.md', '../../')]:
    expected = f'[CONTRACTS.md — scorecard contract v1]({prefix}CONTRACTS.md#eventoutcomescorecard--roundresultpayloadscorecard--live-scorecard-contract-v1)'
    assert expected in (root / name).read_text(), name
print('SC-A-001 closed')
PY
```

No browser/auth/UI/visual rung applies to this expressly headless numerical/persistence packet. This is seeded-estate computation, not a claim of decision-driven gameplay. Full Financial scoring remains M4; numeric diagnostic refinement remains OS-D1/M2; general decision/event estate mutation and transaction/retry redesign remain M1. Late invalid derived output blocks result/ledger/pointer publication, while earlier writes still depend on caller rollback as specified. Those explicit exclusions were preserved, not treated as completed work.

**ACCEPT:** the frozen code, final builder DoD, and saved eight-document patch satisfy the reviewed scorecard contract. The supervisor still owns integration, combined-tree checks, and the same-integration register transition for NS-003 and this closed Report finding under GOVERNANCE §9.

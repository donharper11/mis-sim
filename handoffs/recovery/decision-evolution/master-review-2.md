# M1 master specification review 2 — PASS

Date: 2026-09-15. Independent reviewer: `/root/m1_master_spec_reviewer`.

**PASS for the master specification at exact final candidate `bee3977494c6ff5840d10d1c38a873155e55aac6`. MSR-001 through MSR-004 are closed at specification level.** No remaining blocking finding was identified in the bounded SPEC_PROTOCOL §11 consistency review. This is not implementation acceptance, an M1 completion claim, a balance verdict, or authorization to dispatch P1 before P0b has been independently audited and integrated.

## Exact basis and independence

The substantive corrected master was read at `30944af894e6d5f84df745c60643399854d0baee` in `/tmp/mis-sim-m1-author`, compared with the original RETURN at `dcb59f54e2ea6cc294a9c0cfffcf470e6e521ead` and `/tmp/mis-sim-m1-master-spec-review.md`. During this review the supervisor explicitly clarified that candidate validation preserves eligibility of every held response, including defer/reject. The final successor changes only that local master wording and its concrete negative proof. Its complete diff was inspected and all five final frozen blocks were independently extracted and executed. The author worktree remained clean at final verification; `git diff --check 30944af bee3977` exited 0.

Final immutable blob hashes:

| File | SHA-256 |
|---|---|
| `handoffs/recovery/decision-evolution/spec.md` | `9ecbdec5ca4feafbc97817bc06139235e5d3cc67e5c94fa3f0b5ee70d4613c68` |
| `handoffs/recovery/decision-evolution/verify.md` | `993c70b9419f9b606d3c1ffd59cc6a2dd096896bb4d565d4aff0ed34a0e2a34a` |

Product bases are distinct. The author branch retains product source based on `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`; its documents describe required new implementation. This review executed against actual post-P0 root source at `c4a095bf0bae68da99ba384064dc040c1f18530d`, then root `092cd655bfd407a6717c8c978e562527cfb17ce7` after the R18 clarification. `git diff c4a095b 092cd65 -- backend frontend Makefile` was empty. P0 was previously independently audited and integrated at `1079b612098d3c3c8f604430e1148a0767dccbcb`, with product bytes equal to the inspected `7dbb4c80cdced9c1012095b7dd62e646883b6c26` candidate. The final P0b **specification** remains the independently accepted `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`; its implementation audit is a separate gate and was not presumed complete here.

The complete prior review readset remains the basis: GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS, design/08, authority/inventory/review/content-basis/content-review, original master/verify, and the named source consumers recorded in review 1. This pass read the corrected master and verification contract, the final successor diff, updated R18, and rechecked actual preconditions, ledger, events, metrics, state, source catalog/event/policy records and the packet/public-shape boundaries. No author WIP or author-generated evidence file was accepted as proof. No repository/product edit, delegation, merge or publication was performed by this reviewer. Temporary extracted probes and this report are outside the repository.

## Executed evidence

Environment: repository root, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=backend`, `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`. Probes use local source and temporary memory/SQLite examples, not any shared database.

I obtained each document with `git show <exact SHA>:<path>`, extracted its five executable fenced blocks, removed only the first block's shell/heredoc wrapper, and invoked each body in its own Python process. Final evidence is `/tmp/mis-sim-m1-master-review2-final-evidence.json`; exact extracted bodies and complete logs are `/tmp/mis-sim-m1-master-review2-final-proof-{1..5}.py` and the corresponding `.py.log` files.

| Frozen block | Observed result | Body SHA-256 |
|---|---|---|
| 1: source costs, dependencies, formulas, transaction example | Seven advertised planted defects DETECTED; source recurring 78200, load 3.7 and fund total 182000 checks PASS | `ee240ee47ed8c0c996c23df22444805ae033a42eb09213379c053edf23abf5b0` |
| 2: actual precondition/ledger consumers | All 11 precondition and 13 event quote-independence checks PASS; seven defects DETECTED, including held fund repair and held defer policy-arm changes | `70b0224290ca30d78f20cf0d4197ff49a7ebecf9386c1e881c0ae7d690bb4272` |
| 3: shape/order/source-join reference | Initialized, draft, locked and completed views PASS; eight unknown/missing/null/order/duplicate/reference/completed-sheet defects DETECTED | `e0d5658d093cfb762efc0ff8ad779e8c4c6c04ffd79478c76448089e4f0e5325` |
| 4: source event/cost forecast | All 16 six-round accepted plans (96 rows) PASS; removing ransomware prevention causes the required R2 failure | `6f8a54a147c96ffab1c249148a76e42e39e5a66726590bf5782ba3288ce4c704` |
| 5: exact typed decision recipe | Four six-round recipes and paired technology/response equality PASS | `b8da797b1aa937c8b3649676b229f8a1a2998b460011e6b1fc54854fe3dea21d` |

Additional independent checks, beyond rerunning the author blocks:

- Reexecuted all 96 source forecast rows with the actual legacy `cheapest_effectful_fix` forced to return `None` for every watch. Every event/cost row equalled the ordinary source run. This checks later episodes/fire-once history as well as initial eligibility; it does not substitute for the P0b producer.
- Inspected actual precondition source and its AST: no `was_actionable`, `cheapest_fix_when_raised` or `repair_assessments` read exists. Signal gates use key/status/severity; the other ten predicates use their existing state/graph/policy inputs. The event arms gate consumes policy selection and has no quote dependency.
- Removed ransomware prevention separately for both paired archetypes under all four strategies. All eight runs failed at R2 on the new recurring commitment's full forecast. The cost-leadership witness is `[-80000,-69800,-59600,-49400,-39200]`; the failure is not rescued by dropping a requested line or weakening affordability.

These additional checks are independently replayable with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-master-review2-independent.py`. Observed on the final extracted body: all three PASS lines, including 8/8 removed-prevention detections; exit 0.

The final held-defer proof uses actual `unlogged_system_change` option/tag data and actual `access_logging` policy semantics. Its original zero-cost defer is eligible; changing the policy to close the original arm makes it ineligible. Treating defer as exempt is detected. The final text applies the same check to reject, using the same eligibility predicate and exclusion reason.

Existing post-P0 compatibility evidence was not redundantly rerun without a source change: the prior independent review executed 109 focused P0/scoring/pin tests and the complete 24 historical payload comparison, digest `e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`, including a detected non-score evidence mutation. Every future packet retains the original checks and its own fresh implementation audit obligations.

These are prebuild reference and consumer proofs. Block 3 is representative serialization validation, not the future P1 parser. Block 4 supplies a temporary scoped path reference and actual source watch/event consumers; it does not execute production adoption, scoring, reducers or persistence. The 100-hire liability failure is a forecast check, not a claim that an unbuilt service already refuses the request atomically. Those limitations are explicit in verify.md and remain required P1–P6 evidence.

## SPEC_PROTOCOL §11

| Required row | Result | Consistency evidence |
|---|---|---|
| 1. Every acceptance criterion maps to the check/code path that emits it | PASS | D1–D10 map to named P1–P6 files and test groups. The corrected integration contract has a reviewed representational seam; the concrete paired plans now satisfy source event/cost feasibility. Refusal/fallback recipes and future service observations are stated separately. |
| 2. Invariants ship falsification checks shown able to fail | PASS for this specification gate | The corrected load-bearing reference claims have executed negative proofs, including integration/credit qualification in the separately accepted P0b packet, original-cost/no-op/horizon/operating constraints, source-order/shape joins, held responses, and the previously failing R2 game class. Every packet also names required actual-implementation mutations, failures and restoration; these remain PENDING until built, not implied by reference PASS. |
| 3. Touched fields agree across specification, contracts, design and models | PASS | Legacy fields stay on the original consumers; P0/P0b optional input semantics are referenced explicitly. New production state, accounting, repair and publication shapes are versioned separately. The master supplies literal CONTRACTS/design/scheduling deltas for supervisor integration and preserves historical 16-table/scorer/M0 interfaces. The two original source contradictions are removed. |
| 4. One compliant route is written | PASS | Master line 92 gives the complete bound-content → typed draft → pure reducers → original consumers → validated atomic checkpoint/result route. P2 does not import future P3; P3 follows audited P2, P4 follows audited P3, and P1 waits for audited P0b. |
| 5. Every schema section enumerates downstream checks and vocabulary homes | PASS | Sections 2–4 and 8 freeze command/runtime/checkpoint/delta/resource/action/repair/view/result shapes and their P1–P5 consumers. Collection-specific identity/order, required empty/null paths and action joins replace the invalid generic ordering. M1 uses machine keys; new human labels have an explicit M3 labels.yaml/UI boundary. |

## Stable finding closures

### MSR-001 — CLOSED: entity access remains scoped and physical

The master no longer prescribes `source.serves` union. It derives exact immutable P0b EntityAccess grants from a live source that originally owns the named entity and an original matching receiver dependency. Source serves/roles/ownership remain unchanged; no duplicate physical facet is created. The separately reviewed P0b contract requires a valid client-to-receiver prefix excluding the source, then the exact integration hop; receiver liveness, capacity and reliability participate. Exact entity/level filtering, one-hop scope, physical-owner de-duplication, node/edge exclusions, SPOF/blast/failover consumers, and production versus legacy access evidence remain governed by that packet.

The original POS→ecommerce product route therefore cannot expose sale or POS roles through a serves rewrite. The marketing/customer source-content gap is retained explicitly as an M4 limitation. P2 `integration` tests must exercise actual implemented P0b interfaces; a family approval or this master PASS is not an implementation substitute.

### MSR-002 — CLOSED: concrete games now have eligible accepted paths

Both paired templates order identity in R1, fund all three specified R1 preventions, then explicitly connect the arriving warehouse and identity in R2. The full source forecast includes the inherited order-DB training decay, strategy affinity, original policy arms, fire-once rules and O2 slot release. It retains actual physical IDs and source prices. The original R2 insolvency is reproduced when required prevention is removed.

Paired recurring costs are `[78200,89800,89800,98100,98100,98100]`. Accepted balanced capital spend is `[146000,110000,0,68000,28500,52000]`; all-tech spend is `[86000,50000,0,50000,0,0]`. The exact typed recipes preserve their shared technology/response choices. Do-nothing and the overspender's declared empty fallback remain total despite unavoidable negative operating cash. Overspender attempts and the late-game arrival refusal have explicit expected errors and unchanged-state obligations; no silent fallback selection is permitted.

### MSR-003 — CLOSED: bounded credit-eligible quotes and nonrecursive validation

The master now owns a finite, explicit P4 candidate catalogue. It excludes temporary responses, initial-only free acquisitions, live/no-op variants, postgame arrivals and unsupported arbitrary combination search. Each compact candidate must actually stop the original metric and emit an original-cleared_by action at the original qualifying commitment time; path disappearance or zero capacity is not a repair. A physical integration repair without original clearing credit is retained as `repaired_but_uncredited`, not aliased to upgrade or awarded denominator credit.

Current minimum and affordable witness are separate: the former is the lowest verified credit-eligible incremental capital price, the latter passes the full held sheet's capital and every remaining recurring period. The initial quote is immutable; later genuine opportunity only updates actionability by OR. Empty assessments mean bounded `unassessed`, never zero price or proof that no repair exists. Full witness history, counterfactual action IDs and separate unpriced exposure have declared homes.

Preparation always starts from the same immutable prior checkpoint plus merged sheet. It derives effects/decay/charges once, carries prior histories/accounting unchanged, and exposes signed provisional funds/forecast separately. Every candidate uses the same preparation boundary; no repair is applied to an already-decayed or already-funded current state. Passive future projection assumes empty choices, no future wiring or speculative grants/losses. The disposable complete-empty-assessment ledger checks every held fund/defer/reject against actual state/status/arms; it cannot publish history, set debt, recurse into quote/assessment, or delete a held choice. Only the official real-assessment ledger and existing fire pass publish.

The R18 initial-physical-ID `node_is_spof` rule matches the literal graph consumer. Production `debt_above` is explicitly unsupported while unpriced exposure exists; legacy semantics remain intact. No invented scorer output is introduced.

### MSR-004 — CLOSED: exact shapes, identity joins and total view boundaries

The master provides explicit EffectCandidateV1, ResourceViewV1, EstateDeltaV1, OrgDeltaV1 and PreparedEffectsV1 records; required numeric ranges and resource accounting ownership are stated. Repair histories/witnesses, PreviewV1 and new result evidence have exact homes. P4 alone settles balances; P3 passes staff/alignment to P2 projection without a reverse import.

ActionEnvelope gives a deterministic ID and source-round/source-command/effect-round provenance wrapper around the unchanged ActionRecord. Price/target/effect must join the immutable original commitment; service read and publication validate the join. The engine sees original records only. Arrays now use their actual identity and order fields; ordinal round arrays and authored watch/event/preference order are preserved instead of being forced into `(round,key)`.

Initialization freezes draft revision 0 and null lock/digest; locking defines exact digest input; reopening retains commands and increments revision. Completed views use current/checkpoint round N and `sheet=null`, while the locked final sheet remains available for exact retries. Required empty lists/maps cannot be replaced by null; detached state and malformed persisted-state refusal remain explicit. The executed shape proof detects unknown/missing/null fields, duplicate/unjoined action IDs, bad source references, order drift and a completed editable-sheet mutant. Human labels for new options are explicitly assigned to M3, with no invented runtime label fields.

## Retained implementation obligations and executable closing checks

Lifecycle, money, prevention, debt and TCO contracts remain coherent: cancellation/kill are sunk and terminal; due cancellation/pause precedes arrival and training; replacement preserves physical identity/old operation until arrival; identical replacement is a free no-op without a currency reset; no post-horizon effect is accepted; last-feasible paused expiry is explicit. Capital always covers all one-offs. Any per-round recurring increase requires every candidate forecast close to be nonnegative; real reductions count only when effective. Fully funded one-offs and non-increasing-liability choices remain legal during unavoidable operating deficits. Event losses may create a deficit after validation without causing invented estate damage or changed scoring equations.

Prevention remains current-round paid evidence, neither fire nor repair; original deck attribution/caps/arms and raw outcomes remain authoritative. Debt is a frozen priced estimate with distinct unpriced exposure, no duplicate accrual/refund; TCO remains a fixed acquisition forecast joined to actual unique cost entries, including replacements, not a new financial score. Source preference coverage retains the 131-leaf disposition grammar, 33 live views and 13 response prices; unsupported interests/vectors remain explicitly assigned.

To replay the executed final reference checks from repository root:

```bash
for i in 1 2 3 4 5; do
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend \
    /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python \
    /tmp/mis-sim-m1-master-review2-final-proof-$i.py || exit 1
done
```

The report does not mark unbuilt tests passed. After implementation, the exact master still requires:

- P1 `test_simulation_content.py -k 'strict or content or checkpoint'`, including full DTO/provenance/null/identity validation.
- P2 `test_simulation_estate.py -k 'integration or arrival or lifecycle or resources'`, using actual audited P0b consumers.
- P4 `test_simulation_consequences.py -k 'money or actions_signals or repair_assessments or responses or debt_tco'`, including double-preparation, held fund/defer/reject, credit-ineligible physical repair and complete-forecast mutants.
- P5 `test_simulation_service.py -k 'editing or rollback or retry_reopen or concurrency or isolation'`, plus the actual disposable PostgreSQL migration/schema checks; reference SQLite is not that evidence.
- P6 `test_simulation_games.py -k 'decision_only or determinism or cross_effects'`, all 96 real persisted reports/checkpoints, actual refusal/no-write proofs, complete historical payload equality and per-packet `make check`/fresh independent audits.

Supervisor-owned living-contract integration must apply the frozen literal deltas and the already surfaced design/08 production reopen/history wording correction when the implementation is integrated. This review does not assert that future runtime rows, browser labels, database schema or M2 scheduling have already shipped. No P1 dispatch precedes audited P0b.

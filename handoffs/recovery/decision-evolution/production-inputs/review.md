# P0b independent specification review

Initial review: 2026-09-14; successor review: 2026-09-15. Reviewer: `/root/m1_master_spec_reviewer` (not author or builder).

**PASS — P0b specification only, exact final successor `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`.** Both bounded findings P0BSR-001/002 are CLOSED, and the supervisor's final credit-eligibility clarification is independently verified at this commit. Actual implementation and independent build audit remain required. This does not accept the master or close MSR-001–004.

Exact accepted specification commit: `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`.
Frozen file: `handoffs/recovery/decision-evolution/production-inputs/spec.md`.
File SHA256: `db30453c0e1314dd6eceea01d2f357586123f214b85849cdfcfe7392b07c208f`.
Both successors change only this specification: `a8ec08440aaca528a9be093c16d4316e12971711` closes the two original findings; final `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992` additionally clarifies verified credit eligibility. Initial candidate `4b94bde86d6013fe111cdae33ed3d7d114f2e8ca`, file SHA256 `542a44e34ec5470780a2e71179fc674e1bd9fc2d4c93025933c69de79523104f`, received RETURN for the two findings preserved below. An uncommitted master `spec.md` edit visible during final inspection is outside this frozen P0b review and receives no acceptance.

Authority: root `1e9eada`, including M1-R16/R17, plus the supervisor's 2026-09-15 explicit credit-eligibility clarification. Those approve the seam families and recorded meaning, not unstated details.
Initial executable comparison base: `/tmp/mis-sim-m1-p0-integration` at `7dbb4c80cdced9c1012095b7dd62e646883b6c26` (post-P0). Successor probes ran at integrated root `1079b612098d3c3c8f604430e1148a0767dccbcb`; independent `git diff --exit-code 7dbb4c8 1079b612 -- backend frontend Makefile` returned zero with no output, confirming identical product bytes. The author's branch still has b7706fb product code plus documentation; it was **not** treated as the post-P0 implementation base.

No implementation, repository edit, subagent, merge, push or shared database action was performed. This report is separate from the master review. MSR-001–004 remain pending the complete coherent master successor.

## Evidence

The governing documents and master basis were retained from the preceding independent review; updated authority R16/R17 and all 337 frozen P0b lines were read. Inspected actual post-P0 state/graph/technology/metrics/events changes and complete ledger/precondition consumers; the whole consumer search covered owner_nodes, serving_path, SPOF, blast, failover, generic repair prices and actionability. Existing state/scoring/ownership contracts were checked against the new sidecars.

Commands ran from the post-P0 tree with `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=backend`, and `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`.

1. Extracted the executable block from `git show 4b94bde86d6013fe111cdae33ed3d7d114f2e8ca:handoffs/recovery/decision-evolution/production-inputs/spec.md`, not the author's separate probe copy. Result: all eight advertised defects DETECTED, then `production input source-backed reference probes PASS`.
2. Ran `python -m pytest -q -p no:cacheprovider backend/tests/test_engine_runtime_inputs.py backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py`: **109 passed in 9.01s**.
3. Independently reused the frozen prototype's route with actual post-P0 mapped nodes: POS `{store_operations:6000}`, receiver `{marketing_sales:1125}`. Observed path `client,web,pos`, bottleneck 1125 for marketing_sales; zero receiver capacity gave zero; missing mapped context raised ValueError. Excluding the corresponding network edge preserved the grant; excluding its integration edge removed the route.
4. Independently ran legacy calibration in disposable SQLite: **24 results; 1656959 bytes; SHA256 `e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`**. Inserting a non-score suppression-evidence row changed the digest and was detected.

These are specification/reference and compatibility evidence. They do not claim unbuilt EntityAccess/RepairAssessment constructors or the future production generator already work. The P0b builder and fresh auditor must execute the new inputs and all planted code mutations.

## SPEC_PROTOCOL §11

| Row | Result | Assessment |
|---|---|---|
| Acceptance maps to an emitting path/check | PASS | The six test groups map to the named owner/path/failure/ledger/constructor/legacy consumers. The successor provides the exact evidence home and executable expected fragment, along with explicit exclusion cases. |
| Falsification shown on planted defects | PASS for prebuild reference evidence | Eight original counterexamples and all successor boundary/evidence counterexamples rerun successfully; independent post-P0 unit/context/exact-edge checks and non-score digest mutation also passed. Actual new-constructor and consumer mutations remain mandatory build evidence. |
| Field consistency across spec/contracts/design/models | PASS | Optional fields preserve post-P0 field order/defaults. Successor resolves exclusion null/malformed/native behavior and fixes the per-entity provenance path. Its literal CONTRACTS addition names that path. No pure score or price is invented by this packet. |
| A coherent compliant route is written | PASS | Immutable one-hop grants preserve physical ownership/roles/serves; imported primary routes require receiver plus integration; all contextual failures share this route; verified assessment inputs replace only the production quote branch. No contradictory scoring equation is needed. |
| Downstream checks and vocabulary homes enumerated | PASS | Named graph/technology/metric/event/ledger consumers and future P2/P4 producers are covered. Existing entity/physical precondition meanings remain explicit. `access_via` home/sort/filter/empty/omission behavior is now exact; no new student label vocabulary is required by this pure packet. |

## Findings — original defects and successor closure

The original descriptions below refer to `4b94bde`; their line numbers preserve the initial evidence. Both are closed by the successor clauses and independently executed checks recorded after them.

### P0BSR-001 — CLOSED: new path exclusion input boundary

Owner: P0b author. Dispatch-blocking specification omission; no change to the approved route family requested.

Frozen lines 92–107 introduce `exclude_nodes: frozenset[str]` and `exclude_edges: frozenset[tuple[str,str,str]]`, but do not define accepted containers, explicit None, invalid key/tuple shape, invalid kind, reversed endpoints, or nonempty exclusions when `state.entity_access is None`. The file simultaneously promises an unchanged None-input path (lines 61,84,127) and specifies exclusion processing only under the present-input branch (line 98).

Actual post-P0 `graph.serving_path` at lines 85–98 has no exclusion arguments, so source cannot supply the missing semantics. A builder could either ignore explicit exclusions on the legacy branch, apply them, or reject that combination; all preserve the old default calls but expose different new behavior. Likewise, a None exclusion could become an incidental TypeError, an empty set or a deliberate ValueError. Annotation alone does not choose one.

Closing check: freeze a total boundary for both optional-state branches, including valid unknown node/edge exclusions and edge-key canonicalization versus refusal. Add an executable reference table and later `test_engine_production_inputs.py -k access_failure` cases for absent/default, empty, nonempty, None, wrong container, malformed edge length/key/kind and reversed endpoints. Show a deliberately ignored exclusion and a coerced/null exclusion fail the chosen expected behavior. In the builder/auditor run, use:

```bash
PYTHONPATH=backend python -m pytest -q backend/tests/test_engine_production_inputs.py -k 'access_path or access_failure or immutable'
```

The existing positive prototype cannot close this omission because it accepts generic Python sets and never exercises the unspecified inputs.

### P0BSR-002 — CLOSED: `access_via` evidence home and ordering

Owner: P0b author. Dispatch-blocking cross-module field omission; no added scored output requested.

Frozen lines 137–140 say “Technology entity evidence adds access_via” with sorted grant-shaped rows. They do not name its precise JSON path or the sort tuple, nor explicitly state the production native-only/no-valid-grant case and whether invalid/dangling grants appear in this evidence. These affect the persisted full-result contract and the meaning of the causal trace.

Existing exact homes are observable in post-P0 `technology.py:53–81,133`: each entity has `{required_level,owned_by}` under `TechResult.evidence['data_adequacy']['entities'][entity_key]`; `score.py` nests that under each capability's `evidence['tech']`. No existing `access_via` key resolves this new field. A top-level data-adequacy list, per-entity list, or sibling evidence field would all match the prose and yield incompatible consumers.

Closing check: state the exact JSON home, complete row keys, lexicographic sort tuple, valid/invalid grant filter, duplicate behavior and explicit empty-list versus omitted-key rule in production. Preserve complete absence on legacy None inputs. Add a source-backed expected evidence fragment and planted wrong-home/unfiltered-grant/order/legacy-empty-key examples. Later executable candidate gates are:

```bash
PYTHONPATH=backend python -m pytest -q backend/tests/test_engine_production_inputs.py -k 'access_scope or legacy'
```

Tests must compare the independently specified complete evidence fragment, not search for the field somewhere in the result. The literal CONTRACTS/design integration text should name or directly reference this exact field contract.

## Successor closing evidence

Read the complete successor diff and checked its reconciliation with the retained contract. Exclusions now accept only frozensets, reject None and malformed entries with ValueError, require canonical edge endpoint order and existing edge-kind vocabulary, treat well-formed unknown identities as no-ops, and apply explicit native-only exclusions when entity_access is None. The exact legacy default call remains unchanged.

The new evidence home is `TechResult.evidence["data_adequacy"]["entities"][entity_key]["access_via"]`. Rows include exactly the five named grant fields, are filtered by valid live/level predicates, deduplicated by the complete tuple and sorted by `(connection,source,receiver,capability,entity)`. Production no-valid-grant cases produce `[]`, including native-owner cases. Legacy None inputs omit the key. Distinct valid connection evidence may still name one deduplicated physical owner.

The combined single reference block was extracted from the exact Git blob and executed at integrated post-P0 root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python - <<'PY'
import subprocess,sys
text=subprocess.check_output(['git','-C','/tmp/mis-sim-m1-author','show',
 '2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992:handoffs/recovery/decision-evolution/production-inputs/spec.md'],text=True)
blocks=text.split("PYTHONPATH=backend python - <<'PY'\n")
assert len(blocks)==2
probe=blocks[1].split('\nPY\n',1)[0]
subprocess.run([sys.executable,'-c',probe],check=True)
PY
```

Observed all eight original defect detections, eight malformed exclusion refusals, explicit null rejection, and six additional mutant detections: ignored native exclusion, coerced null, wrong evidence home, dangling grant evidence, legacy empty evidence key, and reversed evidence order. The final successor also detected falsely relabeling an integration for signal credit using actual `matching_clear_actions`; all three reference PASS messages appeared; exit 0.

Independent extension exercised 12 additional malformed inputs (list/dict/string/generator containers on both arguments, whitespace/integer node keys, whitespace/integer edge endpoints). All raised ValueError. Well-formed unknown edges left the imported route unchanged; excluding the wrong edge kind left it intact; excluding its integration edge removed it. An actual native-owner fixture matched the existing graph path and lost that path when its owner was excluded. The existing owner lookup rejected an insufficient source level. Native evidence omitted `access_via` on the legacy branch and produced `access_via:[]` with the same native owner on the production branch. Final output: `independent extra12malformed, native/grant exactkind, level and native-empty evidence checks PASS`.

The prior 109 focused tests and exact 24-result digest evidence remain applicable because the independently compared executable bytes did not change. They were not unnecessarily rerun for a documentation-only successor. New P0b implementation tests and their real code mutations remain required; reference prototypes are not claimed as shipped engine code.

The final meaning is the cheapest **verified credit-eligible repair in the bounded catalogue**, not the cheapest possible physical repair. An eligible candidate must repair the metric and emit a real action from the watch's original `cleared_by` vocabulary at a qualifying original commitment time. A real repair lacking credit eligibility remains `repaired_but_uncredited` in the master's full evidence and is excluded from the compact assessment candidates. The final diff consistently narrows minimum/initial-quote wording, changes no fields, and does not amend watch vocabularies or timestamps. Independently invoked actual `matching_clear_actions`: `cust_data_01` plus integration `add_service_tier` returned `(None,())`; a current qualifying `add_node` returned `(3,('add_node',))`; the same action type committed before the episode returned `(None,())`. Thus the clarification agrees with the preserved consumer rather than inventing denominator credit.

## Semantics checked and retained

- Grants name connection/source/receiver/capability/entity; level stays original source ownership. Both nodes, capability, owned level and integration edge must satisfy the query. A dangling grant becomes ineffective; P2 separately rejects unauthorized content/connection claims. Native ownership remains legal; imported ownership cannot acquire roles, currency membership, extra physical placements or a second system of record.
- Imported primary paths use client→receiver with source excluded, then receiver→source integration. Minimum path length then node-key tuple gives deterministic selection. The real receiver participates in capability-specific capacity and reliability. Secondary-entity adequacy explicitly retains the existing live-ownership rather than client-path rule; this limitation is stated rather than silently changed.
- Production serving SPOFs remove interior nodes and recompute the same route; blast compares existing versus removed-node routes; failover tests load-bearing failover-edge exclusions after the failed node is removed. Source/receiver failures and alternative native/imported paths therefore share one interpretation. Physical `node_is_spof`, `entity_unowned` and placement multiplicity remain unchanged and outside the edit allowlist.
- Repair input records separate the cheapest verified credit-eligible cost from an affordable witness within that bounded catalogue. Full watch coverage, checked/current round equality, in-game effect range, strict values, unique signal/candidate IDs and copied tuples are specified. No supplied assessment falls back to the generic legacy quote. An unassessed episode stores None; later verified opportunities can set actionability without repricing its initial quote. Terminal history, commitment timestamps, action matching and response-window exclusions remain unchanged.
- P0b cannot verify a command witness from a hash alone and does not claim to. The master/P4 contract must freeze the bounded candidate generator, command canonicalization, actual affordability schedule and complete evidence/history joins. It must not convert `unassessed` into “no repair exists,” fabricate retroactive debt or use prevention as a repair. Those are master responsibilities still under review, not implied approvals here.
- The allowed files include all identified new behavioral consumers and exclude preconditions, pure scorer equations, weights, old fixtures/P0 tests, persistence and candidate generation. No unrelated implementation expansion is needed.

P0b-specific independent specification review passes on `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`. The supervisor may prepare its bounded builder dispatch from the audited post-P0 integration base. P0b still needs implementation and independent build audit, and the master must still receive complete coherent successor review before P1–P6 dispatch.

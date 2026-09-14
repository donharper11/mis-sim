# M1 P0 independent specification review — PASS

Date: 2026-09-14. Reviewer: `/root/m1_p0_spec_reviewer` (independent of author and builder).
Frozen specification: `818c54acae3a05b6aa99d6e5ebeb451269c13c8c`.
File: `handoffs/recovery/decision-evolution/engine-inputs/spec.md`.
Spec-file SHA-256: `06eaea0066cc8ae08e1826aab1c169c063fad5700cfbabfd4d591fcef03bbbbc`.
Product source base: `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`.
Authority: root M1-R5 in `handoffs/recovery/decision-evolution/authority.md` (supervisor-approved bounded input seam).

**PASS for P0 spec dispatch only.** This does not accept an implementation, complete M1, or authorize estate, organisation, accounting, service, migration, or UI work. The untracked master M1 draft was excluded. No repository files were edited by this reviewer. Source and successor differ only by the P0 specification.

## SPEC_PROTOCOL §11 checklist

| Row | Verdict | Evidence |
|---|---|---|
| 1. Acceptance maps to emitting check or code path | PASS | Spec 63–83, 123–150 and 173–258 map capacity to graph/technology/metrics/event binding, RTO to outage evidence, physical count to placement precondition, immutability to copied mapping, traversal to subprocess BFS, and legacy compatibility to canonical complete results. The author executable was independently run; capacities are computed as `(2000, 0.333333)` and `(100, 1)`, RTO duration as `36.0`, and all seven negative probes are detected. New-field tests remain mandatory builder deliverables, rather than falsely claimed existing tests. |
| 2. Invariants have demonstrated falsification | PASS | Final executable uses real functions and constructed inputs. Wrong units, min→sum, changed RTO source, duplicated physical node, retained map alias, unordered BFS and full-result evidence mutation each fail the relevant assertion. Independent injection of min→sum into the imported graph module additionally makes the final executable fail at its positive capacity assertion. Former self-comparison defect is closed below. |
| 3. Spec / living contracts / design / models agree | PASS | ArchNode extension is additive and trailing; CatalogItem RTO and Capability demand units retain existing shapes. Existing scalar and catalog-key/default behavior is preserved. Exact versioned living text and a new final design subsection are supplied in spec 266–289, owned by supervisor integration. Existing scorecard-v1 fields and scoring equations are unchanged. |
| 4. A compliant implementation route is written | PASS | Spec 90–94 explicitly names defaulted immutable fields, shared per-node selection, capability propagation through current consumers, optional RTO precedence, and sorted traversal. No physical-node facets or second scorer are needed. |
| 5. New schema enumerates downstream checks/vocabulary homes | PASS | P0 adds only in-memory ArchNode fields. Current graph/technology/metrics/events consumers and legacy constructors are named and inspected by PF1/PF4. Mapping/key/numeric validation is at construction; pack-key vocabulary and duplicate JSON/YAML detection are explicitly assigned to the future projection/parser boundary. Existing placement vocabulary stays in CONTRACTS/preconditions. No casepack field, label, error-code vocabulary, DB or frontend contract is introduced. |

## Source and contract consistency

Mandatory root `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md` and `CONTRACTS.md` were read in full. Actual changed consumers, relevant tests, seed/snapshot producers, calibration harness, Makefile and design/model surfaces were inspected rather than inferred from the author's prose.

The relevant existing living contract says: “a property of an existing serving path returns `0.0` (no raise) when the capability has no path or non-positive capacity” (`CONTRACTS.md`, METRICS entry). P0 keeps that metric behavior; zero capacity still gives technology capacity zero. The outage contract keeps `round(base_rto_hours × failover_factor × staffing_modifier, 1)`; only the explicit node input precedes the old lookup.

Verified source seams:

- `state.py:28–49`: frozen ArchNode, scalar throughput and trailing placement; `round/snapshot.py:134–144` constructs legacy scalar nodes only.
- `graph.py:33–58`: source order and set-neighbor BFS; `graph.py:113–124`: actual min of non-None scalar throughput.
- `technology.py:109–111, 126–132`: helper call, demand division/clamp and six-place factor output.
- `metrics.py:45–58`: known rule capability, demand/path guards, four-place utilisation, zero/nonpositive behavior.
- `events.py:145–175`: helper minimum, first path-node tie and event primary-capability binding; `events.py:210–239`: catalog-key RTO fallback and unchanged duration/evidence equation.
- `preconditions.py:106–110`: one count per physical node.
- `casepack/models.py:167–179, 235–249`: demand-unit content and existing CatalogItem RTO. Catalog assets `order_mgmt_v42` and `erp_suite` really span the differently dimensioned capabilities described in the spec.

Final error/null contract is reviewable: omitted/None capacity map preserves scalar behavior; empty/present missing entry means no ceiling; zero is a ceiling; None values are unlimited; scalar plus present map rejects. Only Mapping containers are accepted; malformed containers, nonstring/empty/whitespace keys, booleans/strings/negative/nonfinite values and overflow reject with ValueError. Explicit RTO is positive finite numeric or None. Mapping input is copied and frozen. Omitted context on a mapped path rejects; an explicit nonmatching capability follows the missing-entry rule. Unknown physical path nodes keep the existing skip behavior. Python mapping duplicates are already collapsed by that input type; duplicate serialized keys remain a future parser responsibility, not a new P0 parser.

## Independent execution evidence

Environment: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`, working directory `/tmp/mis-sim-m1-author`, disposable SQLite only.

1. `PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py` → **14 passed**.
2. `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check` → **311 pytest tests passed; all guards green; all 44 fixtures passed**. Log: `/tmp/mis-sim-m1-p0-review-make-check.log`.
3. Independent `/tmp/mis-sim-m1-p0-review-probe.py` ran original and in-memory sorted BFS separately under process seeds **0, 1, 2, 3, 42, 99**. Original diamond: `a,a,b,b,a,a`; sorted: `a,a,a,a,a,a`. Bottleneck identity follows those same selected nodes.
4. All **12 complete result captures**, each covering 24 rounds, were compared by actual bytes: all equal, **1,656,959 bytes**, SHA-256 **`e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`**. Score-only digest separately matched **`0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`**. Captures: `/tmp/mis-sim-m1-p0-review-{original,sorted}-seed{0,1,2,3,42,99}.json`.
5. Actual technology/metric scalar probe at demand 6000 and bottleneck 2000 returned technology factor **0.333333**, evidence `{bottleneck: 2000, demand: 6000}`, utilisation **3.0**. Existing authored RTO lookup was independently checked for `next_gen_firewall` (base4/duration12) and `order_db_cluster` (base12/duration36) with staffing modifier1 and no failover.
6. Frozen author's executable and independent extra mutation:

```bash
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-p0-final-proofs.py 818c54acae3a05b6aa99d6e5ebeb451269c13c8c
```

Result, from `/tmp/mis-sim-m1-p0-final-proofs.log`:

```text
original exit 0
wrong unit planted defect DETECTED
min changed to sum planted defect DETECTED
wrong RTO planted defect DETECTED
duplicated physical node planted defect DETECTED
retained map alias planted defect DETECTED
unordered BFS planted defect DETECTED
changed legacy evidence planted defect DETECTED
all computed prebuild probes PASS
planted_min_to_sum exit 1
AssertionError: ([(10000, 1), (300, 1)], [(2000, 0.333333), (100, 1)])
PASS: exact new final design subsection declaration and extant target
PASS: revised oracle accepts base and rejects actual min-to-sum code mutation
```

The author block itself is retained at `/tmp/mis-sim-m1-p0-final-authored-oracle.py`; it computes from real source and fixtures. The extra mutation changes the imported graph implementation only in a subprocess. Repository files remain unchanged.

## Findings and closure

**No open findings on 818c54acae3a05b6aa99d6e5ebeb451269c13c8c.** Supervisor should retain these stable closure rows in the integration record.

- **M1-P0-SR-001 — CLOSED (owner: m1_contract_author).** Frozen predecessor `f4394459201de4645a59338126c44e40acccc0f1`, spec201–216, compared canned expected tuples with themselves and unrelated bad tuples/hashes. It continued printing every PASS when graph min was changed to sum; actual helper result changed from1000 to9000. This failed §11.2. Evidence: `/tmp/mis-sim-m1-p0-oracle-proof.py` and `.log`. Final818c54a replaces that oracle with actual computations and independent planted defects. The closing command is the final-proofs command above: original passes, injected min→sum fails, wrapper exits0. This was rerun on the exact final spec.
- **M1-P0-SR-002 — CLOSED (owner: m1_contract_author; application owner: supervisor).** Predecessor f439445 spec247–248 targeted a graph/path or engine-acceptance section absent from `design/07-decision-consequence-map.md`; an earlier revision even named a nonexistent file. `rg -n '^#{1,6} .*([Gg]raph|[Ee]ngine acceptance)' design/07-decision-consequence-map.md` returned no hits/exit1. Final818c54a spec281–289 explicitly appends a new final named subsection to the existing document. The final-proofs command checks the exact declaration and target file and now passes.

## Dispatch and integration obligations

Dispatch only the five engine files, new focused pytest file and P0 DoD listed in the spec. Builder must run/report PF0–5 on its exact assigned clean base, exercise the NEW map/RTO/context interfaces and every specified malformed/null/tie case, retain failing/restored candidate mutations, compare full legacy payloads and pins, and run make check. The prebuild scalar probes establish specification consistency; they are not implemented-node validation evidence.

A fresh build auditor is still mandatory. The supervisor must apply the exact living CONTRACTS/design text with the living-document version/changelog update and reconcile the two closed review findings at integration. No test/seed/pin rewrites or scope expansion are authorized by this PASS.

Quality ladder: contract and headless source/runtime verification apply. UI, browser/auth/UX/screenshots, migrations and new DB isolation checks are N/A for this pure in-memory packet; disposable SQLite is used only to reproduce the existing full-game baseline.

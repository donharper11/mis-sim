# M1 P0b builder evidence — audit pending

Date: 2026-09-15. Builder: `m1_production_builder`.
Assigned clean base: `b59fa540a5c3789ae60739f585148b37ba7f8ffc`.
Branch: `build/m1-production-inputs`.
Frozen implementation authority: [spec.md](spec.md), independently passed at
`2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`; spec SHA256
`db30453c0e1314dd6eceea01d2f357586123f214b85849cdfcfe7392b07c208f`.
The candidate commit identifier is reported to the supervisor after this file is committed.
This is builder verification, not independent audit, integration, or M1 completion.

## Preflight ordering deviation and corrective replay

**P0B-BLD-001 — disclosed procedural deviation.** The builder completed the root protocols,
P0/P0b contracts, frozen historical master/verify, complete engine sources, original
1.4/1.5/1.6 contracts, and every PF1 caller before coding, and initially ran PF0–PF5
successfully. During DoD cross-check the builder found additional background entries in
the historical master's declared readset that had not yet been read: scheduling,
Postgres/migration background, remaining seeds/content, inventory/review and the validator
report boundary. The earlier “complete master readset” report was too broad. These reads
finished **after the first implementation and verification**, and that ordering cannot
be repaired retroactively or described as compliant original preflight.

The builder reported this to the supervisor immediately. The supervisor accepted a
bounded corrective replay while requiring this disclosure and independent audit review.
After finishing the missing reads, the builder preserved all six candidate code/test
files outside the repository with SHA256 hashes, restored the exact clean assigned base,
reran PF0–PF5 there, and reapplied the **same candidate bytes** only after every replay
check passed. No implementation semantics changed because of the background reads.
The ordering deviation remains part of the audit handoff.

Evidence root for all commands/logs below: `/tmp/mis-sim-p0b-builder-evidence/`.
Replay script: `replay-preflight.py`; preservation manifest:
`candidate-before-replay-sha256.json`; ordered results: `preflight-replay.log`;
exact restoration/reapplication: `replay-pf0.log`, `replay-reapply.log`.

## Read basis and consumers

Read complete `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`, `CONTRACTS.md`;
this folder's spec/review and parent authority/master-review-1; P0 engine-inputs/spec;
design 04/07/08; original 1.4 spec/closeout-spec, 1.5 spec/contract-spec, 1.6 spec, and
2.3 scheduling spec. Historical master spec/verify/inventory/review were read from exact
Git object `dcb59f54e2ea6cc294a9c0cfffcf470e6e521ead`, as historical background only.
Master source-serving expansion and generic repair proposals are superseded by this
frozen P0b packet. No successor master draft was used as implementation authority.

Complete executable reads: engine state/graph/catalog/technology/organisation/management/
score/rollup/mathx/metrics/preconditions/ledger/events; round runner/models/snapshot/actions/
db; casepack models/loader; seed demo and calibration harness; Makefile; Postgres runtime
verification script, Alembic env/baseline, models/base; validator's complete `Report`,
`exit_code_for`, `validate_pack_dir` boundary. Other validator internals were not changed.
Read complete Riverside platform/catalog/capabilities/strategies/policies/watch_rules/
obligation_rules/events and all five preference files; complete riverside_r3/riverside_full,
archetype_base and all four archetype seeds. P0 focused, original scoring and round-pin
tests were read complete; each matching signal-engine/runner test caller was inspected.

PF1 exact search was executed before coding and during replay:

```bash
rg -n 'owner_nodes|serving_path|spofs_on_path|blast_radius|failover_exists|cheapest_effectful_fix|was_actionable' backend/app backend/tests
```

| Consumer | Checked context and disposition |
|---|---|
| graph owner/path/SPOF/blast | New present-input route; exact absent-input legacy path retained |
| technology ownership/path/evidence | Original role/currency membership; valid grant provenance; production service SPOFs |
| metrics capacity/availability/data gap | Already delegates capability/entity/level to shared graph helpers; no direct consumer change needed |
| events failed node/failover/outage | Existing path and per-capability bottleneck select failure; production failover reuses exclusions |
| ledger quote/actionability/project | Optional assessment validation and consumption; original action matching and projection retained |
| round runner/snapshot/models, seed/demo | Existing inputs remain absent; frozen quote persistence/debt/projection callers unchanged |
| original/P0 and new tests | Every matching caller inspected; no unseen production caller introduced |

Final inventory: `final-caller-inventory.txt`; replay baseline inventory: `replay-pf1.log`.

Relevant frozen constraints were applied literally:

- CONTRACTS: “Episode identity is `(key, episode_id)`”; history is “append-only and immutable.”
- CONTRACTS clearing match: `first_shown_round ≤ locked_round ≤ round`; no action vocabulary or timestamp rewrite.
- P0b: “The receiver is not promoted to owner.” Original physical ownership and `serves` remain authoritative.
- P0b: “The initial quote is frozen thereafter, even if later assessed or cheaper.”
- P0b: “No assessment may silently fall back to legacy price calculation.”
- P0b P2/P4 producer authority remains separate: compact validation does not prove command
  effect/price/authorization, and candidate search is not implemented here.

## Preflight results

Commands ran from the assigned worktree with the existing supervisor venv on PATH,
`PYTHONPATH=backend`, `PYTHONDONTWRITEBYTECODE=1`, and
`M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-supervisor-baseline.json`.

| Row | Original execution | Corrective exact-base replay |
|---|---|---|
| PF0 | Exact clean assigned SHA confirmed | Exact same SHA and empty `git status --porcelain`; `replay-pf0.log` |
| PF1 | Search executed; all engine, legacy caller and test hits inspected | Same baseline caller inventory; `replay-pf1.log` |
| PF2 | P0 focused + original scoring/pins: 109 passed | 109 passed; `replay-pf2.log` |
| PF3 | Full24 canonical JSON identical to supervisor capture | 24 results, 1,656,959 bytes, same SHA and direct bytes; `replay-pf3.log`, `replay-full24.json` |
| PF4 | Entire frozen standalone author probe passed and detected every planted reference defect | Entire probe again passed; `replay-pf4.log` |
| PF5 | 406 tests, all guards, all 44 fixtures passed | 406 tests, all guards, all 44 fixtures passed; `replay-pf5.log` |

Full24 SHA256 throughout:
`e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`.
PF4 is supplemental author-counterexample evidence; the candidate interfaces and source
mutations below are the implementation evidence.

## Candidate behavior and actual verification

Implemented frozen `EntityAccess`, `RepairCandidate`, `RepairAssessment` and appended
optional TeamState inputs with exact record/container/key/numeric validation and tuple
copying. Present access routes preserve physical ownership while enforcing a live receiver
and integration edge. Native routes compete by length then lexicographic path order;
node and exact-kind edge exclusions are validated in both branches. Ownership/provenance,
service SPOFs, blast, and failover share the same live grant/path semantics. No source
roles, currency membership, or unrelated entity is imported.

Assessed ledger inputs require all pack watch keys, the current checked round, and bounded
effect dates. A new episode records the cheapest verified credit-eligible repair and the
presence of an affordable witness; later opportunity ORs actionability without changing
the initial quote. Empty assessments do not call generic pricing or capital-only logic.
The engine trusts P4's compact attestations; it generates no candidate commands.

| Acceptance | Observed evidence |
|---|---|
| `access_scope` | Named entity only; original roles/currency/placement; exact levels; no transitivity; source dedup; every live predicate and sorted detached evidence; independent-owner penalty |
| `access_path` | Receiver cannot be bypassed by client→source shortcut; receiver 1125 campaigns constrains path while source 6000 store_day does not; each physical reliability once; retirement/disconnection/kind removal; stable native/imported alternatives |
| `access_failure` | Receiver service SPOF despite physical triangle; source/receiver removal; native/imported alternatives; load-bearing failover; parallel edge kinds; total exclusion validation; unknown identity no-op; original physical preconditions |
| `assessment` | Legacy None; all watch keys including nonraising rules; checked/effect bounds; zero vs None; cheaper unaffordable and dearer affordable candidates; immutable initial quote; original real action/time match, still-raises, terminal and projection semantics |
| `immutable` | Both tuple layers copied; frozen fields; malformed containers/classes/keys/counts/dates/bools/nonfinite/overflow rejected; duplicates and self-grants rejected |
| `legacy` | No new access evidence for None; full24 canonical bytes and direct external baseline comparison |
| Restored focused + P0 + pins | 307 passed in `restored-focused-p0-pins.log`; replay result recorded below |
| Full check before corrective replay | 604 passed, every guard, all 44 fixtures; `final-make-check.log` |
| Final check after byte-identical replay | 604 passed, every guard, all 44 fixtures; `final-replay-make-check.log` (includes all 307 focused/P0/pin tests) |

Focused aggregate command:

```bash
python -m pytest -q -p no:cacheprovider backend/tests/test_engine_production_inputs.py backend/tests/test_engine_runtime_inputs.py backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py
make check
```

The P0 test file is unchanged and continues its six-hash-seed full24 comparisons. The new
suite adds 198 tests and its own full24 capture. All captures use fresh disposable SQLite
databases and the real seeded calibration/round engine, not expected output inserted as data.

## Actual disposable code-defect mutations

`run-mutations.py` copied the backend to a fresh temporary directory for each probe,
changed executable source (never assertions), ran the named group, recorded pytest exit 1
and failures, restored the original source, and reran to pass. Original candidate source
hashes were verified unchanged. Evidence: `mutation-results.json`, `mutations.log`, and
the corresponding `mutation-<name>.log` / `restored-<name>.log` files. Group selections can
overlap where test names include more than one family word.

| Mutation name | Executable defect | Detected failures | Restored selection |
|---|---|---:|---:|
| scope_receiver_owner | Add receiver to physical owner IDs | 13 | 14 passed |
| path_receiver_bypass | Native target set incorrectly includes granted source | 5 | 10 passed |
| path_accept_network_grant | Accept non-integration edge for a grant | 1 | 10 passed |
| failure_raw_bfs | Bypass production failover route and use legacy physical BFS | 1 | 50 passed |
| failure_skip_exclusion_validation | Skip total exclusion validation | 46 | 50 passed |
| assessment_generic_fallback | Empty candidates fall back to generic price | 4 | 33 passed |
| assessment_requote_initial | Reprice an open episode from current candidates | 3 | 33 passed |
| assessment_skip_key_coverage | Omit complete watch-key validation | 3 | 33 passed |
| immutable_retain_lists | Retain caller containers | 2 | 101 passed |
| immutable_accept_bool_cost | Omit capital-cost validation | 11 | 101 passed |
| legacy_add_access_evidence | Add access_via to absent-input reports | 2 | 2 passed |

## Definition of done and scope

| Item | Builder status / limit |
|---|---|
| Frozen interface/contract verification | Passed, with disclosed P0B-BLD-001 read-order deviation and corrective replay |
| Implementation, pure runtime tests, full check | Passed as above |
| Casepack fixture matrix | All 44 behave as named; unchanged historical I8 unfixturable note remains |
| Historical full24/P0/R3 pins | Byte-identical; old tests/seeds/pins untouched |
| DB/schema migration/auth/browser/UX/screenshots | N/A: pure optional engine-input packet, no persistence/API/UI/auth changes; disposable real seed/round calculations are exercised |
| Engine I/O, dependencies, scoring formulas/weights | No additions or changes |
| Allowed files | Five engine files plus the new test and this DoD; metrics read but unchanged because its callers already delegate correctly |
| Preconditions | Unchanged physical `entity_unowned`, `placement_count`, global `node_is_spof` |
| Shared documents/register reconciliation | Supervisor owns the literal CONTRACTS/design integration and register updates after independent audit; builder was forbidden to edit them |
| Independent spec review | Frozen P0b review passed before builder dispatch |
| Independent candidate audit | **PENDING**; fresh auditor must verify candidate contracts and repeat actual mutations |
| Main merge/push/deploy/P1–P6 work | Not performed; outside this packet |

No unresolved implementation ambiguity or new semantic source conflict was found in the
completed readset. Historical contradictions already identified by the frozen master
review remain superseded/background; no legacy source contract was reinterpreted.

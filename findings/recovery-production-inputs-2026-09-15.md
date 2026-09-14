# M1 P0b independent build audit — PASS / ACCEPT

Date: 2026-09-15. Auditor: `/root/m1_production_auditor`, fresh and independent of the
author, builder, and supervisor integration work. No subagents were used.

**PASS / ACCEPT the bounded combined candidate
`1729a8966974cf484a25f226290790f6024486c1`.**

Audited tree: `/tmp/mis-sim-m1-p0b-integration`, branch `build/m1-p0b-integration`.
Comparison base: `c4a095bf0bae68da99ba384064dc040c1f18530d`.
Builder implementation: `eaa33e5a69306fb03a61dc6778d8120b0fe18556`, based on
`b59fa540a5c3789ae60739f585148b37ba7f8ffc`. All six changed code/test files are
byte-identical to that builder commit and its before-replay preservation manifest.
Frozen P0b specification: `2bab3519efcb7c41fd7f9ae304ba2ffaf46c9992`; file SHA256
`db30453c0e1314dd6eceea01d2f357586123f214b85849cdfcfe7392b07c208f`.

This acceptance covers the optional immutable engine inputs, their graph/technology/event/
ledger consumers, focused tests, DoD and applied living-document changes. It does not
implement or accept a production candidate generator, command/affordability witness
producer, debt ledger, SimulationService, master successor contract, or M1 completion.

## Findings and procedural disposition

**No new implementation or contract findings.** P0BSR-001/002's implementation-side
exclusion and provenance obligations pass the independent checks below.

**P0B-BLD-001 — retained OWNED procedural residue, Report severity.** Owner:
`m1_production_builder` for readset/preflight discipline; supervisor `/root` for recording
the disposition in the shared register before integration/merge.

The shipped DoD at `handoffs/recovery/decision-evolution/production-inputs/dod.md:14`
explicitly records that additional historical-master background reads happened after the
first implementation and verification. The earlier claim to have completed that entire
readset was too broad. This violates the original preflight ordering; later replay does
not turn the original execution into a compliant one. It is not marked CLOSED here.

The disclosed omission concerns scheduling, PostgreSQL/migration, remaining seed/content,
inventory/review and validator-report background. The DoD states that root protocols,
the P0/P0b contracts, complete affected engine sources and every relevant caller had been
read before coding. The supervisor had already authorized bounded corrective replay.
I inspected its PF0/reapply/ordered-result logs and independently compared the preserved
six-file manifest to both the committed candidate and builder Git object. Those bytes are
identical. This is corroboration of the corrective verification and candid disclosure,
not independent reconstruction of the builder's original reading chronology.

The current implementation is acceptable on the independent evidence below. Carry the
procedural residue with its named owners; do not silently erase it or claim class-wide
closure from this packet. The supervisor must fold this finding/disposition and the audit
link into the shared register/status record, which this auditor was forbidden to edit.

Executable integration closing checks for this owned record:

```bash
python - <<'PY'
from pathlib import Path
assert 'P0B-BLD-001' in Path('handoffs/recovery/decision-evolution/production-inputs/dod.md').read_text()
rows = [line for line in Path('findings/OPEN-REGISTER.md').read_text().splitlines() if 'P0B-BLD-001' in line]
assert rows, 'P0B-BLD-001 register disposition missing'
assert any('supervisor' in line.lower() or 'm1_production_builder' in line for line in rows), 'Named owner missing'
print('PASS P0B-BLD-001 disclosure and owned register disposition')
PY
PYTHONDONTWRITEBYTECODE=1 /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-production-auditor-probes.py
```

The first check requires the DoD disclosure and an explicit owned supervisor register row;
the second fails if the frozen candidate/spec, preservation manifest, literal documents,
physical/assessment interfaces or baseline bytes disagree. This checks honest integration
of the residue, not retroactive read order. Class-wide closure requires evidence that the
complete named readset and PF register precede coding in later Heavy dispatches; until
then this process class remains owned.

## Independent source and scope review

Read GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, full CONTRACTS, authority, frozen P0b
spec/review, P0 spec and independent P0 findings. Read the complete baseline affected
engine sources, their candidate diffs, full new tests and DoD; inspected catalog,
preconditions, snapshot/runner consumers and every ownership/path/failure/price/actionability
search hit. No applicable AGENTS.md exists. Preparation was read-only; final execution
started only after the supervisor supplied the exact committed combined candidate.

Relevant contracts are explicit: the receiver is not promoted to owner; original clearing
vocabulary and commitment timestamps are preserved; the episode's initial quote is frozen;
supplied assessments never silently fall back to generic pricing.

- `state.py:99–167` validates exact record/container classes, nonblank keys, distinct
  grant endpoints, lowercase 64-hex candidate identity, exact non-bool integer
  costs/rounds, finite representability, positive rounds, nonnegative costs and exact
  booleans. Assessment candidates are detached tuples with unique candidate keys.
  `state.py:331` appends both optional fields after all historical fields and separately
  freezes/de-duplicates their records. Existing ArchNode behavior is unchanged.
- `graph.py:85` filters each grant by exact capability/entity, both live physical nodes,
  original source ownership at sufficient level, original receiver serving membership,
  and an integration-kind edge between that physical pair. `owner_nodes` returns sorted
  distinct original/native or granted physical sources. The new input does not rewrite
  nodes, ownership, roles, serving membership or currency membership; no transitive
  grant ownership is inferred.
- `graph.py:125` validates exclusions before either branch, including null/wrong
  containers, malformed tuples, non-string/blank keys, unknown kinds, reversed or self
  endpoints. Well-formed unknown identities are no-ops. Edge identity includes kind,
  so removing a failover edge leaves a parallel network edge intact.
- `graph.py:150` retains the legacy default query and implements explicit native
  exclusions. With access present, native routes compete with each valid grant's
  client-to-receiver prefix with its source excluded, followed by the physical source.
  Selection is minimum path length then node-key tuple. Receiver capacity and reliability
  are unavoidable; P0 capability-specific capacity is reused without unit conversion.
- `graph.py:280`, `graph.py:290`, `technology.py:114`, and `events.py:181` use the same
  contextual route for service SPOFs, before/after blast and load-bearing failover-kind
  removals. Native/imported alternatives both count. Failed-node bottleneck/RTO selection
  and the explicit global physical `node_is_spof` predicate retain their old meanings.
- `technology.py:66` writes exactly the detached five-field grant rows at
  `evidence.data_adequacy.entities[entity].access_via`, filtered at the requested level,
  deduplicated and sorted by all five fields. Production no-valid-grant cases produce
  `[]`; legacy inputs omit the field. Distinct original owners retain the old
  inconsistency penalty; two grants to one physical source do not create two owners.
- `ledger.py:274` validates the complete watch-key set before evaluating any watch,
  including nonraising watches, current checked round and effect dates through the
  authored horizon. `ledger.py:289` chooses an affordable witness by cost then key.
  The new episode quote is the minimum over all supplied credit-eligible candidates,
  independently of affordability. Empty assessments yield None/false; later witnesses
  can set persistent actionability without changing the initial quote or first-shown
  round. P4 owns the truth of the compact attestations, including actual effect,
  original action-credit eligibility and full affordability; this engine does not
  claim to infer those witnesses from the hash.
- AST comparison confirms unchanged original generic price/funds functions, action
  matching, status precedence, projection, ArchNode, failed-node and outage functions.
  Production tests also invoke real matching actions, invalid original commitment times,
  still-raising guard, clear/fire precedence, terminal history and second fire stamping.
- Exactly nine files differ: five allowed engine files, the new focused test and DoD,
  CONTRACTS and design07. Metrics delegates to the revised helpers and needs no edit.
  Preconditions, scorer equations, old tests/P0 tests, fixtures/seeds, pack values,
  dependencies, runtime service/persistence and frontend files are untouched.
- `CONTRACTS.md:564` contains the exact approved literal addition plus the explicit
  credit-eligibility/future-producer clarification, contract-v1 changelog, dated header,
  and link to the frozen P0b spec. Its old generic-price entry is now explicitly the
  absent-input compatibility path. `design/07-decision-consequence-map.md:269` contains
  the approved subsection with a dated contract-v1 changelog. Every added relative link
  resolves. The literal text and source/spec identities are checked by the auditor script.

## Independently executed acceptance checks

Environment: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`, PYTHONPATH pointing at
the tested tree's backend, PYTHONDONTWRITEBYTECODE=1. Tests used real pack/seed/round
calculations and disposable SQLite databases. Builder and supervisor passing logs were
not substituted for these executions.

| Check | Result | Evidence |
|---|---|---|
| Exact combined candidate full check | **604 passed in 33.70s**, all guards green, **all 44 fixtures** behave as named | `/tmp/mis-sim-m1-production-auditor-check.log` |
| Focused P0b + unchanged P0 + original scoring/round pins | **307 passed in 9.95s** | `/tmp/mis-sim-m1-production-auditor-focused.log` |
| Independent real-catalog interface probes | PASS: physical route/1125 capacity/reliability; exact entity/provenance; no role/currency leakage; SPOF/blast/exclusions/failover; assessment bounds/aliasing/quote/opportunity/action clock | `/tmp/mis-sim-m1-production-auditor-probes.log` |
| Independent complete legacy24 capture | **24 results, every canonical byte equals the supplied baseline** | `/tmp/mis-sim-m1-production-auditor-evidence/independent-full24.json` |
| Existing P0 six-hash-seed checks | PASS through focused and full suites; seeds 0, 1, 2, 3, 42, 99 retain stable traversal and complete full24 output | Unchanged `test_engine_runtime_inputs.py`, focused log |
| Direct Riverside validator | **0 errors, 0 warnings**, exit 0 | `/tmp/mis-sim-m1-production-auditor-validator.log` |
| Exact scope, builder/replay bytes, old algorithm ASTs, literal docs/links, diff whitespace | PASS | Auditor probes script/log |
| All mutation-restored groups and final restored full check | PASS; all 604 tests, all guards and 44 fixtures | `/tmp/mis-sim-m1-production-auditor-evidence/restored-make-check.log` |

The independent full capture is **1,656,959 bytes**, SHA256
`e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`.
Canonicalization was `json.dumps(results, sort_keys=True, separators=(',', ':'),
allow_nan=False).encode()`. The supplied baseline's size/hash were verified before the
direct byte comparison. This includes non-score evidence, statuses, event outcomes and
units, not only a score digest.

## Actual source mutations and restoration

Exported the exact candidate with `git archive` to
`/tmp/m1-p0b-auditor-mutations-7xy0y8ho`. Each plant changed actual executable source,
not an assertion or expected value. Each failing command exited 1 with test failures;
the exact original source bytes were restored and the same group then exited 0.

| Planted regression | Group | Failure count | Restored passed |
|---|---|---:|---:|
| Return receiver as physical owner | access_scope | 4 | 14 |
| Emit raw/unfiltered grant provenance | access_scope | 11 | 14 |
| Add grant sources to direct native targets, bypassing receiver | access_path | 5 | 10 |
| Accept a non-integration edge for the grant | access_path | 1 | 10 |
| Use old raw physical blast logic | access_failure | 1 | 50 |
| Use old raw physical failover logic | access_failure | 1 | 50 |
| Skip exclusion validation | access_failure | 46 | 50 |
| Fall back to generic price for empty assessments | assessment | 4 | 33 |
| Rewrite an existing initial quote from current candidates | assessment | 3 | 33 |
| Skip complete watch-key coverage | assessment | 3 | 33 |
| Retain caller-owned lists | immutable | 2 | 101 |
| Skip capital-cost validation, admitting bool/malformed values | immutable | 11 | 101 |
| Add access evidence to the absent-input result | legacy | 2 | 2 |

Exact substitutions, command arrays, original source hashes and failing/restored summaries
are in `/tmp/mis-sim-m1-production-auditor-mutations.py` and
`/tmp/mis-sim-m1-production-auditor-evidence/mutation-results.json`. Each row has separate
`NAME-failing.log` and `NAME-restored.log` files in that evidence directory.

The first restored `make check` in the archive passed 604 tests but its purity guard
could not run `git ls-files` because the archive had no Git metadata. This was an audit
harness failure; retained log: `restored-make-check-initial-no-git.log`. I initialized
Git only inside the disposable archive, added exactly the candidate's tracked engine
inventory, verified that inventory and every restored engine byte against the candidate,
and reran the full check successfully. The corrected reproduction script includes this
setup. No guard or product source was weakened. The candidate worktree was not edited.

## Reproduction and final state

From the audited tree:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-production-auditor-probes.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-supervisor-baseline.json /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_engine_production_inputs.py backend/tests/test_engine_runtime_inputs.py backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONDONTWRITEBYTECODE=1 M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-supervisor-baseline.json make check
PYTHONDONTWRITEBYTECODE=1 /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-production-auditor-mutations.py
git diff --check c4a095b 1729a8966974cf484a25f226290790f6024486c1
git status --porcelain
git rev-parse HEAD main
```

Final inspected candidate state is clean at the exact accepted SHA. Main remains
`952aeacd749a4ca152057bf4bbde5f94c2e12df9`, unchanged from preparation.
No repository source/docs/register fixes, subagents, merges, pushes, deploys or shared
database writes were performed by this auditor. Evidence and this report are outside
the repository.

Quality ladder: contract/source verification, implementation and pure runtime checks,
and independent audit apply and pass. Migrations/new DB scoping, auth, browser, UX,
screenshots and visual design checks are **N/A**: this packet adds no table, query, API
or visible surface. Existing isolation/validator guards nevertheless ran in the full
check. The supervisor owns integration of the audit record and P0B-BLD-001 residue.

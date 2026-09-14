# M1 P0 independent build audit — ACCEPT

Date: 2026-09-14. Auditor: `/root/m1_p0_build_auditor`, independent of the P0 author,
builder and supervisor living-document edits. Fresh audit context; no builder execution
log was used as proof of a passing check.

**ACCEPT the bounded P0 candidate `7dbb4c80cdced9c1012095b7dd62e646883b6c26`.**
Audited worktree: `/tmp/mis-sim-m1-p0-integration`, branch `build/m1-p0-integration`.
Comparison base: `792a6f8`. Frozen specification: `818c54acae3a05b6aa99d6e5ebeb451269c13c8c`.
The six implementation/test files are byte-identical to builder implementation
`68402fa2538a5210484bda86dd0e8a2a8b2555de`.

This acceptance covers the optional in-memory capacity/RTO inputs, their existing consumers,
deterministic traversal, focused tests, DoD and living-document deltas. It does not complete
M1, approve its separate master transition contract, or accept later production projection,
estate, organisation, accounting, integration-access or repair-pricing work.

## Findings

**No open P0 findings. No new finding IDs or accepted implementation residues.**

Existing `M1-P0-SR-001` and `M1-P0-SR-002` remain recorded as closed at specification review
in `findings/OPEN-REGISTER.md:559` and `:560`; this audit does not replace their historical
review evidence. The former's implementation-side obligation is now independently proved
by actual min-to-sum and other candidate-source mutations. The latter's application
obligation is satisfied by the exact living text, v1 changelogs and resolved target links
checked below. The supervisor retains ownership of recording this build acceptance at
integration. No repository file was edited by this auditor.

## Source, contract and scope audit

Read the complete root GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL and CONTRACTS first;
then P0 spec/review/DoD and authority, the required original 1.4 spec/closeout, 1.5
spec/contract, 1.6 spec, design04/07/north-star, decision inventory, complete changed
consumers, remaining engine basis files, casepack models/loader, round
runner/snapshot/models/actions/db, calibration harness, historical seeds, pin tests and
Makefile. No applicable AGENTS.md was found.

The relevant contract states: “A present map forbids scalar throughput”; omitted/None
entries impose no capability ceiling, and explicit RTO precedes historical lookup.
The existing metric rule still returns 0.0 for absent paths or nonpositive capacity.
The duration equation remains `round(base_rto × failover_factor × staffing_modifier, 1)`.

- `state.py:54` appends both defaulted fields after every old positional field.
  `state.py:57` accepts Mapping containers, copies before freezing, rejects malformed keys,
  simultaneous scalar/map input and invalid new numerics. `state.py:80` excludes booleans
  and non-int/float types, rejects nonfinite/negative values and RTO zero, and translates
  arbitrarily large integer conversion overflow to ValueError. Absent maps preserve the
  historical scalar path without new scalar validation.
- `graph.py:113` selects mapped values only with capability context. Missing context
  refuses even an empty map; explicit unknown capability means no ceiling. The path
  helper skips unknown physical nodes and None values, includes zero and takes min.
  Technology (`technology.py:110`), utilisation (`metrics.py:55`) and event primary
  capability binding (`events.py:177`) all supply context. `events.py:145` preserves first
  path-node tie selection using the same selector.
- `events.py:217` uses explicit node RTO when present, otherwise preserves catalog lookup
  by failed key and the 8-hour fallback, including historical unknown-node lookup behavior.
  Staffing, failover, duration and evidence formulas retain their previous structure.
- One mapped node remains one physical placement and one failure identity. Existing
  placement and blast-radius consumers require no changes. `graph.py:39` sorts unique
  sources; `graph.py:53` sorts adjacency neighbors while preserving shortest-path behavior.
- The exact nine changed files are the five allowed engine files, new focused test,
  P0 DoD, CONTRACTS and design07. No seed, old test, pack value, scorer equation, runner,
  dependency, schema, DB, UI or service change is in the diff. All caller/producer search
  hits were inspected; current production snapshot construction remains scalar-only.
- `CONTRACTS.md:531` and `design/07-decision-consequence-map.md:256` contain the specification's
  literal approved additions. Both identify engine input contract v1 and have dated
  changelog entries. All new links resolve. Added explanatory wording is confined to
  frozen construction/context behavior and the explicit later-production boundary;
  it introduces no new scoring or M1-completion claim. The frozen spec file SHA-256 is
  `06eaea0066cc8ae08e1826aab1c169c063fad5700cfbabfd4d591fcef03bbbbc`.

## Independently executed checks

Environment: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin` first on PATH;
PYTHONPATH points to the tested tree's backend. Databases were disposable SQLite only.

| Check | Actual result | Evidence |
|---|---|---|
| Focused candidate tests, supplied supervisor baseline | **95 passed in 7.74s** | `/tmp/mis-sim-m1-p0-auditor-44fj8ld6/focused.log` |
| Original scoring and round pin tests | **14 passed in 1.63s** | Same directory, `pins.log` |
| `make check` on exact combined candidate | **406 passed in 31.08s**, every standalone guard green, **all 44 fixtures** behave as named | `/tmp/mis-sim-m1-p0-auditor-check.log:8`, `:151`, `:192` |
| Riverside validator | **0 errors, 0 warnings**, exit 0 | Direct independent `backend/bin/validate_casepack backend/packs/riverside_grocery` run |
| Six real hash-seed processes | Seeds **0, 1, 2, 3, 42, 99** each select `start,a,end`, bottleneck `a`, capacity 10; repeated/reversed sources select `a,end` | `candidate-seed{0,1,2,3,42,99}.log` in evidence directory |
| Full legacy comparison in each of six fresh games | **24 results each; every canonical byte equals the supervisor baseline** | `candidate-seed{0,1,2,3,42,99}.json` in evidence directory |
| Exact scope, implementation bytes, frozen spec, literal documents, links, whitespace | PASS | `/tmp/mis-sim-m1-p0-auditor-scope.log` |
| Final worktree state | Clean; HEAD remains exact candidate | `git status --porcelain`; `git rev-parse HEAD` |

Each complete legacy capture is **1,656,959 UTF-8 bytes**, SHA-256
`e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`.
Canonicalization was independently performed as
`json.dumps(results, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()`.
The supplied `/tmp/mis-sim-m1-supervisor-baseline.json` was itself checked for the frozen
size/hash before direct byte comparison. The separate score digest is unchanged at
`0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`.
This proof includes event/status/unit/evidence fields, rather than relying on that score subset.

Reproduction commands from the audited root:

```bash
PYTHONPATH=backend M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-supervisor-baseline.json /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_runtime_inputs.py
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-supervisor-baseline.json make check
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-p0-auditor-proofs.py
/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-p0-auditor-scope.py
```

## Actual candidate defects and restored closing checks

The auditor's own executor exported the exact commit with `git archive` into
`/tmp/mis-sim-m1-p0-auditor-44fj8ld6/candidate`. Each plant modified actual source in that
disposable copy. No assertion or expected value was changed. Every failing command exited
1 with assertion failures, then the original bytes were restored and the same group exited
0. All engine source bytes were compared with the audited candidate after restoration.

| Plant | Selected group | Failing result | Restored result |
|---|---|---|---|
| Mapped selector always reads reports | capacity | 6 failed, 57 passed | 63 passed |
| Path min changed to sum | capacity | 4 failed, 59 passed | 63 passed |
| Technology omits capability argument | capacity | 8 failed, 55 passed | 63 passed |
| Explicit-RTO precedence disabled | rto | 6 failed, 13 passed | 19 passed |
| Construction retains caller mapping alias | immutable | 2 failed | 2 passed |
| TeamState appends a second physical facet for a multi-capability node | physical | 1 failed, 6 passed | 7 passed |
| BFS neighbor sorting removed | hashseed | 2 failed, 6 passed | 8 passed |
| Returned staffing-modifier evidence increased by 1 | legacy | 1 failed, 8 passed | 9 passed |

The physical plant creates an actual duplicate node. The legacy plant changes a real
persisted evidence value outside the score-only digest. Group selection is the shipped
test command with `-k GROUP`, PYTHONPATH set to the disposable backend,
PYTHONDONTWRITEBYTECODE=1, and M1_P0_LEGACY_BASELINE set to the supplied baseline.
Exact substitutions, executed argument arrays and summaries are retained in
`/tmp/mis-sim-m1-p0-auditor-44fj8ld6/proof-results.json`; each plant has separate
`NAME-failing.log` and `NAME-restored.log` files there. Combined transcript:
`/tmp/mis-sim-m1-p0-auditor-proofs.log`.

Quality ladder: contract/source verification, implementation checks, pure runtime and
independent audit are complete. Migrations, new DB isolation, auth/browser/UX/screenshots
are **N-A** because P0 adds no database/query/API or visual surface. Existing isolation
guards still ran via make check. No repository edits, fixes, subagents, merges, pushes,
deployments or shared-database writes were performed.

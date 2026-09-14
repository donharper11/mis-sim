# M1 P0 builder evidence

Date: 2026-09-14. Builder: `/root/m1_p0_builder`.
Branch: `build/m1-engine-inputs`; worktree: `/tmp/mis-sim-m1-engine-inputs`.
Assigned clean base: `4490b56e512513dec8600a193073a71c88ba95f6`.
Frozen reviewed spec: `818c54acae3a05b6aa99d6e5ebeb451269c13c8c`;
independent specification review: [review.md](review.md).
Verified implementation commit: `68402fa2538a5210484bda86dd0e8a2a8b2555de`.
This report is a documentation-only successor to that exact implementation. Resolve the
complete handoff candidate with `git rev-parse build/m1-engine-inputs`; the supervisor
receives its full SHA separately. **Independent build audit pending; no merge approval.**

## Contract and scope

Required governance, protocols, living contracts, P0 authority/spec/review and the P0 basis
readset were inspected before implementation. Existing living contracts retained:
`duration_hours = round(base_rto_hours(node) × failover_factor × staffing_modifier, 1)`;
path metrics return `0.0` when no path or nonpositive capacity exists; placement values are
`on_prem`, `cloud`, `saas`. New explicit RTO only changes the input's precedence.

Appended immutable `capacity_by_capability` and `base_rto_hours` to `ArchNode`.
Construction copies/freezes mappings and rejects malformed new inputs with `ValueError`.
The shared graph selector requires capability context for mapped path nodes and preserves
legacy scalar behavior. Technology, metrics and failed-node binding pass their capability;
the minimum, demand division, clipping, event and scoring equations are unchanged.
BFS sorts unique sources and neighbor keys. Physical node count/identity is unchanged.

Only five engine files, the new focused test, and this new DoD changed. No dependencies,
casepack values, old tests, seeds, pins, runner/service, DB, UI, or shared documents changed.
The supervisor owns the exact living CONTRACTS/design delta and review-finding reconciliation
at audited integration, as specified. P0 implements no production projection or M1 transition.
Pack-capability vocabulary and duplicate serialized keys remain the future projection/parser
boundary's responsibility; no caller-facing parser is added here.

## Preflight: all reported before any code

Environment throughout: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin` first on `PATH`,
`PYTHONPATH=backend`, repository-root working directory unless noted. Existing dependencies
were reused without installation or changes. Every database was disposable SQLite.

| PF | Status | Executed check and observed evidence |
|---|---|---|
| 0 | PASS | `git status --porcelain` produced no output; `git rev-parse HEAD` returned exactly `4490b56e512513dec8600a193073a71c88ba95f6`. |
| 1 | PASS | Spec `rg` returned graph definition at base `graph.py:113`, callers `technology.py:110`, `metrics.py:55`, `events.py:149`; event helper `events.py:145`; old unsorted neighbor loop `graph.py:53`; catalog RTO lookup `events.py:216–217`. Inspected these bodies and both BFS source/neighbor loops. |
| 2 | PASS | `PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py` → **14 passed in 1.65s**. |
| 3 | PASS | Executed the spec's complete `run_calibration` capture with `TemporaryDirectory`; independently saved `/tmp/mis-sim-m1-p0-builder-baseline.json`. Exactly **24 results**, **1,656,959 bytes**, SHA-256 `e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4`; actual bytes also equal `/tmp/mis-sim-m1-supervisor-baseline.json`. |
| 4 | PASS | Spec `rg` across app/seeds/tests/frontend returned only the three consumers and graph/event definitions, `round/snapshot.py:135`, nine constructors in `seeds/riverside_r3.py`, and `test_engine_scoring.py:114,134,142`. Read all producers/callers: omitted-context calls use scalar nodes, all existing constructors omit both new fields. No frontend hit. |
| 5 | PASS | `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH make check` → **311 passed**, every guard green, **all 44 fixtures**. Full log `/tmp/mis-sim-m1-p0-builder-preflight-check.log` (pytest line 7, fixtures line 150, final success line 191). |

## Definition of done

Focused command (executed):

```bash
PYTHONPATH=backend M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-p0-builder-baseline.json /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_runtime_inputs.py
```

Result: **95 passed in 7.29s**. The tests are ordinary pytest tests reached by `make check`.
Each required group is independently selected by appending `-k capacity`, `-k rto`,
`-k immutable`, `-k physical`, `-k hashseed`, or `-k legacy`; groups intentionally overlap
where one test proves several contracts.

| Item | Status | Evidence |
|---|---|---|
| Additive fields/positional compatibility | PASS | `state.py:54–72`; test `test_legacy_positional_constructor_compatibility` supplies every old positional argument and sees both new defaults as None. |
| Capability units and every consumer | PASS | Tests 92–121: one physical node 8000 orders/100 reports, demands 6000/80 gives capacity factors 1/1 and utilisation .75/.8. Series node 2000/200 gives minima 2000/100, capacity .333333/1, utilisation 3/.8. Event binding selects end/start according to primary capability, including multi-cap events; demand precondition reads the same metric and retains strict boundary. |
| Null/zero/context/error paths | PASS | Tests 127–233 cover None/empty/missing/None-valued maps, zero, mixed scalar and mapped transit, unknown explicit capability, unknown physical keys, empty paths, disconnected paths, zero-demand metric, first-in-path ties, both omitted and explicit-None contexts, malformed containers/keys, boolean/string/negative/nonfinite/overflow values, and scalar/map conflicts. Existing scalar inputs are not newly validated. Dict/UserDict/read-only Mapping inputs accepted. |
| RTO precedence and historical defaults | PASS | Tests 235–284: unique physical ID with explicit 12 gives base 12/duration 36; explicit beats authored catalog 4; absent uses catalog 4 or default 8; zero/negative/nonfinite/string/bool/overflow and malformed objects refuse. Positive integer/fractional floats work. Existing staffing/failover factors retain their equations and evidence. |
| Immutability | PASS | Test 287 mutates caller dict/UserDict after construction: node capacities and computed technology remain unchanged. Direct map mutation raises TypeError; field reassignment raises FrozenInstanceError. `dataclasses.replace` copies the immutable map again. |
| Physical identity | PASS | Tests 307–331: one mapped node counts one placement; threshold 2 false; removing it loses both capabilities; each event binds that same key. Explicit SPOF first-occurrence and empty-event binding unchanged. |
| Deterministic traversal | PASS | Tests 338–362 start real processes with hash seeds **0,1,2,3,42,99**; each returns `start,a,end`, bottleneck `a`, minimum 10. Duplicate/reversed sources choose `a,end`; empty sources/targets, disconnection, equal targets and shorter alternatives preserve BFS semantics. |
| Full legacy payloads and historical pins | PASS | Test 365 executes all 24 results under each of six hash seeds, comparing complete canonical bytes across seeds, frozen full hash/size, and independently captured base bytes via the environment variable. Original 14 pin tests rerun: **14 passed in 1.64s**. No pin changed. |
| Real planted-defect proof | PASS | All **15 actual code mutations** failed their required pytest group with exit 1 and passed after restoration with exit 0; full details below. No expected value was changed. |
| Full verification | PASS | `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH M1_P0_LEGACY_BASELINE=/tmp/mis-sim-m1-p0-builder-baseline.json make check` → **406 passed in 31.10s**, all guards green, **44 fixtures**. Log `/tmp/mis-sim-m1-p0-builder-candidate-check.log` (lines 8/151/192). |
| Casepack validator | PASS | `PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend backend/bin/validate_casepack backend/packs/riverside_grocery` → 0 errors, 0 warnings. |
| Whitespace and scope | PASS | `git diff --check` clean; Python set comparison of `git diff --name-only 4490b56...` plus untracked paths against the seven-file allowlist passed. The implementation commit contains only six code/test files; its successor adds only this DoD. |
| Behavior/document ripple | PASS | `rg` for throughput/bottleneck/RTO/map across CONTRACTS, design, P0 handoff, engine and snapshot inspected. Engine docstrings updated; legacy snapshot still supplies scalar only. Supervisor applies frozen living text on audited integration; builder does not edit shared files. |
| Findings reconciliation | N-A (builder) | No new finding or old finding closure claimed. Supervisor retains ownership of the two spec-review closures and shared register integration. |
| Ladder 1/2 and pure runtime | PASS | Contracts inspected, pytest/guards/validator pass, real seed→runner→complete payload checks on disposable SQLite. |
| Migrations, new DB isolation, browser/auth/UX/screenshots | N-A | This packet adds only pure in-memory engine inputs; no DB schema/query, service/API or visual surface. Existing isolation guards run through `make check`. |
| Independent build audit | PENDING | Fresh auditor must inspect the exact code and supervisor living-document candidate, rerun checks and one mutation per group. Builder never acts as auditor. |

Complete legacy artifacts are retained outside the repository:
`/tmp/mis-sim-m1-p0-builder-candidate-seed{0,1,2,3,42,99}.json`.
These copies come from the final restored disposable candidate's six-process run; all five
engine files were byte-compared to the implementation before retaining them. All six JSON
files were then directly byte-compared to the independently captured preflight baseline.
Full digest above; separate unchanged historical score-only digest:
`0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1`.

## Executed candidate mutation evidence

Executor: `/tmp/mis-sim-m1-p0-builder-mutations.py`.
Command: `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python /tmp/mis-sim-m1-p0-builder-mutations.py`.
Full transcript: `/tmp/mis-sim-m1-p0-builder-mutations.log`.
Disposable copy and all detailed failure/restoration logs:
`/tmp/mis-sim-m1-p0-builder-mutations-x5lrzasr/`.
Each row's exact substitution, command and results are also in that directory's
`results.json`; its `<mutation>-failing.log` and `<mutation>-restored.log` contain full pytest
assertion output. That copy's original code is restored and retained for audit.

For every row, the executed command in that disposable root was
`/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python -m pytest -q backend/tests/test_engine_runtime_inputs.py -k GROUP`,
with that copy's backend on PYTHONPATH, bytecode writes disabled, and the independent baseline
environment variable set. Every failing command exited **1**; every restored command exited **0**.

| Mutation / GROUP | Actual candidate-source change | Failure → restored result |
|---|---|---|
| `capacity_scalar` / capacity | graph mapped selector reads scalar throughput | 6 failed, 57 passed → 63 passed |
| `capacity_wrong_unit` / capacity | graph mapped selector always reads reports | 6 failed, 57 passed → 63 passed |
| `capacity_min_to_sum` / capacity | graph `min(caps)` changed to `sum(caps)` | 4 failed, 59 passed → 63 passed |
| `capacity_technology_context` / capacity | technology call omits capability argument | 8 failed, 55 passed → 63 passed |
| `capacity_metric_context` / capacity | metric call omits capability argument | 8 failed, 55 passed → 63 passed |
| `capacity_event_context` / capacity | failed-node call omits primary capability | 8 failed, 55 passed → 63 passed |
| `capacity_missing_context` / capacity | graph missing-context refusal returns None | 8 failed, 55 passed → 63 passed |
| `capacity_validation` / capacity | state replaces finite test with True | 3 failed, 60 passed → 63 passed |
| `rto_precedence` / rto | events explicit-RTO condition replaced by False | 6 failed, 13 passed → 19 passed |
| `rto_validation` / rto | state removes positive-zero refusal | 1 failed, 18 passed → 19 passed |
| `immutable_alias` / immutable | state retains original capacities instead of `dict(capacities)` | 2 failed → 2 passed |
| `physical_duplicate` / physical | temporary TeamState constructor appends a replaced `_facet` node for every multi-capability map | 1 failed, 6 passed → 7 passed |
| `hashseed_neighbors` / hashseed | graph neighbors revert to unsorted adjacency | 3 failed, 5 passed → 8 passed |
| `hashseed_sources` / hashseed | graph source loop reverts to input order | 6 failed, 2 passed → 8 passed |
| `legacy_evidence` / legacy | events adds 1 to returned staffing-modifier evidence only | 1 failed, 8 passed → 9 passed |

The physical mutation inserts real duplicate state, then placement/identity assertions catch
it. The legacy mutation changes a real persisted event-evidence value outside the score-only
digest, and the full-payload check catches it. Final executor line:
`ALL 15 candidate-code mutations detected and restored: /tmp/mis-sim-m1-p0-builder-mutations-x5lrzasr`.

No push, main merge, deployment, shared database write, subagent, or scope expansion performed.

## Supervisor integration closeout

The builder's pending-audit status above records its handoff. A fresh independent auditor
subsequently **ACCEPTED `7dbb4c80cdced9c1012095b7dd62e646883b6c26`**, including the
supervisor's living CONTRACTS/design changes, with no open P0 findings. The supervisor
independently inspected the implementation and ran `make check`: 406 tests, all guards and
44 fixtures passed (`/tmp/mis-sim-m1-p0-supervisor-check.log`). Full code bytes are retained
unchanged at integration. The two spec-review findings now also have their implementation
and living-document obligations verified; their register rows are reconciled in the same
integration commit. See [the independent build audit](../../../../findings/recovery-engine-inputs-2026-09-14.md).
This closes P0 only; M1's production transition and decision-only game remain unfinished.

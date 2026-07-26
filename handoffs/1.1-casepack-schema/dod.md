# 1.1 — Definition of Done

> Filled by the BUILDER. This table IS the session report.

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6 reported | PASS | Row 1: `git ls-tree --name-only origin/main -- backend/app/` listed `backend/app/__init__.py`, `api`, `config.py`, `database.py`, `main.py`, `models`. Row 2: `grep -c "^## " CONTRACTS.md` -> `14`. Row 3 initially failed without a password; rerun with supplied credential: `select count(*) from stakeholders; select count(*) from strategy;` -> `14`, `4`. Row 4 rerun with supplied credential: `select count(*) from component_types_master;` -> `45`; design/01 §3 records ~19 buildable. Row 5: `grep -n "pydantic\|PyYAML" backend/requirements.txt` -> pydantic pinned and `PyYAML==6.0.2` present. Row 6: on initial preflight `ls backend/packs 2>&1` -> `No such file or directory`; current `main` later included the pack before this branch was cut. |
| Step 1 — schema document | PASS | `docs/casepack-schema.md` documents every section, every field, type, required/optional status, and worked examples. |
| Step 2 — Pydantic models | PASS | `PYTHONPATH=backend python3 -c "from app.casepack.models import Casepack; from app.casepack.loader import load_casepack; cp=load_casepack('backend/packs/riverside_grocery'); print(cp.metadata.pack_key, len(cp.capabilities), len(cp.catalog), len(cp.strategies))"` -> `riverside_grocery 7 10 4`. |
| Step 3 — loader with named errors | PASS | Malformed temp pack with invalid `pack_key` prints `pack.yaml: metadata.pack_key: Value error, must be snake_case`. |
| Step 4 — skeleton pack loads | PASS | The pack is real content per spec §5.9, not a TODO skeleton. Seed command loads `backend/packs/riverside_grocery` and prints counts plus pinned figures. |
| Step 5 — checks script | PASS | `backend/app/casepack/checks.py` exposes `run_all_checks` and functions for I3-I8. `PYTHONPATH=backend python3 -m compileall -q backend/app/casepack && echo compileall_ok` -> `compileall_ok`. |
| I1 no pack-identity branching | PASS | `git ls-files backend/app/casepack \| xargs grep -niE "riverside\|grocer\|pack_key *==" \|\| true` -> no output. |
| I2 no displayed English in code | PASS | `git ls-files backend/app/casepack/*.py \| xargs grep -nE '"[A-Z][a-z]+ [a-z]+' \| grep -v '#\|"""\|log\|raise' \|\| true` -> no output. |
| I3 keys snake_case | PASS | `run_all_checks(load_casepack(...))` -> `I3: PASS []`. |
| I4 every role fillable | PASS | `run_all_checks(load_casepack(...))` -> `I4: PASS []`. |
| I5 strategy weights sum 1.0 | PASS | `run_all_checks(load_casepack(...))` -> `I5: PASS []`; seed prints all four strategy sums as `1.000`. |
| I6 `cleared_by` keys resolve | PASS | `run_all_checks(load_casepack(...))` -> `I6: PASS []`. |
| I7 demand curves length = rounds | PASS | `run_all_checks(load_casepack(...))` -> `I7: PASS []`. |
| I8 YAML round-trips | PASS | `run_all_checks(load_casepack(...))` -> `I8: PASS []`. |
| O1 capability/activity — recorded | PASS | Recorded in `docs/casepack-schema.md`: one concept, represented by `Capability.chain_position`. |
| O2 demand curve form — recorded | PASS | Recorded in `docs/casepack-schema.md`: explicit absolute per-round arrays. |
| O3 preference file split — recorded | PASS | Recorded in `docs/casepack-schema.md`: one file per decision domain under `preferences/`. |
| `CONTRACTS.md` updated for any new cross-cutting field | PASS | No new cross-cutting field added. Existing contracts cover `pack_key`, `placement`, `required_roles`, `level_of_detail`, `cleared_by`, strategy weights, and labels. |
| Every §5 section traced to a factor in `design/02` | PASS | `docs/casepack-schema.md` states the scoring/reporting factors fed by each section. Labels are justified by Governance/Contracts display-string rule. |
| PyYAML added to `requirements.txt` | PASS | `backend/requirements.txt` includes `PyYAML==6.0.2` on line 8 in current `main`; row 5 verified. |
| Auth / instance-isolation / browser canaries | PASS | **N-A** — headless, no runtime state, no browser surface. Casepacks carry no `instance_id`; runtime scoping begins when module 2.5 loads a pack into a simulation instance. |
| **Seed** — Riverside pack populated, loader prints real counts, weights sum to 1.000 | PASS | `PYTHONPATH=backend python3 -m app.casepack.seed riverside_grocery` prints `7 capabilities, 10 catalog items, 4 strategies`, all four weights sum `1.000`, and pinned figures: round 3; capital `44000 of 220000`; run_rate `58300`; scorecard `61/48/39/27`; signals `3`; inbox `3`; staff `2.0`; load `3.4`; over `170`; review capital `174000 of 220000`; remaining `46000`; run_rate_after `62200`; run_rate_before `58300`; warehouse/store/finance people and contribution figures. |
| No unlisted `TODO` in shipped pack content | PASS | `git ls-files backend/packs/riverside_grocery \| xargs grep -n "TODO" \|\| true` -> no output. |

## Seed Output

```text
7 capabilities, 10 catalog items, 4 strategies
cost_leadership weights sum 1.000
differentiation weights sum 1.000
customer_supplier_intimacy weights sum 1.000
focus_strategy weights sum 1.000
pinned figures: round 3; capital 44000 of 220000; run_rate 58300; scorecard 61/48/39/27; signals 3; inbox 3; staff 2.0; load 3.4; over 170; review_capital 174000 of 220000; remaining 46000; run_rate_after 62200; run_rate_before 58300
warehouse people 34 contribution 25
store_operations people 140 contribution 44
finance people 8 contribution 81
```

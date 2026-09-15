# P2 estate successor audit — PASS

Candidate: `b4bfec9d154277ed92450cf2bc0129a39f83fda2`
Base: `3f6e8a2`
Worktree: `/tmp/mis-sim-m1-p2-estate-v1`
Audit date: 2026-09-15

## Decision

**PASS.** The successor resolves all five blocking findings from the prior P2 audit. Direct lifecycle, resource, projection, DTO-boundary, mutation, and restoration checks passed.

## Scope and integrity

`HEAD` matched the requested candidate. The worktree was clean, `git diff --check 3f6e8a2..b4bfec9d154277ed92450cf2bc0129a39f83fda2` passed, and the base diff contained exactly these five files:

```text
backend/app/simulation/estate.py
backend/app/simulation/projection.py
backend/app/simulation/resources.py
backend/tests/test_simulation_estate.py
handoffs/recovery/decision-evolution/estate/dod.md
```

No candidate or root files were modified.

## Prior RETURN findings rechecked

- **Cancellation/abandonment:** a pending SaaS acquisition was removed from `assets` on both cancel and kill. It was absent from resource projection and cannot materialize later.
- **Replacement:** same asset/placement/config replacement returned no project, no charge and no arrival. A cloud replacement preserved `trained_count=37`, `adoption=0.6`, `process="partial"`, and `ever_trained=True` through arrival. Retiring the target in the same round while its replacement was pending raised `SimulationError(conflicting_commands, replacement)`; retirement after arrival was accepted.
- **Policy and retirement timing:** selecting `full_audit_trail` changed policy load from `0.0` to `0.08` and total load from `3.7` to `3.78`. An asset with `retired_round=2` was live in round 1 and absent in round 2. A future-retired integration contributed `0.4` in round 1 and `0.2` in round 2.
- **Projection and EntityAccess:** `True`, `1.0`, `0`, and `7` were all rejected as round values. Authored grants used authoritative IDs (`initial_pos_product`, `initial_order_accounting`). A dynamically acquired `r1_ecom` receiver and `r2_ec` integration produced an access grant with connection `r2_ec`, confirming dynamic source resolution and exact ID preservation.
- **Acquisition validation:** service units 9 and 100 were rejected with closed `SimulationError(invalid_input, units)`. Unknown catalog, config, and service references were each rejected with closed `SimulationError(invalid_reference, source/config)`; no raw `AttributeError` or `KeyError` leaked.

Initial authored smoke remained correct: 10 assets, 11 connections, 10 projects, 6 catalog rollouts, resource load `3.7`, and recurring opex `16200`.

## Broader direct probe coverage

The audit also exercised source roles/entities, lead and arrival boundaries, pause/continue/kill, terminal/no-op behavior, duplicate/self and joined connection semantics, placement/configuration references, bypass and zero-supply resource factors, rounding/finite guards, staff and integration costs, detached TeamState snapshots, malformed numeric/key/enum inputs, and P1 checkpoint/content immutability probes.

## Gates and mutation restoration

- Focused P2 tests: **10 passed**.
- Combined P2/P1/P0/legacy pins: **331 passed**.
- Supervisor `make check` with `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin`: **628 passed**, all guards green.
- Riverside validator: **0 errors, 0 warnings**.
- Disposable mutation removing the `_round6` finite/non-negative guard made `test_resource_strictness_mutation_guard` fail as expected (`1 failed, 9 deselected`).
- Disposable mutation removing the estate unknown-source guard caused the custom closed-error probe to fail with raw `AttributeError`, confirming the guard is meaningful.
- Candidate worktree remained clean after all checks.

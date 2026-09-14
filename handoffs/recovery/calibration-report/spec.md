# Recovery: complete calibration visibility

Date: 2026-09-14. Tier: Light (read-only reporting; numerical outputs remain untouched).
Owner: assigned reporting builder. Auditor: supervising agent, independently.
Base: planning commit named in dispatch. Read governance/quality/spec protocols, CONTRACTS,
the north-star plan, 1.7 spec, and the source named below before implementation.

## Spec basis and verified problems

Read: `backend/app/calibrate/{inventory,report,harness}.py`, `backend/tests/check_calibration_harness.py`,
`backend/packs/riverside_grocery/{strategies,watch_rules}.yaml`.
The inventory matches the exact string `TODO: calibrate`; strategies.yaml's maintenance
marker has no space and is omitted. At baseline there are 38 marker sites, not the reported 37.
The report prints realised value over all rounds, but BSC perspectives only at the final round.
Earlier event-round values outside the base 0–1 scale are hidden by that summary.

No scoring factors, casepack keys, persisted records or instance queries change. The report
reads existing results; the engine still owns their computation and the user owns balance rulings.

## Allowed files

- `backend/app/calibrate/inventory.py`
- `backend/app/calibrate/report.py`
- `backend/tests/test_calibration_reporting.py` (new)
- `handoffs/recovery/calibration-report/dod.md` (new)

No other file changes without scope amendment. In particular no pack, seed, engine, runner,
dependency, shared-contract/register or original spec edits. No push, deployment or unrelated cleanup.

## Required behaviour

1. Count `TODO:calibrate`, `TODO: calibrate`, and additional horizontal whitespace after
   the colon. Continue counting marker **sites/lines**, not individual numeric values.
2. Exclude the watch-rule marker-convention header by its semantic comment text, not a
   fixed line number, so moving the header cannot change the inventory. Do not suppress
   legitimate markers merely because they occur in a comment. Inspect the current header.
3. Derive the registered-item count from `REGISTER_ITEMS`; no hardcoded 5 in report totals.
4. Keep the realised-value curves and final BSC comparison, and add one readable all-round
   curve table for each of Financial, Customer, Internal Process, Learning & Growth.
   Read each value directly from `RoundResult.scorecard` without rescaling, clipping or recomputing.
5. Report any non-finite or outside-0–1 perspective value with team label, round, perspective
   label and raw value. Wording must call these **score-scale diagnostics requiring review**,
   not a balance verdict. Do not hide or repair the values; the scorecard contract is separate work.
6. Clearly state these archetype curves cover their listed declared strategies only; do not
   imply all strategies were exercised. The historical human gate is not reopened by the report.
7. Show ties honestly in the final ranking; equal firm scores are not ordered with `>`.
8. Default report labels remain readable business labels and the CLI remains report-only.

## Preflight, verification and DoD

Preflight: reproduce baseline marker omission; verify header content; verify current R1/R2
BSC data are present in results but absent from printed tables; capture score digest on a
temporary SQLite database. Never run against configured application DB defaults.

Add meaningful tests with independent expected values: marker whitespace and moved header,
legitimate marker on another line, count changes when REGISTER_ITEMS changes, a synthetic
two-team/two-round report with distinct perspective values, early-round negative/nonfinite
diagnostics, truthful tied ranking and declared-strategy limitation. At least one marker
test and one early-round test must fail on the baseline implementation; record evidence.

Run the real six-round harness against temporary SQLite and `make check`. The score digest
and pack bytes must remain unchanged. 1.4 numeric pins remain unchanged. Compare report
figures to persisted source results, not to another call to the renderer. File allowlist
must be clean. Browser/auth N-A: CLI report. Existing instance canary remains green.

Record commands/results, before/after marker count, displayed example, unchanged digest,
regression proof, limitations and commit SHA in `dod.md`. The supervisor owns shared
register/spec reconciliation after independently auditing the candidate commit.

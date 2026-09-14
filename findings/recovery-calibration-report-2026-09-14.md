# Recovery calibration report audit

Date: 2026-09-14. Candidate: `f858b8a00402eb9889332370a8d90f9788950134`.
Implementation: `0ebba6b7ec2f6ea72b8f317dc9d10324b0b8ba14`; DoD: candidate commit.
Author: supervisor. Builder: `report_builder`. Independent auditor: `report_auditor`,
fresh context with no author/build role. Verdict: **ACCEPT, no findings**.
This record is transcribed by the supervisor from the auditor's returned evidence;
it is not a claim that the supervisor supplied the author-independent audit.

## Independently reproduced evidence

- Clean candidate and exact five-file cumulative scope: the four allowed implementation,
  test and DoD files, plus the expressly authorized own-spec amendment.
- `make check`: **128 pytest tests**, every guard and **44 validator fixtures** pass;
  instance-isolation canary reports zero cross-reads; Riverside validator 0 errors/warnings.
- New focused tests on a fresh archive of original `952aeacd`: **41 fail, 5 pass**;
  on the candidate: **46 pass**. Whitespace variants, moved header, dynamic totals,
  early-round visibility, nonfinite/range diagnostics, ranking ties and scope are covered.
- Fresh baseline and candidate SQLite CLI runs, independently read with instance/team
  filters: **96 round BSC cells, 24 realised cells, 16 final BSC cells and all 25 raw
  diagnostics** match their persisted sources. All 24 complete persisted payloads match
  across versions. All **19 pack files** are byte-identical.
- Score digest remains
  `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`.

Auditor evidence directory: `/tmp/mis-sim-independent-report-audit-sjbog0_3/`;
full check log `/tmp/report-auditor-make-check.log`. Durable reproduction commands and
expected outputs are in `handoffs/recovery/calibration-report/dod.md`.

## Supervisor integration check

The supervisor read the complete production diff and regression tests, applied only the
audited implementation and DoD commits, and reran the 46 reporting tests plus the ten
unchanged scoring tests in a separately installed declared-dependency environment:
**56 passed**. Shared living-spec and register reconciliation accompany this integration.
The original August DoD and its calibration ruling remain historical evidence; their
37-marker count is superseded for current reporting by the live 38-site inventory.

**NS-002 closes on the integration branch** in the commit containing this record. No
remote or main-branch publication is claimed. The combined runtime/report tree receives
another full check before the first-wave integration record is finalized.

## Limits

This improves visibility only. NS-003 score-unit defects and NS-004 decision evolution
remain open. The four archetypes all declare cost leadership; these curves do not establish
all-strategy balance. No pack number, scorer, runner, schema or persisted payload changed.
Browser/auth: N-A, headless reporting. Full financial scoring remains partial and owned.

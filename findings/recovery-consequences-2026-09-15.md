# Final P4 consequences audit

- Candidate: `f43ea7f811026630a5ec282ded6b626d487a085d`
- Base: `73df51d`
- Worktree: `/tmp/mis-sim-m1-p4-consequences-v1`
- Verdict: **PASS**

## Scope and gates

HEAD matched the candidate, the worktree was clean, and `git diff --check` passed. The base-to-candidate diff contains exactly the six allowlisted paths: accounting.py, consequences.py, repairs.py, runner.py mechanical scorer adapter, the focused P4 test, and consequences/dod.md. No scorecard.py or extra docs were added.

Independent gates:

- Focused P4: **8 passed**
- Legacy scorer/runner pins: **190 passed**
- Combined P0–P4 pins: **346 passed**
- Supervisor `make check`: **643 passed**, guards green
- Runtime validator: **0 errors, 0 warnings**

## Direct contract probes

- Repair assessment returned all **8** watch rows, with evaluated metrics (`wh_rollout_01`: baseline `1.0`, candidate `False`).
- Catalogue operation families include `buy_application`, `buy_service`, `connect`, `replace_application`, `replace_service`, `set_policy`, and `set_support`.
- Verified candidates are passed into the engine handoff: **2** engine candidates from the initial assessment; uncredited witnesses and exclusion/history paths are represented.
- Preview returned **13/13** event challenges and a deterministic would-fire list.
- Empty-round resolution returned `result['tco'] == []` and `state.tco_forecasts == []`; no fabricated initial-asset TCO rows.
- Result includes `round == 1`, accounting/state changes, prevention, identity, debt, and TCO evidence.
- Duplicate command keys raise closed `SimulationError(code=invalid_input)`.
- Funded response suppresses the selected event and persists prevention evidence; wrapped ledger probe observed **2** ledger advances.
- Action source joins and duplicate envelope validation remain enforced.

## Conclusion

**PASS.** Prior blocking findings are addressed. Candidate/root files were not modified.

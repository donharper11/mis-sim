# Inventory integration review

Date: 2026-09-14. Author: `decision_inventory`; independently reviewed by supervisor.
Candidate: `0f08674848562cca6f232640e630de2d244ce429`; original base `c7283dc`.
**ACCEPT as preparation evidence only.** This does not pass a Heavy implementation-spec
gate, freeze an interface, or authorize a decision-transition builder.

The supervisor checked the relevant runner lock/write/advance/arrival/result paths,
snapshot/action reconstruction and the inventory's scope, then independently ran its
entire embedded SQLite probe at the inspected base using declared dependencies.
Observed outputs matched:

- Catalog: 14 items/42 modes; platform: 11 services/33 modes; 17 zero-lead-time modes total.
- A cost-1 unknown training target reaches action history while training stays unchanged.
- One initial estate yields 9 nodes in round 1 and zero in round 2.
- Repeated advance(2) refuses the duplicate result only after debt rows increase 1 to 3.
- Unlock(1) retains round-2 result and existing signal/debt history.
- Catching an unrelated scoring-input failure and committing can retain the already
  materialised arrival. This demonstrates caller-controlled partial state, not an
  automatic commit by the runner.

Log: `/tmp/mis-sim-decision-inventory-supervisor.log`. The document preserves the earlier
event-key-to-signal-key ruling and distinguishes absent contracts from source facts.
Only its new inventory file changed on the author branch; no code, formula, pack or
shared database changed. Headless in-memory probes are the appropriate evidence here;
no browser, platform-auth, transaction-safety or M1-completion claim is made.

The next Heavy authoring packet must define typed decisions and the atomic transition
boundary, including the inventory's D1–D10 decisions, before bounded estate/organisation
builders can start. All these gaps remain owned by M1/NS-004. The M0 scorecard correction
does not fix them; its numerical contract is separately reviewed and audited.

# P3 organisation packet DoD

This packet provides the pure `reduce_organisation` boundary. It derives training
retention and coverage, process fit and prices, scoped communication and resistance,
adoption, staffing/support, governance/primary assignments, strategy and policy state,
and the frozen non-policy preference alignments from the bound runtime pack and P1/P2
state. It emits typed organisation charge/effect records without persistence, accounting,
consequence, repair, service, database, or frontend code.

The focused test file covers training decay and bounds, process no-ops and rounding,
service-arrival shock exclusion, scoped communication, staff/support/governance/primary
rules, typed hiring-order carry-forward and wage joins, strategy and policy activity,
authored preference rows, and strict round errors.

Supervisor amendment: the exact correction allowlist is these four files:
`backend/app/simulation/organisation.py`, `backend/app/simulation/types.py`,
`backend/tests/test_simulation_organisation.py`, and this DoD. The single P1 type-file
change adds only `OrgDeltaV1.hiring_orders: dict[str, HiringOrderV1]` and
`OrgDeltaV1.staff_hires: list[StaffHireV1]`. This is required so hire ordering,
cancellation, arrival joins, and recurring wage entries remain authoritative at the
pure P3 boundary; no other P1 DTO or P1/P2 implementation was changed.

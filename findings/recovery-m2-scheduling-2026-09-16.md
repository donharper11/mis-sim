# M2.3 Round Scheduling Audit — 2026-09-16

**Candidate:** `d41edb34d098a090b2b958100b07ab9b77b4c099`  
**Dispatch basis:** `handoffs/recovery/m2-scheduling-amendment.md` and
`handoffs/recovery/m2-scheduling-dispatch.md` at `8cc3ff1`  
**Verdict:** **PASS WITH KNOWN LIMITATION**

The implementation stays within the allowlist and uses the production
`SimulationService` boundary after registered `RuntimePackV1` resolution and digest
verification. Participant snapshots are sourced from `simulation_run_v1` joined to
platform teams by instance scope. Schedule rows persist UTC timestamps and grace values;
participant foreign keys are composite and restrictive across instances.

The first candidate (`ca140d2`) was returned for two bounded issues: missing validation of
`lock_warning_minutes`, and a stale worker could call the production service after lease
reclamation. Successor `d41edb3` validates the setting and fences every lock/advance call
with the current claim token; lost claims fail deterministically without invoking the
production service. The post-call participant update and lease clear remain token-conditional.

Evidence:

- Scheduling tests: **7 passed**.
- Full gate on the successor: **682 passed**, 7 existing deprecation warnings, every
  repository guard green, fixture matrix green, and `make check: all guards green`.
- Migration evidence on the implementation candidate: SQLite upgrade → downgrade to
  `0007` → upgrade to head passed; schema inspection verified the instance-safe composite
  foreign keys and restrictive team deletion.
- Deterministic cohort scheduling evidence: two registry-bound instances each initialize
  production teams; one locks then advances after grace, the disabled instance locks and
  does not auto-advance.
- Static scheduling guard confirms no service clock reads, no legacy `RoundRunner` import,
  the fixed-time CLI boundary, and the unavailable historical BECSR source is documented.

No implementation files outside the dispatch allowlist were changed. The packet is accepted
for M2 with the following bounded risk: because `SimulationService` owns a separate
transaction and was explicitly out of scope, a theoretical TOCTOU window remains between
the scheduler's pre-call claim check and the external mutation if a lease expires at exactly
that point. The schedule-row write and lease clear remain token-fenced, and repeated service
operations are idempotent. Close this before internet-facing multi-worker scheduling or
when the M1 service boundary next permits an operation token. M3 remains the next product
milestone.

# Instructor pilot rehearsal and acceptance

**Scope clarification, 2026-10-07:** use these walkthroughs ourselves with seeded demo
instructor/student accounts to verify platform readiness. Participant recruitment and the
observed human acceptance record below belong to a later pilot and do not block readiness.
Keep seeded technical results distinct from actual human observations.

Prepared 2026-10-06. This is an acceptance script, not a record of observed acceptance.
Use a disposable cohort for technical rehearsals; use a separately prepared class for an
observed pilot. Current release blockers and ownership are in `../TODO.md`.

## Before inviting students

- Confirm the exact revision and working-tree state under review. Run the checks in
  `readiness-runbook.md`. Reconcile any failed or skipped checks.
- Confirm the chosen host, account provisioning method, roster/team membership, casepack
  version/digest, timezone, round deadlines, scheduler worker and instructor access.
- Demonstrate restoration from a backup on a separate database. Record restored row counts
  and immutable report identity; a successful dump alone is not proof of recovery.
- In Instructor Setup, bind the case, create teams and assign active demo students. Resolve
  all start-readiness reasons, explicitly choose each team's agreed initial strategy, and
  confirm Start simulation. Verify round1 and student access through the normal UI.
  Existing course/team records alone do not mean a playable game has been started.
- Provide `student-guide.md`, credentials and a route for reporting problems.

## Observed competent path

Ask a student team to sign in without developer intervention. Have them find the company
situation, declare a strategy, inspect costs and lead times, save application and rollout
choices, assign ownership, respond to a challenge, and explain Review's totals.

EXPECT: choices persist on reload; saves do not erase unrelated choices; capital and
ongoing cost evidence reconcile; no console/network errors, clipped controls or unexplained
technical messages. Ask students to describe what each control will do before advancing.

Have them lock, let the instructor advance, and ask them to locate the debrief and download
it. Repeat through six rounds with coherent decisions. Record why any result differs from
expectations; do not silently alter scoring constants to force a preferred outcome.

## Observed negligent path

Use a separate team. Let it prioritize purchases while leaving training, ownership or
signal responses unsupported. Do not rescue the team through hidden database edits.

EXPECT: low realised value is explained by the actual missing support and causal evidence.
Check whether students can identify the consequence and describe a defensible response.
A do-nothing automated smoke run does not replace this observed purchasing/negligence path.

## Instructor operations

Exercise setup/roster assignment, ownership refusal, pause/resume, lock/reopen, advance,
monitoring, grade derivation, a documented override, CSV export and section lifecycle.
Use disposable copies for reset/archive actions. Check every resulting state rather than
only the success message. Include another instructor and section to verify isolation.

## Acceptance record

| Field | Record during observation |
|---|---|
| Date, host, revision, casepack version/digest | Pending |
| Instructor observer (outside implementation loop) | Pending |
| Student participants and device/viewports | Pending |
| Competent path, rounds and report references | Pending |
| Negligent path and causal explanation | Pending |
| Setup → export workflow | Pending |
| Recovery rehearsal evidence | Pending |
| Issues: reproduction, impact, owner, retest evidence | Pending |
| Teaching usability and balance judgment | Pending |
| Accepted / accepted with bounded limits / returned | Pending |

Implementation agents may prepare and reproduce technical evidence. They must not fill
these rows as observed human acceptance without the actual participants and decision.

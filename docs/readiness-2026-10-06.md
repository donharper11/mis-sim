# October 6 readiness work and evidence

Date: 2026-10-06. Branch: `build/readiness-2026-10-06`; original HEAD `0a535ba`.
This is a builder verification report, **not an independent audit or production approval**.
Six tracked rollout/infrastructure files and untracked `CLAUDE.md`/sample screenshots were
already present; that work was preserved. No push, merge or production deployment performed.

## Completed changes

- Replaced stale README/battlecard headlines with dated implementation evidence and created
  an ordered `TODO.md`. Historical north-star and handoff narratives now point to it.
- Corrected seven ESLint errors. Instructor round statuses use the shared semantic badge.
- Corrected rollout metadata to use actual deployment-mode catalog prices and prefer
  concrete deployment host assignment over catalog fallback.
- Removed unsupported arbitrary rollout budget inputs that caused 422 responses. Saved
  choices now rehydrate from the scoped current sheet; per-application edits preserve other
  assets' training/process choices and other units' communication commands.
- Restored unreachable Security and People panels within Infrastructure; synchronized sheet
  revisions between sibling panels. Draft policies and ownership now rehydrate correctly;
  strategy and ownership saves preserve one another at the API boundary. People hiring
  retains existing rollout communication; policy saves retain pending application purchases.
- Platform detail from Rollout receives real platform data and remains read-only.
- Unassigned students no longer inherit the only team in a section through platform,
  rollout or persona lookup. Host-platform mutations now refuse uninitialized, paused,
  locked or completed runtimes; member lists refresh after mutation.
- Dashboard capital now uses the same current-round grant/spend reducers as Review through
  a lightweight, digest-checked read; completed games retain their closing balance.
- Bundled Barlow font weights and their OFL license locally. The external Google stylesheet
  stalled navigation in this environment; the visual font choice is preserved.
- Updated the PostgreSQL verifier from 28 to all 32 current models. Health returns HTTP 503
  for a database outage so an HTTP/container health probe cannot mistake it for readiness.
- Added a guarded fresh-cohort seed and a reusable browser proof, student guide, pilot
  acceptance script and operational runbook.

## Verification

| Check | Result and boundary |
|---|---|
| Initial full gate | 790 passed, 1 skipped, all guards green; 660.85s. The skipped PostgreSQL concurrency check was then run separately on its own disposable DB and passed. |
| Full gate after core fixes | 795 passed, no skips, 166 warnings; all guards green; 668.93s. Includes explicit disposable PostgreSQL concurrency. Log: `../findings/readiness-2026-10-06/full-check.log`. |
| Later controls correction | Five real browser checks passed after the full pytest run: rollout/ownership revision sync, mutual strategy/ownership preservation, People/hiring preserves communication, Security/People revision sync and draft persistence on reload. Fresh guard sweep and frontend lint/build also pass. Subsequently included in the reviewed full gate below. |
| Focused fixes | Rollout metadata/locked-host/unassigned-team checks and budget-read parity: 4 passed. Budget parity also proves the headline read does not call the expensive full quote. |
| Frontend | ESLint passes; production build passes. Existing ~1.1 MB JS bundle remains a separate optimization task. |
| PostgreSQL | Fresh migrations through `20261004_0011`, 32 application tables plus Alembic, six committed historical results. Log: `../findings/readiness-2026-10-06/postgres.log`. |
| Restore | Custom-format dump restored into another disposable DB; result query returned `6|1|6`. Source/restored ordered payload digests match (`f525251b1d9293bcc31a6f79095a5bb1`). |
| Fresh browser seed | New PostgreSQL DB: two sections, four round-one teams. A second invocation refuses the populated DB. |
| Browser | 17 checks passed: real student/staff login, eight student routes at 1440/1280/1024/720, two rollout saves/reload, capital parity, lock/read-only, instructor workspaces, six advances/debrief reads and report download. Zero console/page/network errors. |
| Host browser proof | Creation, immediate member response, read-only rollout platform detail, cross-instance refusal, locked rename and final 720px layout passed. |
| Independent audit | User-authorized fresh backend, frontend and contract reviewers dispatched. Backend corrections accepted after seed repair; all five frontend findings closed after independent re-review. Host-scope migration 0012 subsequently implemented and accepted by independent backend/browser audits plus the 816-test full gate. See review links below. |
| Production/observed pilot | Not run; host and human participants remain external dependencies. |

Controls evidence: `../findings/readiness-2026-10-06/controls-results.json`.
Browser result inventory: `../findings/readiness-2026-10-06/browser-results.json`.
Screenshots: `../screenshots/readiness-2026-10-06/`. Reproduction commands:
`readiness-runbook.md`. The full-game browser proof uses modest rollout edits and an otherwise
mostly empty sheet; it is not the separate competent/negligent pedagogical acceptance.

## Remaining higher-priority findings

The current generic tests do not establish complete host-platform correctness:

- **READY-001 — CLOSED:** migration 0012 and scoped APIs enforce member/parent and host/team
  instance integrity. Additive host guard and both independent audits pass; see
  [scope acceptance](host-scope-2026-10-06.md).
- **READY-002 — CLOSED:** activation/reset implementation passed independent backend/browser
  audits and the final 834-test gate; see [lifecycle evidence](host-lifecycle-2026-10-06.md).
- **READY-003 — instructor start:** course/team creation does not initialize playable
  runtime teams. The readiness seed is a demo-only workaround. Owner: instructor start packet.
- **READY-004 — operational performance:** repair-inclusive Review/advance calls are slow
  in this environment; the broad backend gate took about eleven minutes. A profiled fresh round-one full read took 17.212s versus 0.091s for the lightweight
  budget read during concurrent verification. `RuntimePackV1.__getattribute__` defensive
  deep copies dominated (16.806s cumulative); repair assessment took 16.095s. Profiling
  overhead and concurrent tests mean these are diagnosis, not capacity estimates. Owner: operational performance.

The concrete proposed next contract is
`../handoffs/readiness-2026-10-06/next-contract.md`. Resolve/review these before proceeding to
lower-priority teaching features or claiming class readiness. `TODO.md` owns the wider queue.

## Independent review follow-up

Fresh reviewers independently inspected source and ran their own probes; these are distinct
from the builder verification above:

- [Backend review](../findings/readiness-2026-10-06/backend-independent-review.md): bounded
  corrections accepted after fixing a reproduced SQLite seed writer lock. Fresh SQLite and
  PostgreSQL seeds now initialize all four teams and refuse reuse. Added
  `backend/tests/test_readiness_seed.py` to retain this regression (1 passed).
- [Frontend review](../findings/readiness-2026-10-06/frontend-independent-review.md): reproduced
  partial People selection losing communication, failed host component provisioning, successive
  service purchases losing earlier choices, and unhelpful stale-draft recovery. All five UI findings (including close-during-purchase timing) were corrected and
  independently closed. Configuration now comes from authored component choices; delayed
  refresh testing proves early Close cannot expose a stale policy snapshot. Original failing
  evidence is retained and the closure checker fails against the original results.
- [Contract review](../handoffs/readiness-2026-10-06/contract-independent-review.md): original
  umbrella proposal returned for missing decisions; the bounded
  [host-scope successor](../handoffs/readiness-2026-10-06/host-scope-contract.md) accepted
  for implementation. The successor has now been implemented and independently accepted; see `host-scope-2026-10-06.md`.

The backend reviewer also reproduced a preexisting SQLite archive migration gap
(READY-AUD-BE-002), owned by platform/migrations in TODO. Complete platform readiness remains
open despite acceptance of the bounded corrections. **Final reviewed-tree gate: 796 passed, no skips, 166 warnings, 691.57s; all guards green.**
This includes explicit PostgreSQL concurrency and the new seed regression. Final frontend
lint/build pass, with the existing bundle-size warning retained as an optimization item.
Logs: `../findings/readiness-2026-10-06/reviewed-full-check.log`, `reviewed-frontend-lint.log`
and `reviewed-frontend-build.log` in that directory. Final source hashes are recorded in
`reviewed-source-sha256.txt`; auditor hashes independently match the three final UI files.

No migration, merge, commit or deployment was performed during this independent-review pass.
Subsequent scope packet: migration 0012, independent backend/browser audits and full gate
**816 passed, no skips, all guards green**. See [scope evidence](host-scope-2026-10-06.md).
Subsequent lifecycle packet: migration0013, independent backend/browser audits and final
**834 passed, no skips, 226 warnings, 1208.74s; all guards green**. Fresh PostgreSQL verifier,
frontend lint/build and reviewed source hashes pass. See [lifecycle evidence](host-lifecycle-2026-10-06.md).
The next work is the independently accepted instructor-start contract, SQLite archive repair
and performance. User requested checkpoint commit/push and a pause; see
[the next-agent handoff](../handoffs/readiness-2026-10-06/NEXT-AGENT.md).

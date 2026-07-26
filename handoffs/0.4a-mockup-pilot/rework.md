# 0.4a — Rework Instruction (Phase 1)

**Drafted by:** the AUDITOR of `findings/0.4a-2026-07-26-audit.md` · **Date:** 2026-07-26
**Branch:** `build/0.4a-mockup-pilot` @ `407342d` · **Audit verdict:** FAIL at the Phase 1 gate

> **Status: PROVISIONAL.** This instruction is blocked on a spec amendment that has not been
> written. It opens with a gate that fails closed, so it is safe to hand to a builder early:
> a builder receiving it before the amendment lands will stop and report rather than
> improvise. Do not remove that gate to make the packet "ready".

**Who reworks.** Per `handoffs/README.md` *"Who fixes findings"* — by cause, not severity —
0.4a-001's cause is a spec gap, not a compromised mental model, so this goes to the **same
builder**, not a fresh one. Its context is an asset here. The builder ↔ auditor separation
still holds: the corrected branch returns to a **fresh auditor** before merge.

**What the auditor did not do.** Amend the spec, and answer S-1 … S-14 in the findings file.
Both are the author's under `GOVERNANCE.md §6`. An auditor that rewrites the spec it just
failed has quietly become that spec's author, which is the separation `§6.1` exists to
protect.

---

## Blocked on the author, before this packet is handed over

| # | Decision | Why a builder cannot take it |
|---|---|---|
| 1 | **Does spec §1 now permit editing `frontend/src/main.jsx` and `frontend/src/pages/DevTokens.jsx`?** | 0.4a-001 is unfixable either way without this. §5.1 retires the names those files read; §1 forbids editing them. `GOVERNANCE.md §4.4` forbids the builder resolving it |
| 2 | **What should `DevTokens.jsx` list after the fix?** The audit found all 113 declared tokens resolve, so a two-tier reference page (38 primitives + 75 roles, labelled) is available and would double as a working proof of the tier rule. A flat re-list of the 75 roles is also defensible | It is a design choice about a surface, not a mechanical repoint |
| 3 | **`.gitignore` negation, or widen the touch list?** `screenshots/0.4a/*.png` is blocked by `.gitignore:16`; 0.2 needed an explicit `!screenshots/0.2/*.png`. The DoD's permitted-files row omits `screenshots/` while another row in the same table demands nine files there, and `playthrough.md` F1 permits them | Finding 0.4a-004. Either route edits a file outside the spec's touch list |

Amendments land in the living document with a version bump, per `SPEC_PROTOCOL.md §8` —
not as a standalone delta file.

---

## Opening instruction for the REWORK BUILDER

Paste this. Do not paraphrase it.

```
You are the REWORK BUILDER for module 0.4a of the MIS Simulation.
Phase 1 landed and FAILED audit. You are fixing three findings. You are not
building Phase 2.

REPO: /home/ubuntu/projects/mis-sim   (origin: github.com/donharper11/mis-sim)
Work on branch build/0.4a-mockup-pilot, pushed at 407342d. Never push to main.

READ FIRST, IN FULL, BEFORE ANY OTHER ACTION:
  1. ~/projects/mis-sim/GOVERNANCE.md
  2. ~/projects/mis-sim/QUALITY_PROTOCOL.md
  3. ~/projects/mis-sim/CONTRACTS.md
  4. handoffs/0.4a-mockup-pilot/spec.md        (the AMENDED spec — see the gate)
  5. findings/0.4a-2026-07-26-audit.md         (your work list)

Treat every finding as a claim that carries its proof. Re-run the proof. An auditor
has been wrong before on this project — see SPEC_PROTOCOL.md §2.1.

GATE — CHECK BEFORE TOUCHING ANY FILE:
  0.4a-001 cannot be fixed under the spec as originally written. §5.1 requires
  retiring token names that frontend/src/main.jsx and frontend/src/pages/DevTokens.jsx
  read, while §1 forbids editing those two files. Both cannot hold.
  Confirm the amendment landed: read §1's out-of-scope list and the spec changelog.
  If §1 still forbids editing frontend/src outside styles/theme.css: STOP AND REPORT.
  Do not widen the scope on your own authority (GOVERNANCE §4.4).

YOUR SCOPE — these three findings, nothing else:
  0.4a-001  Blocking. Repoint the token consumers to semantic roles. The findings file
            proposes an eleven-token antd mapping that the auditor verified resolves to
            values identical to the old theme. Re-verify it in the browser; do not
            trust it. If the amendment does not say what DevTokens.jsx should now list,
            that is an open decision — STOP AND REPORT rather than choosing.
  0.4a-002  Functional. Either repoint --status-neutral-marker to --slate-500, or keep
            --slate-400 and correct the deprecation-table note to record a deliberate
            change. One or the other, not both, and say which you chose and why.
  0.4a-005  Report. CONTRACTS.md: the PROSPECTIVE marker and the "Last updated" header.

PREREQUISITE — 0.4a-004, before you produce any screenshot:
  screenshots/0.4a/*.png is blocked by .gitignore:16. Confirm with
  git check-ignore -v screenshots/0.4a/x.png. Fixing it means editing .gitignore,
  which is outside the spec's touch list. If the amendment does not cover it:
  STOP AND REPORT. Do not work around it with git add -f.

DO NOT:
  - add a back-compatibility alias block to theme.css. That re-creates finding
    0.2-003, which this module exists to resolve. It will fail audit again.
  - start Phase 2. No mockups, no HTML, no screenshots of screens that don't exist.
  - resolve S-1 … S-14 in the findings file. Those are the author's, and four of them
    block Phase 2 deliberately.
  - edit findings/0.4a-2026-07-26-audit.md. It is the audit record. If you think a
    finding is wrong, report that with evidence — do not amend the file.
  - touch dependencies. AR-001 in SECURITY.md covers the 8 high advisories.

BEFORE CLAIMING DONE — verify resulting state, not exit codes (QUALITY_PROTOCOL §1):
  1. Start the dev server. Open /_dev/tokens in a real browser.
     - antd primary button background is rgb(30, 64, 175), not rgb(0, 0, 0)
     - the antd table header is not black and its header text is legible
     - every swatch resolves to a value; zero blanks
     - zero console errors, zero failed network requests
  2. Assert no orphans remain: every token name referenced anywhere under frontend/src
     resolves non-empty in the browser. Paste the list and the result. This is the
     check Part A could not make — finding 0.4a-006.
  3. Re-run and paste output for I2 (one-hop resolution), I7 (no tokens declared
     outside theme.css), and the A4 count (89 rows, no orphans, no phantoms). Any
     theme.css edit can break all three.
  4. If you changed a token's value, re-run the value comparison for that row and
     show old value → new value.
  5. Screenshot at 1280 after the fix. Then prove it is tracked:
     git ls-files screenshots/0.4a/   — not the git add exit code.
  6. dod.md: correct the rows your fix touches and append a "Rework — 0.4a-001, -002,
     -005" section, one row per finding with evidence. Do not overwrite the Phase 1
     report.
  7. Push, then verify: git ls-remote origin build/0.4a-mockup-pilot against
     git rev-parse HEAD. Confirm the changed files are in the remote tree, not just
     that the ref moved.

Report every stop. A reported blocker costs an hour; an improvised architecture costs
a rebuild.

This branch returns to a FRESH AUDITOR before merge — not to me, and not to you.
```

---

## Why the instruction is shaped this way

Three deliberate choices, recorded so the next rework packet can copy them or reject them
knowingly.

**The gate fails closed.** The likeliest failure mode is a builder cheerfully "fixing"
0.4a-001 by editing files the spec still forbids — the silent scope resolution
`GOVERNANCE.md §4.4` is written against. A packet that merely *mentions* the conflict invites
that; one that opens with a check and a STOP does not.

**It names the specific proxy signals that failed**, rather than restating the ladder.
Phase 1's report was "npm ci && lint && build — PASS", all three true and all three blind to
a custom property resolving to `""`. The same class of error is waiting at `git add` for the
screenshots. Both are called out by name.

**It tells the builder to re-verify the auditor's proposed mapping rather than trust it.**
A finding arrives with no Pre-Flight Register in front of it, and the precedent on this
project is that the reviewer was the weakest link, not the builder —
`findings/0.2-2026-07-26-author-review.md`, Amendment 2.

---

## Protocol gap this exposed

`handoffs/README.md` carries verbatim opening instructions for **BUILDER** and **AUDITOR**,
and its folder layout lists `spec.md` · `playthrough.md` · `dod.md` · `notes.md`. It has no
slot for a rework packet, and no opening instruction for the return leg — it says only that
the module "returns to a builder with the findings file as its input."

That assumption holds when findings are actionable. It failed here: 0.4a-001 is unfixable by
any correctly-behaving builder until the spec changes, so the findings file alone would have
bought a wasted cycle and a stop.

**Suggested — author's call, not the auditor's:** add `rework.md` to the folder layout and a
third opening instruction to `handoffs/README.md`, with the fail-closed gate as its standing
first section. Filed here rather than applied, per `GOVERNANCE.md §6`.

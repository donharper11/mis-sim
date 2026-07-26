# Security — Accepted Risk Register

Dependency advisories that are **knowingly not fixed**, with the reasoning and the
condition that reopens them.

An accepted risk with no re-check trigger is not accepted, it is forgotten. Every row
carries one.

**Rule:** a builder never accepts a risk on its own authority. It reports; the risk is
recorded here by decision; the auditor checks this file rather than re-litigating.

---

## AR-001 · react-router RSC Mode CSRF Bypass

| | |
|---|---|
| **Advisory** | GHSA-qwww-vcr4-c8h2 · high |
| **Affects** | `react-router >=7.12.0 <8.3.0`, via `react-router-dom` |
| **Installed** | `react-router-dom@7.18.1` → `react-router@7.18.1` |
| **Accepted** | 2026-07-26 · module 0.2 |
| **Re-check** | Module 0.6 — the React 18 pin revisit |

### Why not fixed

**Every remediation path is blocked or worse.**

*Forward:* the fix lands in `react-router@8.3.0`, which declares
`peerDependencies: react >=19.2.7`. We are pinned to React 18 to match globalstrat's
design-system components (`handoffs/0.2-scaffold/spec.md §3` decision 4). No `8.x` of
`react-router-dom` is published.

*Backward:* downgrading is dramatically worse. Advisory counts across the 7.x line,
queried from npm's bulk advisory endpoint on 2026-07-26:

```
  7.11.0    14 advisories   (6 high)   XSS, SSR XSS, turbo-stream deserialization,
                                       DoS ×2, open redirect, CSRF …
  7.12.0    13 advisories   (6 high)
  7.13.2    10 advisories   (5 high)
  7.15.1     5 advisories   (2 high)
  7.18.1     1 advisory     (1 high)   ← installed. The cleanest release in 7.x
```

`7.18.1` is already the best available version. There is nowhere better to go inside the
constraint.

### Why the residual risk is acceptable

The advisory is specific to **RSC (React Server Components) mode**. This application is a
plain Vite SPA:

- no React Server Components
- no server actions
- no SSR
- the router handles client-side navigation only

The vulnerable code path is not reachable in this configuration.

### Re-check trigger

Reopen when **any** of these becomes true:

1. Module 0.6 establishes that globalstrat's components run under React 19 — the React 18
   pin drops, `react-router@8.3.0` becomes installable
2. A `react-router-dom@8.x` is published
3. A patched `7.x` appears (`>=7.19` outside the advisory range)
4. The application gains SSR, server actions, or RSC — at which point the risk is no
   longer theoretical and this row becomes **blocking**

### Not accepted

The `brace-expansion → minimatch → eslint / eslint-plugin-react` chain (~6 high) is
**dev-only**, not shipped to the browser, and fixing it requires `eslint@10` (breaking).
Deferred rather than accepted — revisit when eslint 10 is otherwise warranted.

---

## How to add a row

Only by decision, never by a builder acting alone. Required fields: advisory ID and
severity, affected range, installed version, why every remediation path is blocked or
worse (**with evidence**), why the residual risk is acceptable in this application's
configuration, and the trigger that reopens it.

If you cannot write the trigger, the risk is not understood well enough to accept.

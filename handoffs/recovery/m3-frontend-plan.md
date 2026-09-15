# M3 frontend delivery plan

Date: 2026-09-16  
Base: `0713729` (M2 lease race closed and pushed)

M3 is the first playable browser loop. It is delivered in dependency order:

1. **3.1 component library:** reusable token-bound controls and a browser gallery;
2. **3.2 shell:** authenticated sidebar/top bar/capital strip/countdown with real instance
   context;
3. **3.3–3.6 read and decision surfaces:** dashboard, platform, component workbench, and
   rollout controls;
4. **3.7 review and lock:** decision sheet, warning mirror, and scheduling lock;
5. **3.8 debrief:** computed business status report and downloadable output.

The M3 gate is a real student session that logs in, reads an estate, makes typed decisions,
locks them, advances six rounds through instructor control, and can explain the result. Static
mockups, fixture-only numbers, or a UI that bypasses the M1 `SimulationService` do not satisfy
that gate. M3 may add API seams as each screen needs them; it must preserve M2 auth, instance,
registry, and scheduling contracts.

## Packet boundaries

3.1 owns only reusable UI primitives and their gallery. 3.2 owns the authenticated shell and
the first live `/api/auth/me` plus instance read seam. Later packets own the domain screens and
typed decision mutations. No packet invents labels or score values: business copy comes from
the approved mockups/contracts, and data comes from the production API.

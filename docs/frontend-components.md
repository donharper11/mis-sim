# Frontend component library and workbench

Packet 3.1 exposes the reusable grammar at `/_dev/components`. It is a development gallery,
not a student route and contains no simulation data.

The components use semantic roles from `theme.css` only:

- `StatusBadge` accepts the four canonical status keys: `complete`, `partly-done`,
  `needs-attention`, and `not-started`.
- `OptionRow` implements selected, unselected, and disabled Pattern A choices.
- `OptionCard` implements selected, unselected, and disabled Pattern B choices.
- `DetailTable` makes open rows visible through first-cell link styling, hover highlight, and
  a trailing chevron.
- `SplitRule` keeps alternatives readable instead of merging them into prose.

The gallery is intentionally separate from the authenticated student shell. M3.2 composes
these primitives into the live shell; M3.5 composes them into the Components workbench.

## M3.5 runtime workbench

M3.5 adds the Components route at `/components` and the scoped runtime endpoint
`GET /api/instances/{instance_id}/components`. The workbench reads catalog assets,
pending projects, and rollout records from the versioned checkpoint; legacy estate and
deployment rows are used only as a read fallback. Student-visible names come from the
registered casepack label map when one is available.

The detail view keeps deployment, rollout, data, connections, and lifecycle information
inside the selected asset. The add-component wizard builds a `buy_application` command
from registered catalog, placement, and configuration choices. Lifecycle retirement builds
`retire_asset`. Both are sent through `SheetPatchV1` and `SimulationService.patch_sheet`
with the current revision, so locked, uninitialized, unavailable, unaffordable, and stale
edits remain explicit runtime outcomes rather than local UI state.

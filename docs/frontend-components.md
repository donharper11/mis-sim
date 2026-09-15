# Frontend component library

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

The gallery is intentionally separate from the authenticated student shell. Packet 3.2 will
compose these primitives into the live sidebar, top bar, capital strip, and countdown.

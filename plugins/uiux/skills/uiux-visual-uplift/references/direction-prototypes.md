# Direction Prototypes

The step that turns words into a look. Two or three directions, rendered on the app's own key screens, measured, and shown side by side so the PM chooses between things they can see.

## What to build

```
design/directions/
  a-swiss-dense/
    tokens.css            # semantic remap of the existing tokens + additions
    P1-deck-list.html     # key place 1: default state
    P1-deck-list.empty.html
    P3-deck-detail.html   # key place 2: the densest screen
    NOTES.md              # Design Read, signature, what differs from the other directions
  b-editorial-calm/
    ...
```

- **Places:** the main place of the most important job, plus the densest or most complex place. Two places show whether a direction holds across screens; one doesn't.
- **States:** default plus the most telling other state (empty for a list, error for a form, loading for anything slow).
- **Content:** real content from the running app (copy a page's data or seed data), realistic lengths, realistic counts. Lorem ipsum hides every density problem.
- **Affordances:** every `U#` of the place from the breadboard is present; the prototype changes how things look and are arranged, not what the user can do.
- **Mobile:** each place also works at 375px (same HTML, responsive CSS).

## How to build

- One self-contained HTML file per place and state. Inline CSS or a shared `tokens.css` plus a small `base.css` per direction. No build step, no framework, no external requests except fonts the product can actually ship.
- All values through CSS custom properties named exactly like the existing tokens (`--surface-page`, `--text-muted`); new tokens get names that follow `../../uiux-design-system/references/token-architecture.md`. A raw value in a prototype is a missing token.
- Components mimic the chosen component library's structure (same parts and variants), themed. A direction that needs components the library can't express is costed in `NOTES.md`.
- Mark each affordance with `data-ux="U4"` so screen specs and reviews can point at it.

## Make the directions differ in what matters

| Lever | Example contrast |
|-|-|
| Density | 32px rows with hairline rules vs. 56px rows on cards |
| Type | one grotesque in 3 weights vs. serif headings with sans body |
| Surface strategy | flat with rules vs. layered elevation |
| Accent use | accent only on the primary action vs. accent carries navigation and selection |
| Signature | status language vs. numeric display face vs. timeline visual |
| Shape | 2px radius vs. 12px radius |

Three hues of the same layout are one direction. Keep one direction close to the current product ("evolved") so the PM sees the cost of not going further.

## Measure each direction

Point a review config at the files (no server needed):

```yaml
# design/directions/review.config.yaml
base_url: file:///abs/path/to/design/directions/a-swiss-dense
places:
  - { id: P1-deck-list, path: /P1-deck-list.html, states: [{ id: default }] }
  - { id: P3-deck-detail, path: /P3-deck-detail.html }
tokens: { source: css, prefixes: ["--surface-", "--text-", "--border-", "--color-", "--radius-", "--font-size-"] }
viewports: [{ id: mobile, size: [375, 812] }, { id: desktop, size: [1440, 900] }]
```

Run `review.mjs run --label dir-a` per direction (change `base_url`). A direction must pass the measured gate before it is shown: off-token values 0, axe serious 0, no horizontal scroll at 375px. Then score each on the vision rubric and compare directions pairwise (`review.mjs compare dir-a dir-b` gives side-by-side sheets).

## Present

- Side by side, same place, same state, same width: one sheet per place with all directions (`compare` sheets, or an artifact page with the screenshots when the session can publish one).
- Per direction: Design Read, signature, the bet, the risk, the vision scores, one line on implementation cost.
- Your recommendation with the reason from the brief, first. Then ask: pick one, merge ("A's density with B's type"), or redo with a different lever. At most two rounds; then narrow to one and refine.
- Record the decision and the rejected directions with reasons in `design/UPLIFT.md`.

## After the choice

The chosen direction's prototypes become `design/targets/<place>.html`, the targets `design-parity` compares the implementation against. Remaining key places get prototypes in the locked direction during Step 5.

# Screen Spec

One file per breadboard place: `design/screens/<P#-name>.md`. It adds the visual layer to the breadboard; it never changes behaviour. If the visual design needs a behavioural change (a new affordance, a different place split), raise it in the journey spec's STATUS.md instead.

The coding agent reads `DESIGN.md`, then this file, then the breadboard. Every value is a token or a component variant; a raw value here is a defect.

## Template

```markdown
# P2 Deck list (J1.1 to J1.3)

Target: design/targets/P2-deck-list.html   Direction: DESIGN.md › Art Direction

## Job of this screen
<one line from the job story: what the user came to do here>

## Layout
- Pattern: table-first list with a filter bar; detail opens in a right drawer (P3)
- Grid: content max 1200px; 12 columns desktop, 1 column below 768px
- Regions, top to bottom: page header (title, count, primary action) · filter bar · table · pagination

## Hierarchy
1. First: the table rows (company name, stage, score)
2. Second: the primary action "Upload deck" (U4)
3. Third: filters (U5 to U7), counts, pagination
Quiet: row actions appear on row hover and focus

## Affordances
| U# | Element | Component / variant | Notes |
|-|-|-|-|
| U4 | Upload deck | Button / primary / md | The only primary on the screen |
| U5 | Stage filter | Select / ghost / sm | Shows active filter count |
| U8 | Row | Table row / interactive | Whole row is the target; 40px height; name `--text-heading` |
| U9 | Score | Badge / status | Signature status language; colour + label |

## States
| State (breadboard) | What the user sees | Components | Copy |
|-|-|-|-|
| default | ... | | |
| loading | Skeleton rows with final heights; header and filters live | Skeleton / row x8 | none |
| empty (first use) | Illustration-free empty state in the table area: what this list is for, primary action repeated | EmptyState / first-use | "No decks yet. Upload a pitch deck to get a first read." |
| empty (filtered) | Inline message under filters, "Clear filters" | EmptyState / filtered | "No decks match these filters." |
| error | Inline banner above the table, table keeps last data if any | Alert / error | "Couldn't load decks. Retry" |

## Responsive
- < 768px: table becomes a list of rows (name, stage, score); filters collapse into a "Filter" button with a sheet; primary action stays in the header

## Motion
- Drawer: slide from right, 200ms, standard easing; reduced motion: fade
- Row hover: background change only, no motion

## Copy
- Verbs: Upload → Uploading → Uploaded
```

## Rules

- Hierarchy lists exactly one "first". Two firsts means the screen has two jobs: split it or demote one.
- Every state in the breadboard's States table appears, with copy. "Same as default" is allowed only when true.
- Copy follows the voice in `DESIGN.md`; error copy says what happened and the next action.
- Component variants must exist in the library or in the design system's inventory; a new variant is listed under "New variants" at the end with its token bindings.
- Responsive notes describe re-composition, not just "stacks".

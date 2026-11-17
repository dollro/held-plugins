# Product UI Craft

What separates a productive system from an MVP is mostly here: dense information that still reads calmly, states that are designed, and feedback that makes the system feel fast and trustworthy.

## Tables and lists

- Tables for comparing records across attributes; lists for scanning one attribute (name) with secondary detail; cards only for heterogeneous objects or visual content.
- Row height by density: 32 to 36px dense, 40 to 48px default, 56px+ only with two-line rows.
- Left-align text, right-align numbers, tabular numerals, units in the header not in each cell.
- Hairline row dividers or zebra, not both; no vertical rules unless columns are many and narrow.
- Sticky header and first column for wide tables; horizontal scroll inside the table container, never the page.
- Row actions: whole row clickable to the detail; secondary actions on hover and focus (always reachable by keyboard), destructive ones in an overflow menu.
- Selection and bulk actions: a bar that replaces the table header while rows are selected.
- Truncate long text with an ellipsis and full text on hover/focus; never truncate numbers.

## Forms

- One column. Labels above fields. Group related fields (≤ ~4 per group) with a group heading.
- Field width hints at the expected input length.
- Validate on blur, not on every keystroke; show the error under the field with what to do; keep the user's input.
- Required is the default; mark optional fields instead.
- Primary action bottom-left aligned with the fields (or sticky footer in long forms); secondary as a text or ghost button next to it.
- Long forms: save drafts automatically; show "Saved" quietly.

## Dashboards and overviews

- Start from the question the user brings ("What needs my attention today?") and answer it first, big; supporting numbers smaller.
- Each number with context: comparison, trend or target. A number alone is decoration.
- Charts: follow the `dataviz` guidance if available; one idea per chart, direct labels over legends.
- Fewer, ranked panels beat a grid of equal tiles.

## Navigation and layout shell

- One primary navigation: a sidebar for 5+ sections or deep apps, a top bar for few sections. ≤ ~5 top-level items visible; group the rest.
- Current location always visible (active nav item and page title).
- Page header pattern, identical on every page: title, context (count, status), primary action at the right.
- Command palette (⌘K) for expert tools with many objects.
- Content max width for reading screens; full width for tables and boards.

## States

| State | Design |
|-|-|
| First use (empty) | What this place is for, the one action that fills it, optional sample data |
| Empty after filter/search | Say why it is empty, offer "Clear filters" |
| Loading < 300ms | Nothing (avoid flashes) |
| Loading 300ms to 3s | Skeleton with final dimensions; keep header and navigation live |
| Loading > 3s | Progress with an estimate; let the user leave and come back |
| Partial | Show what loaded, mark what didn't, retry per part |
| Error (recoverable) | Inline at the source, what happened, retry; keep user input |
| Error (blocking) | Page-level, plain language, a way back |
| Offline | Banner, queue actions if the app can, say what still works |
| Success | Confirm where the user looks (inline, the changed row highlights briefly); toasts only for background completion |
| No permission | Say who can grant it |

## Feedback and perceived speed

- Respond within 100ms to every click (pressed state, optimistic update or spinner inside the button).
- Optimistic updates for reversible, likely-to-succeed actions (toggle, rename, reorder) with rollback on error.
- Undo instead of confirmation dialogs for reversible destructive actions; confirm only the irreversible, naming the object ("Delete 'Acme seed deck'?").
- Keep layout stable: reserve space for async content, images with dimensions, no late-appearing banners above content.
- Disable a submit button only while submitting, never as validation.

## AI surfaces

- Streamed answers render progressively in final typography; show a stop control while streaming.
- Show sources inline next to claims, not in a footer list.
- Separate generated content from user content visually (surface or label), consistently across the app.
- Show uncertainty in words or a calibrated indicator only if it is real; never decorative confidence bars.
- Every generated result is editable or regenerable; keep the previous version reachable.
- Long-running agent work: a task row with status, elapsed time and what it is doing now; notify on completion; never a modal spinner.
- Empty prompt states suggest 2 to 4 concrete starters from the user's own data.

## Content and copy

- Sentence case for labels and headings.
- Button labels are verbs with objects ("Upload deck", not "OK").
- Numbers and dates in the user's locale; relative dates for recent items, absolute on hover.
- Microcopy states the consequence ("Archived decks are hidden from the list. You can restore them.").

## Detail

- Optical alignment: icons with text align to the text's cap height, not the box.
- One icon family, one stroke width, one size per context (16 inline, 20 in buttons, 24 in navigation).
- Focus ring 2px outside, `--border-focus`, on every interactive element.
- Hover adds, never moves (no layout shift on hover).
- Avatars, logos and thumbnails with fixed aspect ratios and fallbacks.

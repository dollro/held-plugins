---
name: uiux-visual-review
description: "Automated look-and-feel review of a running web app: walks every place and state from the journey-spec breadboard at several viewports and colour schemes, measures what can be measured (off-token colours and sizes, spacing off the grid, alignment near-misses, type and colour sprawl, primary actions per view, axe WCAG 2.2, target sizes, overflow, keyboard focus, motion, layout shift), then scores the screenshots against a calibrated vision rubric (hierarchy, density, consistency, distinctiveness, state quality, polish). Produces a ranked uplift list, before/after comparisons and a CI gate with a baseline ratchet. Use for \"review the UI\", \"how good does our app look\", \"UX audit\", \"visual QA\", \"is the redesign better\", \"look and feel check\", or as the audit step of uiux-visual-uplift. Not for matching a given mockup (design-parity) or functional tests."
---

# Visual Review

Functional tests prove a screen works. This skill checks whether it looks and feels like a finished product, in two layers:

1. **Measured layer** (`scripts/review.mjs`): numbers from the rendered DOM. Deterministic, cheap, CI-able. Catches drift, sloppiness and accessibility gaps.
2. **Vision layer** (you, with `references/vision-rubric.md`): screenshots and contact sheets scored against the locked art direction. Catches weak hierarchy, clutter, inconsistency, generic look, undesigned states.

Neither layer replaces the PM's judgement on taste. The skill ends with a ranked list and a gate the PM signs off; it never declares a UI "beautiful" on its own.

## When to use which skill

| Question | Skill |
|-|-|
| Does the build match this mockup / prototype? | `design-parity` |
| How good is this UI, where does it fall short, did it get better? | this skill |
| What should it look like in the first place? | `uiux-visual-uplift` (calls this skill for its audit and gate) |

## Prerequisites

- A running app reachable at `base_url` (never start servers yourself; ask).
- Node 20+. Once per machine: `npm install` in `scripts/`, then `npx playwright install chromium`.
- `review.config.yaml` in the app repo. `node <skill>/scripts/review.mjs init` scaffolds it from `references/review.config.example.yaml`. Auth uses the same block as design-parity (`form | cookie | storage-state | none`).
- Places and states: take them from `specs/ux/breadboards/<flow>.md` (one place per `P#`, one state per row of its States table). No breadboard: list the app's routes and ask the PM which 3 to 6 matter most. Never guess routes silently.

Call the script as `node <path-to-this-skill>/scripts/review.mjs <command>` from the folder holding `review.config.yaml`.

## Workflow

### 1. Configure (once per app)

- Map breadboard places to `places:`; states via `mock:` (fake API responses: empty list, 500, `hang: true` for loading), `offline: true`, and `steps:` (click, fill, upload, press, hover, wait_for) to reach dialogs and validation errors.
- Dialogs and drawers: set `scope:` to the dialog selector so metrics measure the dialog, not the page behind it.
- `tokens:` `css` with `prefixes` that match your design tokens (exclude framework palettes such as Tailwind's default colours, or every Tailwind colour counts as "on token"); or `dtcg` with the token files.
- `primary_action:` selector for the one main action per view, if the component library marks it (e.g. `[data-variant=primary]`). Without it a heuristic counts saturated filled buttons.
- Add `dark` to `schemes` if the app has a dark mode, and how it switches (`dark_mode`).

### 2. Run the measured layer

```bash
node review.mjs run --label mvp-2026-11      # all places x states x viewports x schemes
node review.mjs run --place P2-upload --state error   # one slice while fixing
```

Output in `.uireview/runs/<label>/`: `report.md` (gate, numbers per capture, findings with example elements), `metrics.json`, screenshots per `place/state/viewport-scheme.png`, focus frames, and contact sheets in `sheets/`:
- `places-<viewport>-<scheme>.png`: every place side by side, the consistency check
- `states-<place>.png`: all states of one place
- `viewports-<place>.png`: mobile, tablet, desktop of one place
- `focus-<place>.png`: each tab stop with its focus indicator, in tab order

Read `report.md` first. `references/metrics.md` explains each number, its usual cause and fix, and its known false positives.

### 3. Run the vision layer

Follow `references/vision-rubric.md`. Order matters:
1. Read `DESIGN.md` (Overview and Art Direction) first: the rubric scores against the intended direction, not general taste. No direction yet: score against the generic product-UI anchors and say so.
2. Contact sheets before single screens: `places-*` (same product?), then `states-*` (are empty, error and loading designed or left over?), `viewports-*`, `focus-*`.
3. Single screenshots for the details the sheets hide.
4. Score each place on the eight axes with the anchors. Every score below 3 names the element, the problem and the fix.

Write `review.md` next to `report.md` using the template at the end of the rubric.

### 4. Rank and hand over

Merge measured findings and vision findings into one ranked list in `review.md`:
1. Broken: failed captures, horizontal scroll, axe serious/critical, missing focus, undesigned error or empty states.
2. Systemic: off-token colours and sizes, type sprawl, inconsistent places. One token or component fix repairs many screens; these give the most visible improvement per hour.
3. Per-screen hierarchy and density.
4. Polish: alignment near-misses, spacing off grid, motion.

Each item: what, where (capture and element), why it matters for the user, the fix (token, component or CSS change), and the measured number that will prove it fixed. Group items by component or token where one change fixes several.

### 5. Compare and gate

```bash
node review.mjs compare mvp-2026-11 uplift-v1   # metric deltas + side-by-side sheets
node review.mjs baseline mvp-2026-11            # writes review.baseline.json (commit it)
node review.mjs check                           # exit 1 on failure: use in CI
```

- **Pairwise review:** after `compare`, read the side-by-side sheets in `.uireview/compare/<a>__<b>/` and judge per axis "better, same, worse, and why" (rubric section "Pairwise"). This is far more reliable than two absolute scores.
- **Ratchet:** with `review.baseline.json` committed, each limit becomes max(threshold, baseline value). An MVP far from the thresholds can gate CI from day one: no regressions, and every improvement can be locked in by re-running `baseline`.
- A metric that moves the "wrong" way can be a real improvement (a 20px target growing to 32px moves from `targets_below_24` to `targets_below_44`). Read the regression list; don't react to totals alone.

## Rules

- Never start or stop the app; never edit app code from this skill unless the user asks for fixes. The review is evidence; fixes are a separate step (`fullstack-engineer`, the Vue and Tailwind skills, or design-parity's loop once targets exist).
- Numbers are evidence, not verdicts. Threshold failures from `ignore`-worthy third-party widgets get an `ignore:` entry with a reason, not a silent skip.
- LCP from a dev server is relative only; compare runs, never quote it as production speed.
- Don't score taste without the direction. If `DESIGN.md` has no Overview with personality and audience, say that the distinctiveness score is provisional.
- Report counts, not percentages, for the vision findings (they come from one reviewer, not a sample).
- `.uireview/` holds screenshots and is git-ignored by `init`; commit `review.config.yaml` and `review.baseline.json` only.

## References

| Read | When |
|-|-|
| `references/review.config.example.yaml` | Writing or extending the config: places, states, mocks, steps, tokens, dark mode, thresholds |
| `references/metrics.md` | Interpreting a number in `report.md`, its fix, false positives, threshold tuning |
| `references/vision-rubric.md` | The vision pass: axes and anchors, contact-sheet protocol, pairwise comparison, `review.md` template |
| `../uiux-visual-uplift/references/reflex-defaults.md` | Scoring distinctiveness: the patterns that make a UI look generic |
| `../uiux-design-system/references/accessibility.md` | Fixing axe findings, focus, target size |

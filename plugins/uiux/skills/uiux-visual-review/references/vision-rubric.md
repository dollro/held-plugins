# Vision Rubric

The vision layer judges what numbers can't: hierarchy, density, consistency, character, state quality. A model judging taste drifts toward "looks fine" and toward its own defaults. Four rules keep it honest:

1. **Anchor to the direction.** Read `DESIGN.md` (Overview, Art Direction, Do's and Don'ts) before looking at any screenshot. Score against what this product is meant to feel like.
2. **Anchors, not vibes.** Use the 0 to 4 anchors below. A 4 is rare. Most real screens land at 2 or 3.
3. **Evidence per score.** Every score names what you saw (element, place, state). Scores below 3 also name the fix.
4. **Compare, don't rate, when you can.** Pairwise ("B is better than A on hierarchy because…") beats absolute scores. Use it for before/after and between directions.

## Protocol

1. **Consistency sheet** (`sheets/places-<widest>-<scheme>.png`): could these be screens of one product? Look for different header heights, button styles, card treatments, type sizes for the same role, spacing per page.
2. **States sheet per place** (`sheets/states-<place>.png`): is each non-default state designed? An empty state explains and offers the next action; an error says what happened and how to recover, in the user's words; loading keeps the layout (skeleton with final dimensions) rather than a lone spinner on white.
3. **Viewport sheet** (`sheets/viewports-<place>.png`): does mobile re-compose (stack, collapse navigation, keep the primary action reachable) or just shrink?
4. **Focus sheet** (`sheets/focus-<place>.png`): is every stop visibly focused, in a logical order?
5. **Single screens** at full resolution for hierarchy, alignment, copy and polish.
6. Dark mode, if present: re-check contrast hierarchy, elevation (dark surfaces lighten with elevation) and saturated colours (often too loud on dark).

## Axes and anchors

Score each place (default state, widest viewport) 0 to 4; add state quality from the states sheet.

**1. Hierarchy and focus.** One focal point per view; the eye path follows the job.
- 0: everything shouts; no entry point.
- 2: a heading and a primary action exist, but secondary content competes (same weight, same colour).
- 4: the user's next step is obvious within a second; secondary actions visibly subordinate; size, weight and colour each do one job.

**2. Density and rhythm.** Density fits the usage (daily expert tool vs. occasional visitor); spacing groups related things.
- 0: cramped or floating; spacing random.
- 2: consistent spacing, but grouping is unclear (equal gaps everywhere) or density mismatches the audience.
- 4: proximity shows structure; dense where scanning matters, calm where deciding matters.

**3. Typography.** Scale, roles, measure, numerals.
- 0: many sizes, no roles; long lines; mixed families without reason.
- 2: a scale exists but roles blur (labels and body look alike, headings too close in size).
- 4: clear roles; 65 to 75 character body measure; tabular numerals in data; headings balanced.

**4. Colour and surface.** Colour carries meaning; surfaces build depth.
- 0: colour decorative or random; status by colour alone; low contrast.
- 2: palette coherent but the accent is overused, or surfaces flat where hierarchy needs layers.
- 4: neutrals carry the screen, accent marks the one action and the current state, status colours paired with icon or text.

**5. Consistency.** Same role, same look, across places and states.
- 0: each page looks designed separately.
- 2: shared components, but variants drift (three button styles, two card treatments).
- 4: placed side by side, every screen reads as the same product.

**6. Distinctiveness.** Has character fitting the brief, without decoration for its own sake. Check `../../uiux-visual-uplift/references/reflex-defaults.md`.
- 0: unstyled framework defaults or template look.
- 2: tidy but generic; nothing a user would remember; reflex defaults present.
- 4: a recognisable signature in one place, everything else quiet and disciplined; nobody would mistake it for a template.

**7. State quality.** Empty, loading, error, partial, success are designed.
- 0: blank screens, raw error text, endless spinners.
- 2: states exist but are generic ("No data", "Error") or break the layout.
- 4: each state keeps the layout, explains itself in user language and offers the next action; success is confirmed where the user looks.

**8. Polish and motion.** Alignment, optical details, icon consistency, motion with a reason.
- 0: misalignments, mixed icon sets, jumpy loading.
- 2: mostly aligned; a few near-misses; motion absent or generic.
- 4: pixel-tight; one icon family; motion explains change (where it came from, where it went) and respects reduced motion.

Total per place: max 32. Report the axes, not just the total.

## Pairwise

For two captures of the same place and state (before/after, or two directions): per axis, one of `better / same / worse` and one sentence of evidence. Then an overall verdict and the single biggest remaining gap. If you can't tell the difference on an axis, write `same`; don't invent one.

## Calibration traps

- **Familiarity bias:** a clean framework default (Tailwind UI, Material, shadcn untouched) looks "fine" because it is common. Fine is a 2 on distinctiveness.
- **Screenshot bias:** dense data tables look busy in a screenshot and work well in use. Judge density against the job in the journey spec, not against a landing page.
- **Decoration bias:** gradients, glass and glow raise first impressions and lower clarity. Score them against the direction.
- **Content bias:** realistic data changes everything. Flag captures with lorem ipsum or two-row lists as "not representative" and ask for seed data.

## review.md template

```markdown
# Visual review: <label>  (<date>, direction: <DESIGN.md direction or "none yet">)

## Verdict
<3 lines: overall state, the systemic problem, the biggest win available>

## Scores
| Place | Hier. | Density | Type | Colour | Consist. | Distinct. | States | Polish | Total |

## Ranked findings
| # | Severity | Where (capture, element) | Problem (user impact) | Fix (token/component/CSS) | Proof (metric or sheet) |

## Systemic fixes (one change, many screens)
- <token or component> → fixes #3, #7, #12

## Not representative
- <captures with placeholder data or missing states>

## Open questions for the PM
- <taste calls the rubric can't settle>
```

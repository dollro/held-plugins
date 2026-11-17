---
name: uiux-visual-uplift
description: "Art direction for a product UI: takes a working MVP (or a journey spec) plus a rough design system and turns it into a distinctive, consistent, production-grade interface. Audits the current screens, commits to one aesthetic direction with a signature, renders 2 to 3 competing directions as HTML prototypes of real screens with real tokens and states, locks the chosen one into the design system and DESIGN.md, writes per-screen visual specs bound to the breadboard, and gates the result with measured and scored review before handoff to coding agents. Use for \"make our MVP look great\", \"visual redesign\", \"UI uplift\", \"art direction\", \"it works but looks generic\", \"from prototype to product\", \"give the app a visual identity\". Not for functional flows (uiux-journey-spec), token architecture alone (uiux-design-system), or matching an existing mockup (design-parity)."
---

# Visual Uplift

`uiux-journey-spec` says what the user does; `uiux-design-system` gives the token structure. This skill decides what the product should **feel like**, proves it visually on real screens, and locks it so every screen and every coding agent follows it.

## Principles

1. **Direction before pixels.** One committed direction with a reason from the brief beats an average of safe choices. If you would give the same look to any similar product, it is a default: change it (counterfactual test).
2. **Spend boldness in one place.** One signature element the product is remembered by; everything around it quiet and disciplined.
3. **Show, don't describe.** Directions are judged as rendered prototypes of the app's own screens, with its real content and states, side by side. Never as mood words alone.
4. **Evolve, don't replace.** An existing design system is remapped at the semantic tier (same token names, new values and additions). Component names, breadboard IDs and functional behaviour stay.
5. **Variation within identity, never between.** Screens differ in composition, never in palette, type, radius, motion or voice. "Every screen must read as the same product if placed side by side."
6. **The PM decides taste.** You propose, render, measure and argue. The PM chooses the direction and signs off the gate.

## Modes

- **uplift** (default): a running MVP exists. Start with the audit (Step 1).
- **greenfield**: no app yet, only a journey spec. Skip Step 1; prototypes are built from the breadboards.
- **extend**: a direction is already locked in `DESIGN.md`. Read it, skip Steps 2 to 4, spec new places in it (Step 5) and flag anything the brief forces outside it.

## Files

`DESIGN.md` (repo root) and the DTCG tokens are the source of truth after Step 4. Working files live in `design/`:

| File | Content |
|-|-|
| `design/UPLIFT.md` | Mode, step, decisions with dates, rejected directions and why, open questions. Resume from here |
| `design/audit/` | Visual review of the MVP (from `uiux-visual-review`) |
| `design/inspiration/<site>/` | DNA extractions (`review.mjs dna`) |
| `design/directions/<direction>/` | One folder per direction: `tokens.css`, `<place>.html` prototypes |
| `design/targets/<place>.html` | Prototypes of the chosen direction: targets for `design-parity` |
| `design/screens/<place>.md` | Visual spec per place, bound to breadboard IDs |

## Workflow

### Step 0: Read, then ask little

Read silently: `DESIGN.md`, token files, component library in use, `specs/ux/` (jobs, journey, breadboards, STATUS), the frontend's routes and layout shell, `design/UPLIFT.md` if resuming. Then ask at most three questions, one at a time, AskUserQuestion with options where possible:
1. Who uses it and how often (daily expert tool, weekly check-in, occasional visitor)? This sets density.
2. Three words it should feel like, and one thing it must not feel like.
3. Reference products or sites admired (1 to 4 URLs), optional.

### Step 1: Audit the MVP (uplift mode)

Run `uiux-visual-review` on the running app: measured layer plus vision rubric, scored without a direction (provisional distinctiveness). Copy `report.md`, `review.md` and the contact sheets to `design/audit/`. Commit `review.baseline.json` so nothing regresses during the uplift. Summarise for the PM in 5 lines: what works, the systemic problems, the biggest win.

### Step 2: Art direction

Follow `references/art-direction.md`:
- **Design Read**: one line, the feeling plus the bet ("Calm, exact, fast to scan: trust through precision, not decoration").
- **Register**: `product` (design serves a task) or `brand` (design is the product). Product UIs are almost always `product`.
- **Direction**: one from the menu, justified from the brief and the audit; run the counterfactual test.
- **Signature**: the one element the product is remembered by.
- **Dials** (1 to 10): variance from convention, motion, density.
- **Inspiration**: for each URL run `node ../uiux-visual-review/scripts/review.mjs dna <url> --out design/inspiration/<site>` and write took/rejected per `references/inspiration-intake.md`.
- Check against `references/reflex-defaults.md`.

Write it to `design/UPLIFT.md`. Gate: PM confirms the brief (not yet the look).

### Step 3: Diverge: 2 to 3 directions on real screens

Follow `references/direction-prototypes.md`. Pick 2 key places: the main place of the most important job and the densest or most complex one. For each direction:
- a `tokens.css` that remaps the existing semantic tokens (and adds missing ones), nothing else global;
- the 2 places as static HTML with real content from the app, every breadboard affordance present, default plus one non-default state, and one mobile width.

Directions must differ in what matters (type pairing, density, surface strategy, accent use, signature), not in hue alone. Measure each with `review.mjs run` against the prototype files, then show the PM the sheets side by side (contact sheet, or an artifact page when available) with a recommendation and its reason. The PM picks, or asks for a merge ("A's type with B's density"); iterate at most twice before narrowing.

### Step 4: Converge and lock

- Tokens: write the chosen direction into the DTCG files at the semantic and mapped tiers (`uiux-design-system`: `token-architecture.md`, `theming-multi-brand.md`); regenerate CSS/Tailwind.
- `DESIGN.md`: Overview gets the Design Read, audience, density and what it is not; a `## Art Direction` section gets register, direction, signature, dials, inspiration (took/rejected) and the lock sentence (`../uiux-design-system/references/design-md.md`). Do's and Don'ts get the reflex defaults this product rejects.
- Component library: if none is chosen or the current one fights the direction, decide with `../uiux-design-system/references/component-library-choice.md`. Theme it with the tokens; never re-implement its components.
- Record rejected directions and why in `design/UPLIFT.md`.

### Step 5: Screen specs

For each breadboard place in job priority, write `design/screens/<place>.md` per `references/screen-spec.md`: layout pattern, hierarchy (what the eye sees first, second, third), component and variant per affordance (`U#`), every state from the breadboard's States table, responsive behaviour, motion, copy. Apply `references/product-ui-craft.md` for tables, forms, dashboards, empty and loading states, AI surfaces. Places that carry the job get an HTML prototype in `design/targets/`; repetitive places only a spec.

### Step 6: Pre-flight gate

Run `references/preflight.md`: the measured gate on the prototypes (`review.mjs run` + `check`), the vision rubric on the targets with no axis below 3, the identity-lock and reflex checks, state coverage, accessibility. Fix and re-run until it passes, stating per change what changed and why. Then the PM signs off in `design/UPLIFT.md`.

### Step 7: Handoff

Add to the journey spec's `AGENT_BRIEF.md` (or write `design/AGENT_BRIEF.md` if none):
- Read order: `DESIGN.md`, `design/screens/<place>.md`, the breadboard, the `.feature` file.
- Slices, cheapest visible win first: (1) tokens and theme of the component library (changes every screen at once), (2) app shell, navigation, page header, (3) places in job priority, each with all states.
- Rules: build on the component library themed with tokens; no raw values; every state from the screen spec; ambiguity goes to STATUS.md as a question.
- Verification: `design-parity` against `design/targets/` per place; `uiux-visual-review` in CI with the baseline ratchet; refresh the baseline after each slice.

Implementation then runs through `fullstack-engineer` with `uiux-design-vue3` and `uiux-design-tailwindv4` (or the repo's stack).

## Turn style

First line: mode, step, what this turn does. Show, don't describe: a sheet or a prototype beats a paragraph. Last line: the next question or gate. Converse in the PM's language; tokens, files and code in English.

## References

| Read | When |
|-|-|
| `references/art-direction.md` | Step 2: Design Read, register, direction menu, signature, dials, counterfactual test, evolving an existing system |
| `references/reflex-defaults.md` | Steps 2, 3, 6: patterns that make a UI look generic, and what to do instead |
| `references/inspiration-intake.md` | Step 2: extracting DNA from reference sites, synthesis without cloning |
| `references/direction-prototypes.md` | Step 3: building, measuring and presenting competing directions |
| `references/screen-spec.md` | Step 5: visual spec per place, bound to breadboard IDs |
| `references/product-ui-craft.md` | Steps 3 and 5: tables, forms, dashboards, navigation, states, feedback, AI surfaces |
| `references/preflight.md` | Step 6: the gate before handoff |
| `../uiux-visual-review/SKILL.md` | Steps 1, 3, 6: running the measured and vision review |
| `../uiux-design-system/references/design-md.md` | Step 4: writing the Art Direction into DESIGN.md |
| `../uiux-design-system/references/component-library-choice.md` | Step 4: choosing and theming a component library |

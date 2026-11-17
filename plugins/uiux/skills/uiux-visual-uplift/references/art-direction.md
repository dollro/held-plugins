# Art Direction

The decisions that make a product recognisable, made once, written down, and locked. Each decision names its reason from the brief (users, job, usage frequency, brand) or the audit.

## 1. Design Read

One line: the feeling plus the bet. It is the tie-breaker for every later decision no rule covers.

- Weak: "Modern, clean and user-friendly." (decides nothing)
- Strong: "Calm, exact, fast to scan: trust through precision, not decoration."
- Strong: "A workbench, not a showroom: dense, keyboard-first, quiet until something needs attention."

## 2. Register

Decide first; it flips many rules.

| | product | brand |
|-|-|-|
| Design serves | a recurring task | first impression, persuasion |
| Density | as high as scanning allows | generous |
| Type | 1 family (2 at most), tight scale | expressive display face, large scale |
| Signature | in a functional element | can be the layout itself |
| Motion budget | feedback only | orchestrated moments |
| Component library | yes, themed | optional, often bespoke |

An app with a marketing page has two registers: lock both, share tokens, and keep the product screens in `product`.

## 3. Direction (commit to one)

| Direction | Fits | Visual traits | Risk |
|-|-|-|-|
| Swiss / grid | data products, finance, tools for experts | strict grid, one sans in several weights, neutral surfaces, colour only for meaning | sterile without a signature |
| Technical / utilitarian | developer tools, operations, analysts | mono accents, dense tables, visible structure (rules, labels), keyboard affordances | hostile to occasional users |
| Editorial | research, reports, knowledge work | strong typographic hierarchy, generous measure, a serif or high-contrast display for headings | slow for dense data |
| Calm / soft | health, HR, consumer services, onboarding-heavy | low contrast surfaces, rounded shapes, warm neutrals, generous spacing | vague hierarchy |
| Industrial / signage | logistics, field work, status-heavy | high contrast, big numerals, bold status colours, clear zones | loud |
| Luxury / refined | premium services, investors, advisory | restraint, fine rules, precise spacing, one accent, quality type | cold, slow |
| Playful | consumer, education, creative | saturated palette, expressive shapes, characterful type, motion | wears out in daily use |
| Brutalist / raw | internal tools with personality, creative tech | exposed structure, system fonts on purpose, hard edges | looks unfinished if half-done |

Mixing is allowed when stated ("Swiss grid with editorial headings"), never by drift.

**Counterfactual test:** would you propose this look for any similar product in the category? If yes, it is the category default; push one decision (type, surface, accent, signature) away from it and say why. A fintech app need not be blue; an AI tool need not be purple on black.

## 4. Signature

The single element the product is remembered by, tied to its job. Spend boldness here and keep everything else quiet ("remove one accessory").

Good signatures in product UIs come from the domain:
- a distinctive status language (shape plus colour plus wording) for pipeline stages;
- one characterful numeric face for the key figures, used nowhere else;
- a timeline or score visual that explains the core decision at a glance;
- a precise, consistent keyboard command bar.

Not signatures: a gradient hero, glass cards, an illustration style the product never uses again.

## 5. Dials (1 to 10)

| Dial | 1 | 10 | Typical product UI |
|-|-|-|-|
| `design_variance` | convention | experimental | 3 to 5 |
| `motion_intensity` | static | choreographed | 2 to 4 |
| `visual_density` | airy | packed | 5 to 8 for daily expert tools, 3 to 5 for occasional users |

Dials keep later screens consistent: a new screen at density 7 next to old screens at 4 is drift.

## 6. Colour strategy

| Strategy | Meaning | Fits |
|-|-|-|
| restrained | tinted neutrals carry the screen, one accent ≤ ~10% of area | most product UIs |
| committed | one saturated colour carries 30 to 60% | brand register, strong identity |
| full palette | 3 to 4 named roles | categorical data, multi-product suites |
| drenched | the surface is the colour | campaigns, rarely in apps |

Method: OKLCH ramps; neutrals tinted toward the brand hue (chroma +0.005 to 0.015) rather than pure grey; status colours in the same chroma language; dark mode re-derived, not inverted; every text and UI pair passes WCAG AA (`../../uiux-design-system/references/color-utilities.md`).

## 7. Type

Pick from the subject and the register, not from habit. Roles: display (used with restraint), body, utility/mono for data. Pair on a contrast axis (serif with sans, geometric with humanist) or use one family in several weights; product UIs mostly do the latter. Tabular numerals for any column of numbers. Body measure 65 to 75 characters. Self-host or bundle the fonts the direction needs; a direction that depends on a font the app can't ship is not a direction.

## 8. Evolving an existing system (uplift mode)

The MVP's design system is usually structurally fine and visually generic. Keep:
- token names at the semantic and mapped tiers, component names and variants, breadboard IDs;
- the spacing base and breakpoints, unless the audit shows they cause problems.

Change by remapping semantic values (colour roles, type roles, radius, elevation, motion) and adding missing tokens the audit found (text-on-action, surface levels, status surfaces, focus ring). Code that already uses tokens then changes appearance without edits; code with raw values shows up in the review as off-token and is fixed screen by screen.

## 9. Writing it down

Into `design/UPLIFT.md` during Steps 2 and 3; into `DESIGN.md` at Step 4:

```markdown
## Overview
<Design Read>. For <audience>, used <frequency>; density <n>/10. It is not <what it must not feel like>.

## Art Direction
- Register: product
- Direction: Swiss grid with editorial headings, because <reason from the brief>
- Signature: <element>, because <why it fits the job>
- Dials: variance 4, motion 3, density 7
- Colour strategy: restrained
- Inspiration: <site> took <DNA>, rejected <what>; synthesis: <one line>
- Lock: every screen must read as the same product if placed side by side. New values go through the tokens, never into components.
```

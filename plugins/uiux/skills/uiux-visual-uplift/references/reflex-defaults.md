# Reflex Defaults

Patterns a model (and a hurried designer) reaches for without a reason. Each makes a UI look templated. None is forbidden: one is allowed when the brief asks for it and `DESIGN.md` says why. Unjustified, it is a finding.

**The generic test:** could someone look at the screen and say with certainty "a template" or "an AI made that"? Two passes:
- First order: generic for any product (characterless, framework defaults).
- Second order: the expected look for this category (the category predicts the aesthetic).

## Layout

| Reflex | Instead |
|-|-|
| Three equal cards in a row for anything | List with dividers, table, stat strip, asymmetric grid; cards only when elevation means "separate object" |
| Card inside a card | One surface level per container; use spacing or a rule inside |
| Dashboard = grid of equal KPI tiles | Lead with the one number that answers the job; the rest smaller or in a table |
| Centred hero over a dark gradient (brand pages) | Split asymmetric, full-bleed type, product in context |
| Every section the same block pattern | Vary the pattern family across a long page |
| Numbered section markers `01 / 02 / 03` and eyebrow kickers everywhere | Only when the content is a real sequence |
| Decorative status dots, fake "trusted by" rows, div-drawn fake screenshots | Real content or nothing |
| Sidebar + top bar + breadcrumbs + tabs all at once | One primary navigation pattern; ≤ ~5 top-level items |

## Colour and surface

| Reflex | Instead |
|-|-|
| Purple-to-blue gradients, glow on dark ("AI look") | Derive from the brief; one accent |
| Gradient text as "premium" | Weight, size and space carry emphasis |
| Pure grey neutrals (`#f5f5f5`, `#e5e5e5`) | Neutrals tinted toward the brand hue |
| Cream or beige default background chosen for "warmth" without a reason | Decide the surface from the direction |
| Glassmorphism on everything | Solid surfaces; translucency only for overlays over content |
| Accent colour on every interactive element | Accent for the primary action and current state; secondary actions neutral |
| Status by colour alone | Colour plus icon or label |

## Type

| Reflex | Instead |
|-|-|
| Framework default face picked because it was there (Inter, Roboto, system-ui as an unexamined choice) | Choose the face for the direction; a neutral grotesque is fine when chosen and tuned (weights, tracking, tabular numerals) |
| The model's go-to "characterful" faces for personality (Playfair Display, Fraunces, Space Grotesk, Instrument Serif) | Pick from the subject; justify any serif |
| Huge hero type in a product screen | Product headings stay modest; hierarchy through weight and space |
| Light grey body text for elegance | Body at AA contrast or better |

## Copy (copy is design)

| Reflex | Instead |
|-|-|
| Buzzwords: seamless, powerful, next-gen, elevate, unleash | Say what happens, from the user's side |
| "No data", "Error", "Something went wrong" | What happened, why if known, the next action |
| Fake-precise numbers in demos (`99.9%`, `10x`) | Realistic seed data from the domain |
| Em-dash chains as a stylistic tic | Full stops; shorter sentences |
| Inconsistent action verbs (Save / Submit / Confirm for the same act) | One verb per action through the flow ("Publish" → "Published") |

## Motion

| Reflex | Instead |
|-|-|
| Bounce or elastic easing on UI controls | One named easing curve; overshoot only if the direction calls for it |
| Fade-in on scroll for every section | One orchestrated moment, or none |
| Infinite decorative animation | Motion only while something is happening |
| Motion without a reason | Each motion explains a change in one sentence, or it goes |

## Components

| Reflex | Instead |
|-|-|
| Untouched component library defaults (the shadcn / Material / Bootstrap look) | Theme radius, type, colour, density and focus ring with the tokens |
| Modal for everything | Inline editing, drawers for context, modals only for blocking decisions |
| Toasts for errors that need action | Inline error at the source; toasts for confirmations |
| Spinner on a white page | Skeleton with final dimensions |

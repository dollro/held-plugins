---
name: uiux-design-system
description: "Tool-agnostic design system architecture: component tiers and naming (atoms to screens), 3-tier tokens (primitive, semantic, mapped text/icon/surface/border) as W3C DTCG, type scale and 4px grid, dark mode and multi-brand theming, UX and content patterns, WCAG 2.2 tokens, code pipeline. Use when architecting, naming, auditing or extending a design system, tokens or component inventory. Not for Tailwind v4 code (uiux-design-tailwindv4) or drawing in Penpot/Figma (uiux-design-penpot/figma)."
---

# Design System Architecture

Architect production design systems from token foundations through component hierarchy, UX patterns, theming and accessibility. Follows W3C DTCG, atomic design, and practice from Brad Frost, UI Collective, IBM Carbon, Salesforce Lightning and Atlassian.

This file holds the method and the rules that always apply. Details live in `references/`; read the one that matches the job (index at the end). Naming advice or a quick token review usually needs nothing beyond this file and `references/token-architecture.md`.

The `references/` here are the **shared, tool-agnostic source** for `uiux-design-penpot`, `uiux-design-figma` and `uiux-image2design`. Tool plugins read them from here; they are not duplicated.

## Mental model

A design system is a tree. **Roots** are primitive tokens (raw values nobody sees directly), the **trunk** is semantic tokens (intent: primary, error, neutral), the **leaves** are mapped/component tokens applied to UI (surface fills, text, icon and border colors per state). Change a root and it ripples to every leaf. Tokens are *design decisions*, not just CSS variables.

## Workflow

1. **Establish scope.** Single brand or multi-brand, which modes (light, dark, high contrast), which platforms, greenfield or existing tokens. Decide 2 tiers (single brand, no dark mode, small team) or 3 tiers (multi-brand, dark/high-contrast mode, shared library, rebrand expected).
2. **Foundations first.** Primitives in priority order: color (six scales: primary, neutral, error, success, warning, information), typography, number scale; then radius, shadow, sizing, border, motion, opacity, z-index, breakpoints.
3. **Semantic tier.** Map primitives to intent; this is the layer swapped per theme or brand.
4. **Mapped tier.** Fill the four categories text, icon, surface, border with all states, light and dark values.
5. **Components.** Build atoms first, then compose upward with instances; every interactive component gets default, hover, focus, disabled (and error/selected where relevant).
6. **Patterns and screens.** Compose layouts, sections, state patterns, product screens; apply UX decision patterns and content voice.
7. **Verify.** Contrast for every text/surface pair in every mode, focus rings, touch targets, naming consistency, completeness checklist (`references/design-system-template.md` §13).
8. **Ship to code.** DTCG `.tokens.json` as the single source, transformed to CSS custom properties, Tailwind `@theme`, SCSS or native platforms.

## Rules that always apply

**Tokens**
- Never skip tiers: component → semantic → primitive → raw value. Primitives are the only place raw values (hex, px, font stacks) live.
- Semantic names encode intent, not appearance (`danger`, not `red`). Define both sides of contrast pairs (`on-*`).
- Naming formula `{namespace}.{category}.{concept}.{property}.{variant}.{scale}.{state}`: fixed order, only levels that add meaning, at least category + one level, at most ~5 levels. The token file uses `.`; platform names (`-`, `/`) are derived at build time.
- Theme and brand by remapping the **semantic** tier: same token names, different values per mode. Component tokens stay stable.
- Icon tokens mirror text tokens. Alert surfaces use the 50 shade (light) / 900 shade (dark).
- All spacing, sizing, radius and border values are multiples of 4; the only exceptions are 1px borders and 2px focus rings. Color scales are solid hex, never opacity-based.
- Body text stays 16px on every breakpoint; only headings scale down. Nothing readable below 12px. Font sizes in `rem`.
- Start lean. A semantic token that only aliases a primitive without adding meaning is skipped. Version token sets like code: new token = minor, rename/remove = major.

**Components**
- Name `{tier}/{component}/{variant-type}/{variant-value}`; prefer variant properties for multi-axis components; internal building blocks get a `.` prefix.
- Once atoms are registered, higher tiers use instances, never rebuilt shapes.
- Focus ring: separate 2px outside stroke with `border/focus`, 3:1 contrast. Touch targets 44px by default (24px is the WCAG 2.2 AA floor).
- Start monolithic, split when variant combinations exceed ~50 or parts are independently reusable.

## Decision framework

**Create a token?** Used in 2+ places → tokenize. Changes with theming → must be a token regardless of reuse. One-off override → skip (local value or component tier). Existing token covers the intent → use it.

**Which tier?** Raw value → primitive. UI intent (background role, spacing direction) → semantic. Component-specific divergence → component/mapped. When in doubt, start semantic; promote only when a specific element diverges.

**Create a component?** Used 3+ times, has interactive states, or represents an enforced design decision → register. Otherwise keep as a one-off.

**Variant or new component?** Same layer structure and same semantic role → variant. Different structure or role → new component.

**Branded house or house of brands?** Same components, different primary color → branded house (semantic modes). Completely different identities → house of brands (separate files with own primitives).

## Output

- Tokens: DTCG JSON (`.tokens.json`) with `$value`/`$type`, aliases as `{path.to.token}`, grouped by tier; scaffold from `references/starter-template.md` when nothing exists.
- Reviews: findings as `token or component · problem → fix`, tier violations and missing states first, then naming, then gaps against the completeness checklist.
- Mirror the user's language; token names, file names and code in English.

## References

| Read | When |
|-|-|
| `references/token-architecture.md` | Naming or reviewing tokens: tree model, 3 tiers, 2 vs 3 tiers, naming taxonomy, state names, separators |
| `references/token-categories.md` | Defining primitives and semantics per category: color scales, 4px number scale, spacing, sizing to opacity |
| `references/typography.md` | Generating a type scale, line heights, text style names, responsive type |
| `references/mapped-tokens.md` | Building or checking the mapped tier: full text/icon/surface/border tables with light and dark values |
| `references/theming-multi-brand.md` | Dark mode, high-contrast mode, branded house vs house of brands, white-label |
| `references/dtcg-format.md` | Writing or validating `.tokens` / `.tokens.json` files |
| `references/starter-template.md` | New project with no tokens: complete DTCG starter set (primitives, semantics, mapped) |
| `references/platform-mapping.md` | Turning tokens into code: pipeline, CSS three layers, Tailwind v4 `@theme`, SCSS, Style Dictionary, native |
| `references/component-architecture.md` | Component tiers, naming, internal vs published, state variants, component properties |
| `references/componentization-guide.md` | Component boundaries: register or not, split vs monolithic, variants, instances, scaling, anti-patterns, build order |
| `references/component-patterns.md` | Building or reviewing a specific component: structure, token bindings, variant matrix, page-level patterns |
| `references/design-system-template.md` | Architecting from scratch: full inventory, type and grid specs, motion, pattern recipes, UX decisions, screens, content voice, icons, responsive rules, completeness checklist |
| `references/layout-patterns.md` | Choosing Flex vs Grid, auto layout, fluid layouts without breakpoints |
| `references/accessibility.md` | Any user-facing interface: WCAG 2.2 + EAA checklist, contrast, keyboard, ARIA, accessibility tokens |
| `references/platform-guidelines.md` | Targeting iOS, Android, responsive web or desktop: screen sizes, safe areas, platform specs |
| `references/color-utilities.md` | Converting OKLCH/HSL/RGB to hex, generating palettes, computing contrast ratios |
| `references/token-binding-strategy.md` | Binding tokens to shapes in a design tool: greenfield inline, brownfield sweep, coverage report |
| `references/visual-reference-naming.md` | Organising screenshots or visual references for a design system |

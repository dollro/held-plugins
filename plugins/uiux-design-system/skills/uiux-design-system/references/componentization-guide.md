# Design System Componentization Guide

Decision frameworks for when, how, and at what granularity to componentize UI elements
in a design tool. These criteria apply to any tool (Penpot, Figma) — tool-specific API
patterns live in the respective tool plugins.

The goal of componentization is **change once, update everywhere**. A well-modularized
design system lets you modify a button's radius token and see every button instance across
100 screens update automatically. Bad modularization makes this impossible — either because
components aren't registered, tokens aren't bound, or instances are detached.

---

## Table of Contents

0. [Internal vs Published Components](#0-internal-vs-published-components)
1. [Should This Be a Component?](#1-should-this-be-a-component)
2. [Granularity: Split vs. Monolithic](#2-granularity-split-vs-monolithic)
3. [Variant Architecture](#3-variant-architecture)
4. [Token Binding Through the Hierarchy](#4-token-binding-through-the-hierarchy)
5. [Instance vs. Fresh Build](#5-instance-vs-fresh-build)
6. [Composition Patterns](#6-composition-patterns)
7. [Scaling to 100+ Screens](#7-scaling-to-100-screens)
8. [Anti-Patterns Checklist](#8-anti-patterns-checklist)
9. [Decision Trees](#9-decision-trees)
10. [Recommended Build Order](#10-recommended-build-order)

---

## 0. Internal vs Published Components

Before deciding whether to componentize, understand the two publication levels:

**Published components** (end users see these):
- Named normally: `Menu`, `Tab Bar`, `Carousel`, `Input`
- Available in the asset panel / component library
- The components designers use day-to-day

**Internal components** (building blocks, not published):
- Prefixed with a dot: `.menu-item`, `.tab-item`, `.carousel-item`, `.text-area`
- The dot prefix tells Figma not to publish it in the library
- In code-based systems, use `_` prefix or an `internal/` directory
- Used inside published components via composition

**Why this matters:** End users should only see composed, ready-to-use components — not the individual building blocks. A `.menu-item` is meaningless on its own; the `Menu` component (composed of `.menu-item` instances) is what designers need.

**Examples:**

```
.menu-item     → internal → used inside Menu
.tab-item      → internal → used inside Tab Bar
.carousel-item → internal → used inside Carousel
.text-area     → internal → used inside Text Area (label + area + hint)
.button-group-item → internal → used inside Button Group
```

**Rule:** If a sub-component has no independent meaning (a tab item outside a tab bar), make it internal. If it's reusable across multiple parents (an avatar used in cards, headers, and comments), publish it.

---

## 1. Should This Be a Component?

**Register as a library component when 2+ of these hold:**

- **Reuse threshold**: Used in 3+ distinct contexts (the "rule of three"). A button used
  on every screen: definitely. A one-off hero layout: probably not.
- **State variations**: Has meaningful interactive states (hover, disabled, loading, error)
  that must be consistent everywhere.
- **Enforcement value**: Represents a design decision the system must enforce centrally.
  If someone rebuilds it from scratch, would they likely get it wrong?
- **Update propagation need**: If its visual treatment changes (radius, color, spacing),
  should all usages update automatically?
- **Complexity**: Contains internal layout rules, token bindings, or accessibility
  requirements that are non-obvious to recreate correctly.

**Keep as a one-off (not a component) when:**

- Used only once or twice and unlikely to recur
- Is purely compositional — just arranging existing components in a layout with no
  new design decisions
- Would require so many instance overrides that the component link becomes fragile
  (>50% of properties overridden = reconsider)

**The 80% test**: Does an existing component already solve 80% of this use case? If yes,
extend it with a variant rather than creating a new component.

---

## 2. Granularity: Split vs. Monolithic

### Split into sub-components when:

- **Sub-parts are independently reusable.** An avatar used inside a card AND inside a
  header AND standalone → make avatar its own component. The card composes it via instance.
- **Variant explosion.** If the component has >4 variant axes, splitting reduces
  combinations. Extract the axis that varies most independently into a sub-component.
- **Different update cadences.** Icon sets change more frequently than button shapes.
  Separate components let you update icons without touching buttons.

### Keep monolithic when:

- **Sub-parts have no independent meaning.** A checkbox's checkmark is meaningless alone.
  A button's label is not a separate component.
- **Splitting adds indirection without reuse.** If you'd create a sub-component used
  in exactly one parent, you're just adding complexity.
- **The element is atom-level.** Buttons, inputs, badges, toggles — these are the smallest
  meaningful units. Don't split them further.

### The cost of getting it wrong:

| Direction | Cost |
|-|-|
| Over-componentized | Cognitive overhead finding the right component, brittle nesting chains, design tool performance issues from deep instance trees |
| Under-componentized | Inconsistency across screens, repeated manual work, inability to propagate changes, broken design system promise |

**When in doubt, start monolithic and split when pain appears.** It's easier to split a
working component than to merge scattered one-offs.

---

## 3. Variant Architecture

### Multi-axis variant (recommended default)

Group related variations into a single component with switchable properties:

```
Button
  - style: primary | secondary | ghost | danger
  - size: sm | md | lg
  - state: default | hover | active | disabled | loading
```

**Use this when:**
- Axes are orthogonal (any style works with any size works with any state)
- Total combinations stay under ~40-50 variants
- The component's layer structure is identical across all variants

### Split into separate components when:

- **Axes aren't orthogonal.** "Compact" style drops the icon sub-element entirely —
  the layer structure differs, so it's a different component.
- **Combinations exceed ~50.** The variant picker becomes unusable. Split the most
  independent axis into a sub-component.
- **A variant axis represents fundamentally different behavior.** A dropdown and a
  combobox share styling but differ in interaction — separate components.

### Naming variant properties

Use meaningful property names that describe the axis, not the values:

| Property | Values | Not |
|-|-|-|
| `style` | primary, secondary, ghost | `color` (too generic) |
| `size` | sm, md, lg | `dimension` (too abstract) |
| `state` | default, hover, disabled | `interaction` (unclear) |

### Managing explosion via nesting

If Button × IconPosition × Size × State × Theme = 200+ combinations, extract:
- Icon handling → separate Icon component swapped via nested instance
- Theme → controlled by token binding, not variants
- Result: Button only needs Style × Size × State ≈ 36 variants

---

## 4. Token Binding Through the Hierarchy

The most important architectural decision: **how tokens flow through components.**

### The chain that enables "change once, update everywhere":

```
Primitive token (raw value)
  ↓ referenced by
Semantic token (intent)
  ↓ referenced by
Component token (scoped override, optional)
  ↓ bound to
Shape property (fill, stroke, font-size, etc.)
```

If ANY link in this chain is broken (a shape has a hardcoded hex instead of a token
binding), that shape won't update when the system changes.

### Rules by component tier:

**Atoms (button, input, badge):**
- Bind to **semantic tokens** directly. Atoms are generic enough that component-level
  tokens usually add unnecessary indirection.
- Exception: if the atom needs a variant-specific override (e.g., danger button uses
  `color.feedback.danger` instead of `color.interactive.default`), create a component
  token for that specific override.
- Every visual property must be token-bound: fills, strokes, border-radius, font-size,
  font-weight, spacing (padding/gap). No hardcoded values.

**Molecules (card, form-field, nav-item):**
- Bind molecule-level properties (card background, card shadow, card radius) to semantic
  tokens.
- Nested atom instances inherit their own token bindings from the atom main component.
  Don't re-bind atom properties at the molecule level.

**Organisms (header, sidebar, data-table):**
- Same principle: bind organism-level properties to semantic tokens.
- Nested molecules and atoms carry their own bindings.
- Only create component-level tokens if the organism genuinely diverges from semantic
  defaults (e.g., sidebar has a darker background than the standard surface).

### The binding audit question:

For every shape in a component, ask: "If I change the semantic token this property
should reference, will this shape update?" If the answer is no, the binding is missing.

---

## 5. Instance vs. Fresh Build

### Use component instances when:

- The composite needs the element to stay synchronized with its main component
- Customization is <30% of the component's properties (overrides are lightweight)
- You want the design file to function as a real design system, not a flat mockup

### Build from scratch when:

- The usage diverges >50% from any existing component
- You're prototyping/exploring and don't want component constraints yet
- The element is truly one-off and will never need to sync

### The cardinal rule for design system generation:

**After registering atoms, all subsequent tiers MUST use `component.instance()` to place
them.** Never rebuild a button shape manually inside a card if a button component exists
in the library. This is what makes the output a real design system.

A generated design file with 50 button shapes but zero button instances is a mockup,
not a design system — it cannot propagate changes.

### Penpot-specific considerations:

- Text content overrides may break style inheritance from main. Apply typography tokens
  BEFORE creating instances. Use token binding for colors rather than direct overrides.
- You cannot add/remove elements from instances — only hide, swap nested components,
  and change styles. Design atom layer structures with this in mind.
- Nested component swaps work: a card can swap its icon from one component to another.
  Design swap points deliberately.

---

## 6. Composition Patterns

### Pattern 1: Flat Composition (atoms inside a layout)

```
Card (molecule, registered component)
  - Avatar instance (atom)
  - Text (styled with tokens)
  - Badge instance (atom)
  - Button instance (atom)
```

Each nested atom is a component instance. The card owns the layout (flex/grid) and
spacing tokens. Atom instances handle their own visual properties.

### Pattern 2: Slot-Based Composition

Design components with clear "swap points" where different content can be inserted:

```
ListItem (molecule)
  - [leading slot] → swap between: Avatar, Icon, Checkbox
  - Text content
  - [trailing slot] → swap between: Badge, ChevronIcon, Toggle
```

The leading/trailing elements are nested component instances that consumers swap.

### Pattern 3: Responsive Variants

For components that change structure at breakpoints:

```
NavigationBar
  - variant: desktop → horizontal layout, text labels
  - variant: tablet → horizontal, icon-only with tooltips
  - variant: mobile → bottom bar, icon + small label
```

These are structural variants (layer tree differs), so they're variants of the same
component rather than separate components — the navigation bar's semantic role is the same.

---

## 7. Scaling to 100+ Screens

### Library organization

- **Separate libraries by domain** when the system grows large:
  `foundations` (tokens, colors, typography) → `core-components` (atoms, molecules) →
  `patterns` (organisms, layouts) → `product-screens` (actual pages)
- Smaller library files = better performance and easier team ownership
- Chain libraries: product-screens connects to patterns, which connects to
  core-components, which connects to foundations

### Naming as infrastructure

Component names are the primary discovery mechanism. Use hierarchical naming:

```
atoms/button/primary/default
atoms/button/primary/hover
atoms/input/text/default
molecules/card/product/default
organisms/header/main/desktop
```

This makes the asset panel searchable, sortable, and predictable at any scale.

### Governance

- **Track metrics**: component adoption rate, override rate, detachment rate,
  variant count growth
- **Audit quarterly**: remove unused components, merge near-duplicates, rename
  tokens that drifted from their intent
- **Decision trees as docs**: codify "when to use X vs Y" as flowcharts alongside
  the library — reduces support burden

---

## 8. Anti-Patterns Checklist

Review generated design files against these:

| Anti-pattern | Signal | Fix |
|-|-|-|
| **Hardcoded values** | Shapes with raw hex/px instead of token bindings | Bind every property to semantic tokens |
| **Detached instances** | Components that were detached and never re-attached | Re-attach or create new variant |
| **Duplicate components** | Near-identical components that should be variants | Consolidate into one with variant axes |
| **Variant explosion** | >50 variants, many unused | Split axes, nest sub-components |
| **Premature componentization** | Components used only once | Delete or demote to pattern |
| **God component** | One component with 10+ variant axes or boolean props | Break into focused sub-components |
| **Token bypass** | Components referencing primitives directly | Route through semantic tokens |
| **Fresh shapes in composites** | Molecules rebuilding atoms instead of instancing | Replace with `component.instance()` |
| **Missing annotations** | Components without usage documentation | Add annotations describing when/how to use |
| **Orphan components** | Registered but never instantiated anywhere | Either use them or remove |

---

## 9. Decision Trees

### "Should I make this a component?"

```
Is it used in 3+ places?
  - Yes → Register as component
  - No
      Has meaningful state variations?
        - Yes → Register as component
        - No
            Represents an enforced design decision?
              - Yes → Register as component
              - No → Keep as one-off (pattern or local group)
```

### "Should I add a variant or create a new component?"

```
Does the new variation share the same layer structure?
  - Yes
      Does it share the same semantic role? (both are "buttons")
        - Yes → Add as variant
        - No → New component
  - No (different layers, different structure)
      → New component
```

### "Should I use a component instance or build fresh?"

```
Does a registered component exist for this element?
  - Yes
      Would I override >50% of its properties?
        - Yes → Consider new variant or build fresh
        - No → Use instance
  - No
      Does this element meet the componentization criteria?
        - Yes → Register it first, then use instances
        - No → Build fresh (one-off)
```

---

## 10. Recommended Build Order

Build atoms first, then compose upward. This order minimizes rework — each component uses instances of previously built components:

**Phase 1 — Core atoms:**
1. Button (filled, outline, transparent × states × sizes)
2. Label (default, required with asterisk)
3. Input Field (all states including focus ring)

**Phase 2 — Core molecules:**
4. Input (composed: Label + Input Field + Hint Text)
5. Checkbox + Checkbox Label
6. Radio Button + Radio Label
7. Switch/Toggle + Switch Label

**Phase 3 — Content atoms + organisms:**
8. Text Area (Label + multiline field + Hint)
9. Menu Item (internal `.menu-item`) → Menu
10. Tab Item (internal `.tab-item`) → Tab Bar

**Phase 4 — Secondary atoms:**
11. Button Group (from `.button-group-item`)
12. Link + Breadcrumb variant
13. Avatar (icon/image/initials × sizes) + Avatar Group
14. Tag/Chip (selected/unselected)
15. Badge (count + dot × semantic colors)

**Phase 5 — Feedback + complex organisms:**
16. Loader/Spinner (sizes + animation)
17. Progress Bar + Progress Circle
18. Snackbar/Toast (semantic variants + progress)
19. Button Icon (icon-only circular button)
20. Carousel (.carousel-item + navigation + progress)
21. Table (Cell Item → Column → Table — most complex)

**Why this order?** Each phase builds on the previous. Input (phase 2) needs Label and Input Field (phase 1). Menu (phase 3) needs its internal `.menu-item`. Toast (phase 5) may use Button Icon for the close button.

---

## Sources

- Brad Frost — Atomic Design Methodology
- Nathan Curtis / EightShapes — Patterns vs Components
- Martin Fowler — Design Token-Based UI Architecture
- GitLab Pajamas — Design Token Strategy
- Smashing Magazine — Decision Trees For UI Components (2024)
- Smashing Magazine — Building Components For Consumption, Not Complexity (2023)
- Penpot Blog — Component Variants to Scale Your Design System
- Penpot Blog — Design Systems Best Practices with Penpot
- Figma — Component Architecture Best Practices
- UXPin — Design System Governance

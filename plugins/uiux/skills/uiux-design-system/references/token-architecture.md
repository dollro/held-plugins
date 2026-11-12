# Token Architecture and Naming

The mental model behind design tokens, the 3-tier hierarchy (primitive, semantic, component/mapped), and the naming taxonomy. Read before creating, naming or reviewing tokens. Category-by-category guidance is in `token-categories.md`, the complete mapped tier in `mapped-tokens.md`, the file format in `dtcg-format.md`.

## Philosophy

### The Tree Metaphor

A design system is a tree:

- **Roots** = Primitive tokens — raw values nobody sees directly. Hex codes, pixel values, font family strings.
- **Trunk** = Semantic tokens — contextual roles connecting raw values to intent. "Primary", "error", "neutral" — the translation layer.
- **Leaves** = Mapped/Component tokens — what users actually see applied to components. Surface fills, text colors, border colors for specific states.

Every leaf traces back through the trunk to the roots. Change a root color, and it ripples through the trunk and out to every leaf that references it.

### Tokens Are Not Just Variables

Design tokens are *design decisions*, not just CSS variables. A raw color `#6C5CE7` is a value. The *decision* that it's your brand's primary color, and the further *decision* that primary buttons use it as a background — those are the tokens that matter.

### Naming Across the Industry

| This Skill | UI Collective | Brad Frost | Salesforce | Carbon (IBM) |
|-|-|-|-|-|
| Tier 1 (Primitive) | Brand | Tier 1 | Global | Foundation |
| Tier 2 (Semantic) | Alias | Tier 2 | Alias / Semantic | Theme |
| Tier 3 (Component) | Mapped | Tier 3 | Component-specific | Component |

The three-tier model is the architecture used by IBM Carbon, Salesforce Lightning, Atlassian, and recommended by Brad Frost. Figma's variable scoping and Penpot's token system naturally support it.

## The 3-Tier Token Hierarchy

Each tier builds on the one below, creating layered abstraction from raw values to component-specific decisions.

| Tier | Purpose | Holds Raw Values? | Example |
|-|-|-|-|
| Primitive | Raw values on a named scale | Yes | `color.blue.600` |
| Semantic | Intent-based aliases | No | `color.background.danger` |
| Component | Scoped to UI elements | No | `button.color.background.primary.hover` |

**Primitive tokens** define your palette — all available colors, sizes, values. They describe *what exists*. The roots of the tree — raw material.

**Semantic tokens** assign meaning — *how* primitives are used: which color is a background, which is danger text, which spacing goes between stacked elements. The trunk — the translation layer.

**Component tokens** handle exceptions — *where* a semantic value is overridden for a specific component or state. The leaves — what users see.

### Referencing Chain

```
Component tokens → Semantic tokens → Primitive tokens → Raw values

surface/action (mapped)
  → primary/default              (semantic/alias)
    → purple-500                 (primitive/brand)
      → #6C5CE7                  (raw value)
```

When theming, swap values at the **semantic** tier. Component tokens stay stable — the entire UI updates through the alias chain. Same token names, different values per mode.

### When to Use 2 vs 3 Tiers

**Two tiers** (Primitive → Semantic) are sufficient when:
- Single-brand, single-theme product
- Small team (1–3 designers)
- No dark mode or rebrand anticipated

**Three tiers** are recommended when:
- Multiple brands or sub-brands are involved
- Dark mode / high-contrast mode are requirements
- Component library is reused across projects
- Design language evolution anticipated (rebrands, v2.0)

Start with 2 tiers for simplicity; promote to 3 when real component-level divergence demands it.

### Tier Rules

1. **Never skip tiers.** Component → semantic → primitive. No shortcuts — it breaks the abstraction.
2. **Primitives are the only source of raw values.** Hex codes, pixel values, font stacks live exclusively in primitives.
3. **Semantic tokens encode intent, not appearance.** Name by role (`danger`, `surface`, `interactive`) not visual (`red`, `light-gray`).
4. **Component tokens are optional.** Only create when a component genuinely diverges from semantics.
5. **Start lean.** Begin with primitives + semantics. Add component tier when real divergence demands it.

## Naming Taxonomy

### Formula

```
{namespace}.{category}.{concept}.{property}.{variant}.{scale}.{state}
```

Not every token uses all seven levels. Include only levels that add meaning. The order is fixed — don't rearrange.

### Levels

| Level | Definition | When to Include | Examples |
|-|-|-|-|
| namespace | System or brand identifier | Multi-system orgs | `acme`, `nord`, `ds` |
| category | Token type / domain | Always | `color`, `space`, `font`, `shadow`, `border`, `motion`, `opacity`, `radius`, `z`, `breakpoint`, `size` |
| concept | Semantic role or grouping | Semantic + component tiers | `background`, `text`, `border`, `surface`, `interactive`, `feedback`, `inline`, `stack` |
| property | Specific attribute | When concept is ambiguous | `family`, `size`, `weight`, `line-height`, `duration`, `easing` |
| variant | Named variation | When element has variants | `primary`, `secondary`, `danger`, `success`, `warning`, `info` |
| scale | Position on a value scale | Primitive tier / sizing | `50`–`950`, `xs`/`s`/`m`/`l`/`xl`, `1`–`12` |
| state | Interactive / contextual state | Component tier / interactive | `hover`, `active`, `focus`, `disabled`, `pressed` |

**Minimum:** Every token needs `category` + one more level. **Maximum practical depth:** 5 levels.

### Annotated Examples

```
color.blue.600
cat . concept . scale                         (primitive — raw hue on numeric scale)

color.background.danger
cat . concept . variant                       (semantic — intent-based, no raw value)

button.color.background.primary.hover
comp . cat . concept . variant . state        (component — scoped, includes interaction state)

space.inline.md
cat . concept . scale                         (semantic — directional spacing, t-shirt size)
```

### Examples by Tier

**Primitive** — raw values: `color.blue.600`, `space.4`, `font.size.300`, `font.weight.semibold`, `shadow.elevation.2`, `radius.md`, `motion.duration.fast`

**Semantic** — intent: `color.background.surface`, `color.text.primary`, `color.interactive.default`, `color.feedback.success`, `space.inline.md`, `space.stack.lg`, `font.heading.size`, `shadow.overlay`

**Component** — scoped overrides: `button.color.background.primary.hover`, `button.radius`, `input.color.border.error`, `card.shadow.hover`

### Mapped Token Categories

At the component/mapped tier, tokens organize into **four categories** that get directly applied to UI elements (full tables with light/dark values in `mapped-tokens.md`):

| Category | What it controls | Example tokens |
|-|-|-|
| `text/*` | Text/font colors | `text/heading`, `text/body`, `text/action`, `text/on-action`, `text/disabled` |
| `icon/*` | Icon colors (mirrors text) | `icon/default`, `icon/action`, `icon/on-action`, `icon/disabled` |
| `surface/*` | Background fills | `surface/page`, `surface/default`, `surface/action`, `surface/action-hover` |
| `border/*` | Stroke/border colors | `border/default`, `border/action`, `border/focus`, `border/error` |

### State Naming

| State | When it applies |
|-|-|
| `default` | Resting state |
| `hover` | Mouse over |
| `hover-light` | Subtle hover (lighter surface change for inputs, rows) |
| `focus` | Keyboard focus |
| `disabled` | Non-interactive |
| `active` / `selected` | Currently active/toggled |
| `on-action` | Content that sits *on top of* an action surface (e.g., text on primary button) |

### Separator Conventions

- **Token files** (`.tokens`): `.` — `color.blue.600`
- **CSS custom properties**: `-` — `--color-blue-600`
- **SCSS variables**: `-` — `$color-blue-600`
- **Figma**: `/` — `color / blue / 600`
- **Penpot**: `.` — `color.blue.600`
- **Tailwind v4 classes**: `-` — `bg-[--color-bg-surface]`
- **Within levels**: `kebab-case` — `line-height`, `ease-in-out`

The canonical source is always the token file (`.` separators). Platform naming is derived during build.

## Token Proliferation Guard

- **Start lean.** Add later; removing is harder.
- **Alias test.** If a new semantic token just aliases a primitive with no added meaning, skip it.
- **Fewer well-named tokens > many granular tokens.** Each token is a maintenance commitment.
- **Audit quarterly.** Treat token sets like code — use semantic versioning. New token = minor bump. Rename/remove = major bump.

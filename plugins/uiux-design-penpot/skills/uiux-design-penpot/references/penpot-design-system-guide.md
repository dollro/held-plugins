# Penpot Design System Implementation Guide

> Penpot-specific implementation patterns for the design system architecture
> defined in `uiux-design-system/references/design-system-template.md`.

---

## 1. Penpot Structural Hierarchy

```
Team
  Project
    File (= 1 shared library = entire design system)
      Page 1
        Frame (board) A
          Component (main)
          Shapes, text, groups
          Nested component instances
        Frame (board) B
      Page 2
        ...
      Colors (asset palette — separate from canvas)
      Typographies (asset palette — separate from canvas)
      Tokens (native tokens panel — W3C DTCG format)
```

Key facts:
- **Shared library = file level.** Publish once; all assets (components, colors, typographies) become available team-wide.
- **Components live on the canvas** as layers. Automatically registered in assets panel when created.
- **Colors and typographies** are in the assets panel (left sidebar) — no canvas representation needed, but create visual documentation boards for human review.
- **Tokens** live in the dedicated tokens panel (left sidebar, tokens tab). Follow W3C DTCG JSON format natively.
- **Pages** sort in creation order (drag to reorder manually).
- **Frames** (boards) are the canvas containers within each page.

---

## 2. Page Structure & Naming

### Naming Convention

```
{category-prefix} {descriptive-name}
```

Lowercase with hyphens. No number prefixes (not a Penpot convention). Group related pages by keeping them adjacent.

### Complete Page List

One page per tier. Boards within each page separate individual components/topics.

```
cover
getting-started
foundations        ← colors, typography, spacing, grid, elevation, borders, icons
atoms              ← button, input, badge-tag, avatar, toggle-checkbox-radio, divider, tooltip, spinner
molecules          ← form-field, card, nav-item, dropdown-select, toast-alert, search-bar, pagination
organisms          ← header-navbar, sidebar-navigation, data-table, modal-dialog, footer, command-palette
patterns           ← layout-templates, section-hero, features, pricing, cta, testimonials, faq, states
screens-landing
screens-dashboard
screens-auth
screens-settings
```

### Page Purpose Reference

| Page | Purpose | Contains |
|-|-|-|
| `cover` | File thumbnail + metadata | Version, date, changelog, status. Use 1390x930 frame set as file thumbnail |
| `getting-started` | Usage guide for humans | Naming rules, grid explanation, token architecture, how-to |
| `foundations` | Tokens visualized | Boards per topic: colors (swatches, dark mode), typography (scale, pairings), spacing (scale, grid), elevation, icons |
| `atoms` | Smallest components | Board group per atom (button, input, badge, etc.). Each group: variants + anatomy + usage |
| `molecules` | Composed from atoms | Board group per molecule. Shows which atoms are nested inside |
| `organisms` | Complex compositions | Board group per organism. Responsive breakpoint frames (desktop/tablet/mobile) |
| `patterns` | Reusable section recipes | Board group per pattern: layout skeletons, section compositions, state patterns (empty/loading/error) |
| `screens-*` | Product pages | Real content, final designs. Built from patterns + component instances. Include prototype flows |

---

## 3. Frame (Board) Naming

### Convention

```
{page-context}/{frame-purpose}
```

Slashes for hierarchy — consistent with Penpot's asset grouping. Lowercase with hyphens within segments.

### Standard Frames on Tier Pages

On consolidated pages (atoms, molecules, organisms), boards carry the component scope. Each component gets a group of boards:

```
--- atoms page ---
button/variants          ← All variant instances in a grid
button/anatomy           ← Dissected view: padding, token refs, spacing
button/usage             ← Do/don't examples, usage guidelines
input/variants
input/anatomy
input/usage
badge/variants
badge/anatomy
...

--- organisms page ---
header-navbar/variants
header-navbar/responsive ← Desktop, tablet, mobile breakpoints
data-table/variants
data-table/responsive
modal-dialog/variants
...
```

### Foundations Page Frames

```
colors/primitives        ← Raw color ramp swatches
colors/semantic          ← Semantic mapping: bg-body, txt-primary, etc.
colors/dark-mode         ← Side-by-side light/dark comparison
typography/scale         ← Full type scale specimen
typography/pairings      ← Heading + body combinations in context
spacing/scale            ← Visual spacing ruler
spacing/grid             ← 12-column grid overlay at each breakpoint
elevation/levels         ← Shadow scale samples
icons/grid               ← Icon inventory
```

### Patterns Page Frames

```
layout/sidebar-content   ← Sidebar + main area at 1440px
layout/full-bleed        ← Stacked full-width sections
section-hero/variant-a   ← Hero with image right
section-hero/variant-b   ← Hero with centered text
section-hero/responsive  ← All hero variants at 1440/768/375
state-empty/default      ← Empty state pattern
state-loading/default    ← Skeleton loading pattern
state-error/default      ← Error state pattern
```

### Product Screen Frames

```
landing/desktop          ← Full landing page at 1440px
landing/tablet           ← Same at 768px
landing/mobile           ← Same at 375px
dashboard/main           ← Default dashboard view
dashboard/empty          ← Empty state
dashboard/loading        ← Skeleton loading state
```

---

## 4. Token Panel Usage (Native Penpot)

Tokens are organized into **sets** in Penpot's tokens panel. Create three sets:

```
Set: primitives     ← Raw values. Never applied directly to components.
Set: semantic       ← Intent-based aliases referencing primitives. Applied to components.
Set: component      ← (optional) Component-scoped overrides referencing semantic tokens.
```

### Concrete Token Values — Primitives

```json
{
  "color": {
    "blue": {
      "50":  { "$value": "#E6F1FB", "$type": "color" },
      "100": { "$value": "#B5D4F4", "$type": "color" },
      "200": { "$value": "#85B7EB", "$type": "color" },
      "400": { "$value": "#378ADD", "$type": "color" },
      "500": { "$value": "#2563EB", "$type": "color" },
      "600": { "$value": "#185FA5", "$type": "color" },
      "800": { "$value": "#0C447C", "$type": "color" },
      "900": { "$value": "#042C53", "$type": "color" }
    },
    "gray": {
      "50":  { "$value": "#F9FAFB", "$type": "color" },
      "100": { "$value": "#F3F4F6", "$type": "color" },
      "200": { "$value": "#E5E7EB", "$type": "color" },
      "300": { "$value": "#D1D5DB", "$type": "color" },
      "400": { "$value": "#9CA3AF", "$type": "color" },
      "500": { "$value": "#6B7280", "$type": "color" },
      "600": { "$value": "#4B5563", "$type": "color" },
      "700": { "$value": "#374151", "$type": "color" },
      "800": { "$value": "#1F2937", "$type": "color" },
      "900": { "$value": "#111827", "$type": "color" },
      "950": { "$value": "#030712", "$type": "color" }
    },
    "green":  { "500": { "$value": "#22C55E", "$type": "color" } },
    "red":    { "500": { "$value": "#EF4444", "$type": "color" } },
    "amber":  { "500": { "$value": "#F59E0B", "$type": "color" } },
    "white":  { "$value": "#FFFFFF", "$type": "color" },
    "black":  { "$value": "#000000", "$type": "color" }
  },
  "dimension": {
    "0": { "$value": "0px" }, "1": { "$value": "4px" }, "2": { "$value": "8px" },
    "3": { "$value": "12px" }, "4": { "$value": "16px" }, "5": { "$value": "20px" },
    "6": { "$value": "24px" }, "8": { "$value": "32px" },
    "10": { "$value": "40px" }, "12": { "$value": "48px" }, "16": { "$value": "64px" }
  },
  "borderRadius": {
    "none": { "$value": "0px" }, "sm": { "$value": "4px" }, "md": { "$value": "8px" },
    "lg": { "$value": "12px" }, "xl": { "$value": "16px" }, "full": { "$value": "9999px" }
  },
  "fontFamilies": {
    "sans": { "$value": "Inter", "$type": "fontFamilies" },
    "mono": { "$value": "JetBrains Mono", "$type": "fontFamilies" }
  },
  "fontSizes": {
    "xs": { "$value": "12", "$type": "fontSizes" }, "sm": { "$value": "14", "$type": "fontSizes" },
    "base": { "$value": "16", "$type": "fontSizes" }, "lg": { "$value": "18", "$type": "fontSizes" },
    "xl": { "$value": "20", "$type": "fontSizes" }, "2xl": { "$value": "24", "$type": "fontSizes" },
    "3xl": { "$value": "30", "$type": "fontSizes" }, "4xl": { "$value": "36", "$type": "fontSizes" }
  },
  "fontWeights": {
    "regular": { "$value": "400", "$type": "fontWeights" },
    "medium": { "$value": "500", "$type": "fontWeights" },
    "semibold": { "$value": "600", "$type": "fontWeights" },
    "bold": { "$value": "700", "$type": "fontWeights" }
  },
  "letterSpacing": {
    "tight": { "$value": "-0.025em", "$type": "letterSpacing" },
    "normal": { "$value": "0em", "$type": "letterSpacing" },
    "wide": { "$value": "0.05em", "$type": "letterSpacing" }
  },
  "shadow": {
    "sm": { "$value": "0 1 2 0 #0000000D", "$type": "shadow" },
    "md": { "$value": "0 4 6 -1 #0000001A", "$type": "shadow" },
    "lg": { "$value": "0 10 15 -3 #0000001A", "$type": "shadow" }
  },
  "opacity": {
    "subtle": { "$value": "0.1", "$type": "opacity" },
    "medium": { "$value": "0.5", "$type": "opacity" },
    "strong": { "$value": "0.8", "$type": "opacity" },
    "opaque": { "$value": "1", "$type": "opacity" }
  },
  "sizing": {
    "icon-sm": { "$value": "16", "$type": "sizing" },
    "icon-md": { "$value": "20", "$type": "sizing" },
    "icon-lg": { "$value": "24", "$type": "sizing" },
    "avatar-sm": { "$value": "32", "$type": "sizing" },
    "avatar-md": { "$value": "40", "$type": "sizing" },
    "avatar-lg": { "$value": "56", "$type": "sizing" }
  },
  "borderWidth": {
    "1": { "$value": "1", "$type": "borderWidth" },
    "2": { "$value": "2", "$type": "borderWidth" },
    "4": { "$value": "4", "$type": "borderWidth" }
  }
}
```

### Concrete Token Values — Semantic

```json
{
  "bg": {
    "body":    { "$value": "{color.white}", "$type": "color" },
    "surface": { "$value": "{color.gray.50}", "$type": "color" },
    "muted":   { "$value": "{color.gray.100}", "$type": "color" },
    "inverse": { "$value": "{color.gray.900}", "$type": "color" }
  },
  "txt": {
    "primary":   { "$value": "{color.gray.900}", "$type": "color" },
    "secondary": { "$value": "{color.gray.500}", "$type": "color" },
    "muted":     { "$value": "{color.gray.400}", "$type": "color" },
    "inverse":   { "$value": "{color.white}", "$type": "color" },
    "link":      { "$value": "{color.blue.600}", "$type": "color" },
    "danger":    { "$value": "{color.red.500}", "$type": "color" },
    "success":   { "$value": "{color.green.500}", "$type": "color" }
  },
  "border": {
    "default": { "$value": "{color.gray.200}", "$type": "color" },
    "strong":  { "$value": "{color.gray.300}", "$type": "color" },
    "focus":   { "$value": "{color.blue.500}", "$type": "color" },
    "danger":  { "$value": "{color.red.500}", "$type": "color" }
  },
  "action": {
    "primary-bg":      { "$value": "{color.blue.600}", "$type": "color" },
    "primary-fg":      { "$value": "{color.white}", "$type": "color" },
    "primary-hover":   { "$value": "{color.blue.800}", "$type": "color" },
    "secondary-bg":    { "$value": "{color.gray.100}", "$type": "color" },
    "secondary-fg":    { "$value": "{color.gray.800}", "$type": "color" },
    "secondary-hover": { "$value": "{color.gray.200}", "$type": "color" },
    "danger-bg":       { "$value": "{color.red.500}", "$type": "color" },
    "danger-fg":       { "$value": "{color.white}", "$type": "color" }
  },
  "radius": {
    "button": { "$value": "{borderRadius.md}" }, "card": { "$value": "{borderRadius.lg}" },
    "input":  { "$value": "{borderRadius.md}" }, "badge": { "$value": "{borderRadius.full}" },
    "modal":  { "$value": "{borderRadius.xl}" }
  },
  "spacing": {
    "xs": { "$value": "{dimension.1}" }, "sm": { "$value": "{dimension.2}" },
    "md": { "$value": "{dimension.4}" }, "lg": { "$value": "{dimension.6}" },
    "xl": { "$value": "{dimension.8}" }, "2xl": { "$value": "{dimension.12}" },
    "3xl": { "$value": "{dimension.16}" }
  },
  "font": {
    "family": {
      "body": { "$value": "{fontFamilies.sans}", "$type": "fontFamilies" },
      "heading": { "$value": "{fontFamilies.sans}", "$type": "fontFamilies" },
      "mono": { "$value": "{fontFamilies.mono}", "$type": "fontFamilies" }
    },
    "size": {
      "body": { "$value": "{fontSizes.base}", "$type": "fontSizes" },
      "caption": { "$value": "{fontSizes.xs}", "$type": "fontSizes" },
      "label": { "$value": "{fontSizes.sm}", "$type": "fontSizes" },
      "h1": { "$value": "{fontSizes.4xl}", "$type": "fontSizes" },
      "h2": { "$value": "{fontSizes.3xl}", "$type": "fontSizes" },
      "h3": { "$value": "{fontSizes.2xl}", "$type": "fontSizes" },
      "h4": { "$value": "{fontSizes.xl}", "$type": "fontSizes" }
    },
    "weight": {
      "body": { "$value": "{fontWeights.regular}", "$type": "fontWeights" },
      "heading": { "$value": "{fontWeights.bold}", "$type": "fontWeights" },
      "label": { "$value": "{fontWeights.medium}", "$type": "fontWeights" }
    }
  },
  "shadow": {
    "card": { "$value": "{shadow.sm}", "$type": "shadow" },
    "dropdown": { "$value": "{shadow.md}", "$type": "shadow" },
    "modal": { "$value": "{shadow.lg}", "$type": "shadow" }
  },
  "opacity": {
    "disabled": { "$value": "{opacity.medium}", "$type": "opacity" },
    "overlay": { "$value": "{opacity.strong}", "$type": "opacity" }
  },
  "sizing": {
    "icon-default": { "$value": "{sizing.icon-md}", "$type": "sizing" },
    "avatar-default": { "$value": "{sizing.avatar-md}", "$type": "sizing" }
  }
}
```

### Themes

Define at minimum light/dark:
```json
{ "themes": { "Mode": ["Light", "Dark"] } }
```

Dark mode overrides (semantic set):
```
bg/body       → Light: {color.white}       Dark: {color.gray.950}
bg/surface    → Light: {color.gray.50}     Dark: {color.gray.900}
txt/primary   → Light: {color.gray.900}    Dark: {color.gray.50}
txt/secondary → Light: {color.gray.500}    Dark: {color.gray.400}
border/default→ Light: {color.gray.200}    Dark: {color.gray.700}
```

---

## 5. Color Asset Registration

Register in Penpot assets panel → colors (what designers pick from the color picker). Name to map to CSS variables:

```
primitives/blue-50
primitives/blue-100
primitives/blue-200
...
primitives/gray-50
primitives/gray-100
...
semantic/bg-body
semantic/bg-surface
semantic/bg-muted
semantic/txt-primary
semantic/txt-secondary
semantic/txt-muted
semantic/txt-link
semantic/border-default
semantic/border-strong
semantic/border-focus
semantic/action-primary-bg
semantic/action-primary-fg
semantic/action-primary-hover
semantic/action-secondary-bg
semantic/action-secondary-fg
semantic/action-danger-bg
semantic/action-danger-fg
semantic/status-success
semantic/status-warning
semantic/status-danger
semantic/status-info
```

---

## 6. Typography Asset Registration

Register in assets panel → typographies:

```
heading/h1          → Inter 36px/1.2 weight 700
heading/h2          → Inter 30px/1.25 weight 700
heading/h3          → Inter 24px/1.3 weight 600
heading/h4          → Inter 20px/1.35 weight 600
heading/h5          → Inter 18px/1.4 weight 600
heading/h6          → Inter 16px/1.5 weight 600
body/lg             → Inter 18px/1.6 weight 400
body/md             → Inter 16px/1.6 weight 400
body/sm             → Inter 14px/1.5 weight 400
caption/default     → Inter 12px/1.5 weight 400
caption/strong      → Inter 12px/1.5 weight 500
label/default       → Inter 14px/1.4 weight 500
label/sm            → Inter 12px/1.4 weight 500
mono/default        → JetBrains Mono 14px/1.5 weight 400
mono/sm             → JetBrains Mono 12px/1.5 weight 400
overline/default    → Inter 11px/1.5 weight 600, uppercase, letter-spacing 0.05em
```

---

## 7. Naming Rules Summary

| Entity | Convention | Example |
|-|-|-|
| Page name | lowercase-hyphens | `atoms` |
| Frame name | slash-separated, lowercase-hyphens | `button/variants` |
| Component name | slash-separated, lowercase | `atoms/button/primary/default` |
| Variant property | camelCase key, lowercase value | `style: primary`, `size: md` |
| Color asset | slash-separated, lowercase-hyphens | `semantic/bg-body` |
| Typography asset | slash-separated, lowercase | `heading/h1` |
| Token name | slash-separated groups, lowercase-hyphens | `color/blue/500`, `bg/body` |
| Token set | lowercase | `primitives`, `semantic`, `component` |
| Theme axis | Capitalized | `Mode` |
| Theme value | Capitalized | `Light`, `Dark` |
| Layer names | descriptive, lowercase-hyphens | `hero-section`, `nav-item-label` |

### Rules

1. **No spaces** in machine-readable names. Use hyphens for multi-word segments.
2. **Slashes create hierarchy** in the assets panel. Use deliberately.
3. **Consistency over cleverness.** Same pattern depth for all items in a category.
4. **Semantic over visual.** Name by purpose (`action-primary-bg`) not appearance (`blue-600`).
5. **Annotations on every main component.** Primary documentation in Penpot.
6. **Use Penpot's native variant system** for multi-axis variations (style x size x state).
7. **Tokens reference other tokens** using `{curly.bracket.syntax}`. Semantic always references primitives.
8. **Every component must use Flex or Grid layout** — ensures usable CSS in Inspect mode.
9. **Cover page is mandatory** — version number + last updated + status.

---

## 8. Cover Page (File Metadata)

The cover page frame (1390x930, set as file thumbnail) must contain:

```
[Product Name] Design System
Version: [semver, e.g. 1.0.0]
Last updated: [YYYY-MM-DD]
Status: [Draft | Beta | Stable]

Changelog:
- v1.0.0: Initial release — foundations, atoms, molecules
- v1.1.0: Added organisms, landing page patterns
- v1.2.0: Dashboard screens, dark mode tokens

Component count: [N]
Token count: [N]
Pages: [N]
```

# UI Component Patterns Reference

Token-driven build recipes for every core component. Each recipe specifies structure (layout and layers), token bindings (surface, text, icon, border), and variant matrix.

## Token Quick Reference

| Role | Tokens |
|-|-|
| Surface | `surface/page`, `surface/default`, `surface/action`, `surface/action-hover`, `surface/action-hover-light`, `surface/disabled`, `surface/success`, `surface/warning`, `surface/error`, `surface/information` |
| Text | `text/heading`, `text/body`, `text/action`, `text/action-hover`, `text/on-action`, `text/disabled`, `text/success`, `text/error` |
| Icon | `icon/default`, `icon/action`, `icon/on-action`, `icon/disabled`, `icon/success`, `icon/error` |
| Border | `border/default`, `border/action`, `border/action-hover`, `border/focus`, `border/disabled`, `border/success`, `border/error` |

---

## Buttons

### Button

**Structure:** Auto layout horizontal → Icon Left (20x20, optional) + Label (text) + Icon Right (20x20, optional).

**Token bindings by type:**

| Type | Fill | Stroke | Text | Icon |
|-|-|-|-|-|
| Filled | `surface/action` | `border/action` | `text/on-action` | `icon/on-action` |
| Outline | transparent | `border/action` | `text/action` | `icon/action` |
| Transparent | none | none | `text/action` | `icon/action` |

**Variant matrix:** status (default / hover / focus / disabled) x type (filled / outline / transparent).

| Status | Surface change | Border change | Text/Icon change |
|-|-|-|-|
| Default | per type above | per type above | per type above |
| Hover | `surface/action-hover` (filled) or `surface/action-hover-light` (outline/transparent) | `border/action-hover` | `text/action-hover` (outline/transparent) |
| Focus | same as default + absolute-positioned rectangle with `border/focus` 2px | `border/focus` | unchanged |
| Disabled | `surface/disabled` | `border/disabled` | `text/disabled`, `icon/disabled` |

Always add the stroke even when it has the same color as the fill — it keeps dimensions consistent across type variants.

**Specs:** Min touch target 44x44px. Padding 12-16px horizontal, 8-12px vertical. Border radius 4-8px. Font weight semibold.

**Label patterns:** Use action verbs, 2-4 words (Save Changes, Add to Cart, Create Account).

### Button Icon

**Structure:** Square frame 44x44 → single icon centered (20x20 or 24x24).

**Tokens:** Same type variants as Button (filled / outline / transparent) with same token bindings. No label layer.

**Use for:** Close buttons, action icons, carousel navigation, table row actions.

### Button Group

**Structure:** Horizontal auto layout → multiple button group items sharing a continuous border. Inner items lose their individual border-radius (0 on adjacent sides). First item keeps left radius, last item keeps right radius.

**Tokens:** Each item follows Button token bindings. Selected item uses filled type, unselected items use outline or transparent type.

---

## Form Controls

### Label

**Structure:** Auto layout horizontal → label text.

**Tokens:** Text color `text/body`.

**Variants:**
- **Default** — plain label text.
- **Required** — adds a red asterisk (`*`) absolute-positioned to the left. Asterisk color: `text/error`.

### Input Field

**Structure:** Auto layout horizontal → Icon Left (20x20, optional) + Placeholder/Value text (fill width) + Icon Right (20x20, optional).

**Default tokens:** Fill `surface/default`, stroke `border/default`, text `text/body`, placeholder `text/disabled`, icon `icon/default`.

| Status | Fill | Stroke | Notes |
|-|-|-|-|
| Default | `surface/default` | `border/default` | — |
| Hover | `surface/action-hover-light` | `border/action-hover` | — |
| Focus | `surface/default` | `border/default` | Absolute-positioned rectangle with `border/focus` 2px |
| Disabled | `surface/disabled` | `border/disabled` | Text `text/disabled`, icon `icon/disabled` |
| Error | `surface/default` | `border/error` | Icon `icon/error`, hint text `text/error` |

### Input (Composed Molecule)

**Structure:** Vertical auto layout → Label component + Field component + Hint Text.

Use nested instances to expose Label and Field properties through the parent. Hint text layer is toggled via a layer property; hidden by default.

**Tokens:** Label follows Label recipe, Field follows Input Field recipe, Hint text uses `text/body` (or `text/error` when field is in error state).

### Text Area

**Structure:** Vertical auto layout → Label + multiline field + hint text.

Same as Input molecule but the field is multiline. No left icon (awkward with multiline content). Field is resizable vertically. Token bindings identical to Input Field.

### Checkbox

**Structure:** 20x20 rectangle (4px radius) → checkmark icon inside.

| Type | Fill | Stroke | Icon |
|-|-|-|-|
| Selected | `surface/action` | `border/action` (outside) | `icon/on-action` (checkmark) |
| Unselected | none | `border/default` (outside) | none |

**Variant matrix:** status (default / hover / focus / disabled) x type (selected / unselected).

Hover: stroke `border/action-hover`. Focus: additional `border/focus` ring. Disabled: `surface/disabled`, `border/disabled`.

**Checkbox Label molecule:** Horizontal auto layout → Checkbox + Label text, 8px gap. Expose the nested instances so the checkbox properties are editable from the molecule. Radio and Switch label molecules follow the same pattern.

### Radio Button

**Structure:** Outer ellipse 20x20 → inner ellipse 10x10 (centered, visible only when selected).

| Type | Outer fill | Outer stroke | Inner fill |
|-|-|-|-|
| Selected | `surface/default` | `border/action` | `surface/action` |
| Unselected | `surface/default` | `border/default` | hidden |

**Variant matrix:** Same as Checkbox (status x type). Token state changes mirror Checkbox.

**Radio Label molecule:** Horizontal auto layout → Radio + Label text, 8px gap.

### Switch / Toggle

**Structure:** Pill-shaped container (auto layout) → circle knob inside.

| State | Container fill | Container stroke | Knob fill |
|-|-|-|-|
| On | `surface/action` | `border/action` | `icon/on-action` (knob positioned right) |
| Off | `surface/default` | `border/default` | `icon/default` (knob positioned left) |

Disabled: container `surface/disabled`, stroke `border/disabled`, knob `icon/disabled`.

### Validation & Error Guidelines

- **On blur:** Validate when user leaves field.
- **On change (after error):** Clear error as user types correct input.
- **On submit:** Final validation before processing.
- **Never on focus:** Do not show errors before user types.

Error messages should be specific: "Email address is required", not "Invalid input".

### Form Layout

- Single column preferred — reduces cognitive load.
- Top-aligned labels — fastest completion times.
- Logical grouping — related fields together.
- Mark optional fields, not required (fewer asterisks).
- Preserve data on errors (do not clear the form).

---

## Navigation

### Tab Item (internal .tab-item)

**Structure:** Auto layout horizontal → Icon Left (optional) + Label text.

| Type | Border bottom | Text | Font weight |
|-|-|-|-|
| Selected | 2px `border/action` | `text/action` | Semibold |
| Unselected | none | `text/body` | Regular |

**Variant matrix:** status (default / hover / focus / disabled) x type (selected / unselected).

Hover (unselected): text `text/action-hover`, background `surface/action-hover-light`.

### Tab Bar

**Structure:** Horizontal auto layout → multiple .tab-item instances.

One item is selected at a time. A full-width 1px border bottom `border/default` sits behind the items; the selected item's `border/action` bottom overlaps it.

### Menu Item (internal .menu-item)

**Structure:** Auto layout horizontal → Icon Left (optional) + Label (fill width) + Icon Right (optional). 1px border bottom `border/default` as separator.

**Tokens:** Fill `surface/default`, text `text/body`, icon `icon/default`.

| Status | Fill | Text | Icon |
|-|-|-|-|
| Default | `surface/default` | `text/body` | `icon/default` |
| Hover | `surface/action-hover-light` | `text/body` | `icon/default` |
| Selected | `surface/action-hover-light` | `text/action` | `icon/action` |
| Disabled | `surface/disabled` | `text/disabled` | `icon/disabled` |

Stronger selected variant (when selection must read at a glance, e.g. a single-select list): fill `surface/action`, text `text/on-action`, icon `icon/on-action`.

### Menu

**Structure:** Vertical auto layout → multiple .menu-item instances + optional scrollbar. Border radius 8px, fill `surface/default`, stroke `border/default`.

Elevation: shadow layer for dropdown appearance.

### Link

**Structure:** Auto layout horizontal → Icon Left (optional) + Label (underlined text) + Icon Right (optional).

**Tokens:** Text `text/action`, icon `icon/action`. Hover: `text/action-hover`. Visited state optional.

**Breadcrumb variant:** Multiple Link instances separated by chevron icons. Max ~6 items. Current (last) item is not clickable, styled with `text/body` and no underline.

```text
Link > Link > Link > Current Page
```

### Navigation Layout Patterns

**Top bar:** Logo + nav items + utility icons. Best for marketing sites, simple apps. Max 5-7 top-level items. Collapse to hamburger on mobile.

**Sidebar:** 200-280px expanded, 64px collapsed. Best for dashboards, complex apps. Mobile: overlay drawer.

**Bottom bar (mobile):** 3-5 primary destinations, always visible, persistent.

---

## Data Display

### Avatar

**Structure:** Circle frame, fill `surface/default`, `border-radius/full`.

**Types:**
- **Icon** — centered user icon, `icon/default`.
- **Image** — clipped image fills frame.
- **Initials** — 2-character text centered, `text/body`.

**Sizes:** Large 64x64, Medium 48x48, Small 32x32 — set with scale constraints so the content scales with the frame.

**Avatar Group:** Horizontal auto layout with negative gap (-4px) for overlap. Avatars stack with z-index. Ends with a count badge showing "+N" remaining.

### Tag / Chip

**Structure:** Auto layout horizontal → Icon Left (optional) + Label + Close Icon (optional).

| Type | Fill | Stroke | Text | Icon |
|-|-|-|-|-|
| Unselected | none | dashed `border/default` | `text/body` | `icon/default` |
| Selected | `surface/action` | solid `border/action` | `text/on-action` | `icon/on-action` |

Close icon visible on hover or always, depending on use case.

### Badge

**Structure:** Fixed circle 24x24, `border-radius/full`.

**Types:**
- **Count** — displays a number, text centered.
- **Dot** — 12x12, no text (notification indicator).

**Semantic variants:**

| Variant | Fill |
|-|-|
| Default | `surface/action` |
| Success | `surface/success` |
| Error | `surface/error` |
| Warning | `surface/warning` |
| Information | `surface/information` |

Text on all variants: `text/on-action`.

### Table

The most complex component. Built in three layers:

**1. Cell Item:** Frame containing text, icon, link, or other content. Type variants control content (text cell, icon cell, link cell, action cell with button icon).

**2. Column:** Vertical auto layout → header cell + data cells stacked. Header cell: fill `surface/action-hover-light`, text `text/heading` semibold. Data cells: fill `surface/default`, text `text/body`. Bottom border `border/default` on each cell as row separator.

**3. Table:** Horizontal auto layout → multiple Column instances. Use gap-adjustment trick for resizable columns (each column set to fill width). Outer stroke `border/default`. Expose nested instances so cell content is customizable from the table level.

---

## Feedback

### Loader / Spinner

**Structure:** Frame with ellipses arranged in a circle pattern. Animated rotation.

**Tokens:** Ellipses use `surface/action` with varying opacity for animation effect.

**Sizes:** Large 64x64, Medium 48x48, Small 32x32.

### Progress Bar

**Structure:** Vertical auto layout → Label (optional) + bar frame.

Bar frame: background track fill `surface/action-hover-light`, progress fill `surface/action`. Progress width is percentage-based.

**Progress Circle variant:** Donut chart (ring) with center percentage text. Track ring `surface/action-hover-light`, progress ring `surface/action`, text `text/heading`.

### Snackbar / Toast

**Structure:** Auto layout horizontal → Icon + Content (title + description + link) + Close button (button icon).

**Default tokens:** Fill `surface/default`, stroke `border/default`, text `text/heading` (title) + `text/body` (description), icon `icon/default`.

**Semantic variants:**

| Variant | Surface | Icon color |
|-|-|-|
| Success | `surface/success` | `icon/success` |
| Error | `surface/error` | `icon/error` |
| Warning | `surface/warning` | `icon/default` |
| Information | `surface/information` | `icon/default` |

Optional progress bar absolute-positioned at bottom of snackbar (auto-dismiss timer visualization).

---

## Containers

### Cards

**Structure:** Vertical auto layout → Image/Media slot (optional) + Content area (padding 16-24px) containing category label + title + description + action buttons.

**Tokens:** Fill `surface/default`, stroke `border/default`, border-radius 8-12px. Title `text/heading`, description `text/body`, category label `text/action`.

Shadow: subtle elevation for layered appearance.

**Guidelines:**
- Consistent sizing via grid, equal heights.
- Content hierarchy: Image, Title, Description, Actions.

### Modals and Dialogs

**Structure:** Vertical auto layout → Header (title + close button icon) + Content area + Footer (action buttons right-aligned).

**Tokens:** Fill `surface/default`, overlay behind modal uses semi-transparent dark layer. Title `text/heading`, body `text/body`. Close button follows Button Icon recipe. Primary action button: filled type. Secondary: outline type.

**Specs:** Width 400-600px desktop, full-width minus margins mobile. Close via X button, overlay click, or Escape key. Keyboard focus trap required.

### Carousel

**Structure:** Auto layout → .carousel-item cards (horizontal scroll or swipe) + navigation arrows (button icon, left/right) + progress indicator bar with sliding segment.

Navigation arrows use Button Icon recipe. Progress bar track `surface/action-hover-light`, active segment `surface/action`.

---

## Page-Level Patterns

### Dashboards

**Layout principles:**
1. Most important metrics at top (KPIs, summary cards).
2. Progressive detail — overview to drill-down.
3. Consistent card sizes via grid system.
4. Minimal chart decoration — only data-serving visuals.
5. Actionable insights — highlight anomalies.

**Token usage:** KPI cards use `surface/default` fill, metric numbers `text/heading`, trend indicators use semantic colors (`text/success` for positive, `text/error` for negative). Filter controls and date range selectors should be prominent, using outline Button type.

**Data visualization selection:**

| Data type | Chart type |
|-|-|
| Comparison across categories | Bar chart |
| Trend over time | Line chart |
| Part of whole | Pie (max 5 slices) or Donut |
| Distribution | Histogram |
| Correlation | Scatter plot |
| Geographic | Map |
| Single metric | Big number + sparkline |

Limit 5-9 widgets per view. Stack cards on smaller screens.

### Empty States

**Structure:** Centered vertical auto layout → Illustration/Icon + Heading + Description (1-2 sentences) + CTA button.

**Tokens:** Heading `text/heading`, description `text/body`, illustration/icon `icon/disabled` or custom. CTA follows filled Button recipe.

**Guidelines:** Explain value (why create something?), not just "No data". Keep brief.

### Loading States

| Duration | Pattern |
|-|-|
| < 1 second | No indicator (feels instant) |
| 1-3 seconds | Spinner (Loader component) |
| 3-10 seconds | Skeleton screens + progress |
| > 10 seconds | Progress Bar + explanation text |

**Skeleton screens:** Match layout of loaded content. Use `surface/action-hover-light` for placeholder shapes with subtle shimmer/pulse animation on `surface/default` background.

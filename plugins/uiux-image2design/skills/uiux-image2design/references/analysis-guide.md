# Screenshot Analysis Guide

Systematic methodology for extracting design system information from UI screenshots using
Claude's vision capabilities. This guide ensures consistent, thorough extraction regardless
of the source material.

## Mindset: The Core Directive

Before starting any analysis, internalize this instruction:

> **"Deeply analyze the design of the attached screenshot to create a design system layout
> of every UI component needed in a design system for a SaaS product service. Pay close
> attention to spacing, fonts, colors, design styles and design principles."**

This prompt (from Sergei Chyrkov's screenshot-to-design-system workflow) captures the
essential stance: you are not writing an art critique — you are **reverse-engineering a
buildable system**. Every visual detail you extract must translate into either a token
(color, size, spacing, shadow) or a component (button, card, input, navigation).

Ask yourself for every observation: *"Can I turn this into a Penpot shape with specific
fill, size, font, radius, and spacing values?"* If not, keep looking until the observation
is concrete enough to build from.

## Analysis Order

Always analyze in this order — each step informs the next:

1. **Initial Assessment** — platform, design language, density, color mode
2. **Color Palette** — extract all distinct colors by role
3. **Typography** — identify all text styles
4. **Spacing** — detect base unit and spacing scale
5. **Layout Structure** — grid system, content hierarchy, section mapping
6. **Border Radius** — catalog radius values
7. **Shadows & Depth** — elevation strategy, shadow values, border treatments
8. **Component Inventory** — catalog every UI component with measurements
9. **Iconography** — icon style and sizing
10. **Special Patterns** — gradients, glassmorphism, textures, etc.

After all phases: **Gaps & Confidence** (mandatory) and **Quality Checklist**.

## 1. Initial Assessment

Before extracting any tokens, establish the context. This determines defaults for later
phases (e.g., platform affects touch targets, density affects spacing, color mode affects
which colors are "background" vs "surface").

**Identify and document:**

| Attribute | What to Determine |
|-|-|
| Platform | Mobile (iOS/Android), web (desktop/responsive), desktop app |
| Design language | Material Design, iOS HIG, custom, hybrid |
| Layout approach | Single column, multi-column, sidebar+content, dashboard grid |
| Density | Compact (data-heavy), comfortable (standard), spacious (marketing) |
| Color mode | Light, dark, or mixed |
| Apparent era | Current trends (2024+), dated patterns, or deliberately retro |

**Required output:**

```
INITIAL ASSESSMENT:
  Platform:        [platform]
  Design language: [language]
  Layout:          [approach]
  Density:         [compact / comfortable / spacious]
  Color mode:      [light / dark / mixed]
  Notes:           [anything notable — e.g. "glassmorphism elements", "data-dense dashboard",
                    "marketing page with illustration-heavy hero"]
```

This assessment feeds downstream decisions:
- **Platform** → touch target minimums, safe areas, navigation patterns
- **Density** → spacing scale expectations (compact uses tighter spacing)
- **Color mode** → which colors are "base" backgrounds, how shadows behave
- **Design language** → expected component patterns and radius conventions

**Visual style classification** (identify which applies):
- Minimal/clean — lots of whitespace, limited color
- Dark mode — dark backgrounds, light text, accent colors
- Glassmorphism — frosted glass effects, transparency
- Neubrutalism — bold borders, raw shapes, bright colors
- Corporate/enterprise — conservative, professional, data-dense
- Playful — rounded shapes, bright colors, illustrations

**Design era indicators:**
- Large border radius (12px+) → 2022+ trends
- Subtle shadows with low spread → modern elevation
- Monochrome with single accent → minimal trend
- Gradient backgrounds → still current but watch for specifics

## 2. Color Extraction

### Method

Scan the screenshot in this order:
1. **Background colors** — page background, card backgrounds, section backgrounds
2. **Text colors** — primary text, secondary/muted text, heading text, link text
3. **Accent/brand colors** — buttons, highlights, active states, progress bars
4. **Border colors** — dividers, card borders, input borders
5. **Feedback colors** — error red, success green, warning yellow, info blue
6. **Overlay colors** — modal backdrops, tooltip backgrounds

### Extraction Rules

- **Extract the actual hex value you see.** Don't normalize to a standard palette unless asked.
  If the green is `#A3E635` (lime), report that — don't round to `#22C55E` (Tailwind green-500).

- **Note opacity separately.** If a color appears to have transparency (e.g. a semi-transparent
  overlay), report it as: "Background overlay: #000000 at approximately 50% opacity"

- **Identify color relationships.** Note when colors appear to be tints/shades of the same hue.
  This suggests a scale: "Primary appears to have at least 3 stops: ~#1B3C2D (dark), ~#2D5A42
  (medium), ~#A3E635 (accent/light)"

- **Count unique colors.** A well-designed UI typically uses 5–12 distinct colors.
  If you're finding 20+, you're likely picking up slight variations — group them.

### Output Format

```
### Color Palette

| # | Color | Hex | Usage | Suggested Token |
|-|-|-|-|-|
| 1 | Dark forest green | #1B3C2D | Page background, card backgrounds | color.neutral.900 |
| 2 | Medium green | #2D5A42 | Secondary backgrounds, borders | color.neutral.700 |
| 3 | Lime green | #A3E635 | CTAs, progress bars, active states | color.primary.500 |
| 4 | White | #FFFFFF | Headings, primary text | color.neutral.50 |
| 5 | Gray | #9CA3AF | Secondary text, placeholders | color.neutral.400 |
| 6 | Dark border | #2D4A3A | Card borders, dividers | color.neutral.600 |
```

## 3. Typography Extraction

### Method

Identify every distinct text style visible in the screenshots. Look for differences in:
- Size (estimate in px by comparing to known elements like nav bars, buttons)
- Weight (thin, regular, medium, semibold, bold, black)
- Family (serif, sans-serif, monospace — try to identify the specific font)
- Case treatment (normal, UPPERCASE, Capitalize)
- Letter spacing (tight/compressed, normal, wide/tracked)
- Color (usually handled in color section, but note if a style always pairs with a color)

### Font Identification Tips

**Geometric sans-serif** (circular shapes, even stroke width):
- Inter — very slightly narrower, slightly squared
- Poppins — rounder, slightly wider
- Geist — similar to Inter but with distinctive 't' and 'a'
- Nunito — very round, friendly

**Humanist sans-serif** (varied stroke width, calligraphic hints):
- Open Sans — neutral, slightly wide
- Source Sans — slightly narrower, professional
- Lato — semicircular, warm

**Neo-grotesque** (very uniform, minimal personality):
- Helvetica/Arial — the default baseline
- Roboto — Android default, slightly wider than Helvetica
- SF Pro — Apple system font, similar to Helvetica but optimized

**Monospace:**
- JetBrains Mono — ligatures, slightly wide
- Fira Code — ligatures, narrower
- SF Mono — Apple mono, clean

If you can't confidently identify the font, describe its characteristics and suggest 2–3
candidates. The user can confirm in Phase 2.

### Size Estimation

Use known reference points to estimate sizes:
- Mobile status bar text: ~12px
- Mobile body text: ~16px
- Mobile nav bar title: ~17–20px
- Desktop body text: ~14–16px
- Desktop H1: ~32–48px
- Button labels: ~14–16px
- Caption/helper text: ~12px

### Output Format

```
### Typography

| # | Style | Family | Size | Weight | Case | Tracking | Usage |
|-|-|-|-|-|-|-|-|
| 1 | Display | Inter (or similar) | ~32px | Bold (700) | Normal | Tight | Page titles |
| 2 | Heading | Inter | ~24px | Semibold (600) | Normal | Tight | Section headers |
| 3 | Body | Inter | ~16px | Regular (400) | Normal | Normal | Main content |
| 4 | Caption | Inter | ~12px | Medium (500) | Uppercase | Wide | Labels, metadata |
| 5 | Button | Inter | ~14px | Semibold (600) | Uppercase | Normal | Button labels |
```

## 4. Spacing Measurement

### Method

1. **Find the base unit.** Examine the smallest repeated spacing value. Common bases:
   4px (fine-grained), 8px (standard). Look at icon-to-text gaps, input padding, and
   tight element pairs.
2. **Internal component spacing.** Padding inside buttons, cards, inputs, list items.
3. **Between-element spacing.** Gaps between sibling elements (button groups, form fields,
   list items).
4. **Section spacing.** Distance between major content sections.
5. **Page margins.** Outer padding of the main content area.
6. **Consistent vs. inconsistent.** Note whether spacing follows a strict scale or varies.

### Output Format

```
SPACING:
  Base unit: [N]px

  Scale:
    2xs:  [N]px  ([base] × [multiplier]) — used for: [context]
    xs:   [N]px  ([base] × [multiplier]) — used for: [context]
    sm:   [N]px  ([base] × [multiplier]) — used for: [context]
    md:   [N]px  ([base] × [multiplier]) — used for: [context]
    lg:   [N]px  ([base] × [multiplier]) — used for: [context]
    xl:   [N]px  ([base] × [multiplier]) — used for: [context]
    2xl:  [N]px  ([base] × [multiplier]) — used for: [context]

  Component padding:
    Buttons:     [top] [right] [bottom] [left]
    Cards:       [top] [right] [bottom] [left]
    Inputs:      [top] [right] [bottom] [left]
    List items:  [top] [right] [bottom] [left]

  Gap patterns:
    Form fields:    [N]px between fields
    Button groups:  [N]px between buttons
    Section gap:    [N]px between major sections
```

## 5. Layout Structure

Dedicated analysis of spatial organization. This feeds directly into Phase 5 (Sample Screen
Generation) — without it the agent would have to re-analyze the screenshots later.

### Method

1. **Grid system.** Identify columns, gutters, and margins. Note whether a standard grid
   (12-column) or custom layout is used.
2. **Section mapping.** Divide the interface into named sections (header, sidebar, main
   content, footer, etc.) with approximate dimensions.
3. **Content hierarchy.** Rank content areas by visual prominence — what draws the eye first,
   second, third? Note what creates that hierarchy (size, color, contrast, position, whitespace).
4. **Alignment axes.** Identify the dominant alignment pattern (left-aligned, center-aligned,
   mixed). Note any deliberate breaks.
5. **Content density per section.** Sparse, moderate, or dense — this varies within a screen.

### Output Format

```
LAYOUT STRUCTURE:
  Grid:
    Type:      [fixed / fluid / hybrid]
    Columns:   [N]
    Gutter:    ~[N]px
    Margin:    ~[N]px
    Max width: ~[N]px (if constrained)

  Section map:
    [Section name]: [position, ~dimensions, role]
    [Section name]: [position, ~dimensions, role]
    ...

  Visual hierarchy (reading order):
    1. [Element/area] — draws attention via [mechanism]
    2. [Element/area] — secondary focus via [mechanism]
    3. [Element/area] — tertiary via [mechanism]

  Alignment:
    Primary axis: [left / center / mixed]
    Notable breaks: [any deliberate alignment breaks]

  Content density:
    [Section]: [sparse / moderate / dense]
```

## 6. Border Radius

### Method

Look at every element with rounded corners and estimate the radius. Group by usage:

### Output Format

```
### Border Radius

| Value | Where | Suggested Token |
|-|-|-|
| 0px | None detected | radius.none |
| 4px | Input fields, small badges | radius.s |
| 8px | Buttons, dropdowns | radius.m |
| 12px | Cards, modals | radius.l |
| 9999px | Avatars, tags, pills | radius.full |
```

## 7. Shadows & Depth Strategy

### Method

First, classify the **overall depth strategy** — this prevents generating shadows for a
UI that relies on borders, or vice versa:

| Strategy | Characteristics |
|-|-|
| Borders only | No shadows. Depth conveyed via border color, background shifts. Common in minimal/flat UIs. |
| Subtle shadows | Light, small shadows on cards and elevated elements. Modern default. |
| Layered shadows | Multiple shadow levels creating clear elevation hierarchy. Material-like. |
| Surface shifts | Depth via background color differences rather than shadows or borders. Common in dark UIs. |

Then extract specifics:
- Drop shadows on cards, buttons, dropdowns
- Inner shadows on inputs or inset elements
- Blur effects (background blur / glassmorphism)
- Border-based elevation (using border color to simulate depth)
- Divider patterns — how are sections separated? (borders, spacing, background, shadows)

Note: many modern UIs use minimal or no shadows, relying on borders and background
color differences for depth. This is valid — note it if that's the case.

### Output Format

```
DEPTH STRATEGY: [borders-only / subtle-shadows / layered-shadows / surface-shifts]

Shadows:
  Level 1 (subtle):   [offset-x] [offset-y] [blur] [spread] [color] — used for: [context]
  Level 2 (medium):   [offset-x] [offset-y] [blur] [spread] [color] — used for: [context]
  Level 3 (elevated): [offset-x] [offset-y] [blur] [spread] [color] — used for: [context]

Border treatments:
  Default:  [width] [style] [color] — used for: [context]
  Subtle:   [width] [style] [color] — used for: [context]
  Strong:   [width] [style] [color] — used for: [context]

Elevation map:
  Level 0: [elements at base level]
  Level 1: [elements floating above base]
  Level 2: [elements above level 1]
  Level 3: [highest elevation — modals, dropdowns]

Divider pattern: [how sections are separated — borders, spacing, background shifts, etc.]
```

## 8. Component Inventory

### Method

Scan the screenshots and catalog every distinct UI component. A component is a reusable
UI element with consistent visual treatment.

**Identification checklist:**
- [ ] Buttons (how many variants? primary, secondary, ghost, icon-only, destructive?)
- [ ] Text inputs (with labels? with icons? with clear button?)
- [ ] Select/dropdown (custom styled or native?)
- [ ] Checkbox
- [ ] Radio button
- [ ] Toggle/switch
- [ ] Cards (how many types? content card, metric card, list card?)
- [ ] Navigation bar (top? bottom? sidebar?)
- [ ] Tabs
- [ ] Badges/tags/chips
- [ ] Avatars
- [ ] Progress bars
- [ ] Tooltips
- [ ] Modals/dialogs
- [ ] Toast/snackbar notifications
- [ ] Lists/list items
- [ ] Dividers/separators
- [ ] Search bar
- [ ] Breadcrumbs
- [ ] Pagination

**For each component, note:**
- How many visual variants are visible
- Which states are visible (default, hover, active, disabled, error, loading)
- Which states are NOT visible but will need to be designed
- Any distinctive characteristics (unusual shape, animation hint, etc.)

### Output Format

```
### Component Inventory

| # | Component | Variants Detected | States Visible | States Needed | Notes |
|-|-|-|-|-|-|
| 1 | Button | Primary, Secondary, Ghost | Default only | Hover, Active, Focus, Disabled | Lime bg for primary, outline for secondary |
| 2 | Text Input | Standard, With Icon | Default, Filled | Focus, Error, Disabled | Dark bg, subtle border, placeholder text visible |
| 3 | Toggle Switch | — | On, Off | Disabled | Lime green for "on" state |
| 4 | Metric Card | — | Default | Hover (if interactive) | Icon + number + label pattern |
| 5 | Progress Bar | — | Partial fill | Complete, Empty | Lime fill on dark track |
| 6 | Bottom Nav | — | Active, Inactive | — | 5 items, icon + label |
| 7 | Checklist Item | — | Checked, Unchecked | — | Checkbox + text, swipe hint |
```

## 9. Iconography

### Method

If icons are visible, characterize:
- **Style:** Outlined (stroke only), Filled (solid), Duotone (two-tone)
- **Weight:** Thin (1px stroke), Regular (1.5px), Bold (2px+)
- **Size:** Typically 16px, 20px, or 24px
- **Set identification:** If you recognize the icon set (Lucide, Heroicons, Material Symbols,
  Phosphor, Tabler, Feather), note it. If not, describe the style.

### Output Format

```
### Iconography

- **Style:** Outlined, regular weight (~1.5px stroke)
- **Size:** ~20px in navigation, ~24px in cards
- **Set:** Appears to be Lucide or similar (simple, geometric, consistent stroke)
- **Color:** Uses text color tokens (white for primary, gray for secondary)
```

## 10. Special Patterns

Note anything that doesn't fit the above categories:

- **Gradients** — direction, color stops, where used
- **Glassmorphism** — backdrop blur value, background opacity
- **Textures/patterns** — background textures, noise overlays
- **Illustrations** — style (flat, isometric, hand-drawn), where used
- **Image treatment** — rounded, with overlay, aspect ratio
- **Animations** — any motion hints (e.g. skeleton loading states visible)
- **Dark/light mode** — are both modes visible in the screenshots?

## Multi-Screenshot Cross-Reference

When analyzing multiple screenshots:

1. **Identify the primary screenshot** — the one with the most components visible.
   Use it as the source of truth for color and typography.

2. **Cross-validate consistency.** Compare colors, sizes, and spacing across screenshots.
   Note discrepancies: "Screenshot 1 uses 8px button radius, Screenshot 3 uses 12px"

3. **Merge component inventories.** Some components may only appear in one screenshot.
   Combine them into a single unified inventory.

4. **Note responsive variations.** If screenshots show the same UI at different sizes,
   note how layout adapts (sidebar collapses, grid stacks, etc.)

5. **Prioritize the most complete screenshot** for ambiguous values. If one screenshot
   is higher quality or shows more detail, prefer its values.

---

## Gaps & Confidence (MANDATORY)

Every analysis MUST end with an honest gaps section. This feeds directly into Phase 2
(User Confirmation) — the user needs to see what's unknown so they can provide answers.

**Never fabricate values for gaps.** State what is unknown and suggest how to obtain the
missing information.

### Required Output Format

```
KNOWN GAPS:
  Cannot determine from static screenshot:
  - [ ] Hover states for [components]
  - [ ] Focus ring style and color
  - [ ] Active/pressed states for [components]
  - [ ] Disabled state appearance
  - [ ] Animation/transition properties
  - [ ] Responsive breakpoint behavior
  - [ ] Touch target sizes (if mobile, cannot measure precisely)
  - [ ] Scroll behavior (sticky headers, parallax, etc.)
  - [ ] Loading/skeleton states
  - [ ] Empty states
  - [ ] Error states for [components]
  - [ ] [Other gaps specific to this screenshot]

  Low confidence extractions (flagged for user review):
  - [ ] [Item] — [reason for low confidence]
  - [ ] [Item] — [reason for low confidence]

  Suggested next steps:
  - [How to obtain missing info — e.g. "provide additional screenshots showing hover states",
    "inspect the live app", "confirm font family"]
```

## Common Mistakes

Avoid these during analysis — they lead to unusable output:

| Mistake | Fix |
|-|-|
| Guessing hex values without acknowledging approximation | Prefix all sizes with `~`; note confidence for colors |
| Extracting colors without assigning roles | Every color must have a named role (background, text, border, accent) |
| Listing components without measuring them | Every component needs dimensions, padding, radius, and color values |
| Ignoring the spacing system | Find the base unit first; express all spacing as multipliers |
| Skipping the gaps section | Always document what cannot be determined from a static image |
| Treating all text sizes as a flat list | Organize into a named hierarchy (Display, H1, H2, Body, Caption) |
| Extracting shadows without noting depth strategy | Classify the overall approach before listing individual values |
| Providing vague font identification | State confidence level; suggest closest known match |
| Inventing hover/focus/disabled states | Only document states that are *visible*. Mark missing states as gaps. |
| Assuming Inter for every sans-serif | Look at character shapes. State confidence. Suggest 2–3 candidates. |

## Quality Checklist

Before delivering the analysis to the user (Phase 2), verify:

**Completeness:**
- [ ] Initial Assessment documents platform, language, density, color mode
- [ ] Color palette organized by role with `(observed in: ...)` attributions
- [ ] Typography scale uses named hierarchy levels with confidence on font family
- [ ] Spacing identifies base unit and expresses values as multipliers
- [ ] Layout structure includes grid, section map, and visual hierarchy
- [ ] Border radius values cataloged with usage contexts
- [ ] Depth strategy classified; shadows/borders documented accordingly
- [ ] Every visible component cataloged with measurements
- [ ] Iconography characterized (or noted as absent)
- [ ] Special patterns documented (or noted as absent)

**Precision:**
- [ ] All colors include hex values
- [ ] All sizes include pixel estimates with `~` where approximate
- [ ] Font families include confidence level (high/medium/low)
- [ ] Component specs include dimensions, padding, radius, and colors
- [ ] Spacing values traceable to base unit multipliers

**Honesty:**
- [ ] Gaps section present and populated
- [ ] No fabricated hover/animation/responsive values
- [ ] Low-confidence extractions flagged
- [ ] Missing component states explicitly listed in gaps
- [ ] Discrepancies between screenshots noted

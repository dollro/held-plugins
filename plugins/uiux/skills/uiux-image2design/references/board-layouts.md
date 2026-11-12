# Board Layouts Reference

Standard board dimensions, positioning conventions, and layout patterns for the
design-from-screenshots workflow.

## Page-to-Board Mapping

Page structure follows `penpot-design-system-guide.md`. Boards within each page:

```
cover              → version-info (1390×930)
foundations        → colors/primitives, colors/semantic, colors/dark-mode,
                     typography/scale, typography/pairings,
                     spacing/scale, spacing/grid, elevation/levels, icons/grid
atoms              → button/variants, button/anatomy, input/variants, input/anatomy,
                     badge/variants, avatar/variants, toggle/variants, ...
molecules          → form-field/variants, card/variants, nav-item/variants,
                     dropdown-select/variants, toast-alert/variants, ...
organisms          → header-navbar/variants, header-navbar/responsive,
                     data-table/variants, modal-dialog/variants, ...
patterns           → layout/sidebar-content, section-hero/variant-a,
                     state-empty/default, state-loading/default, ...
screens-*          → {context}/desktop, {context}/mobile
                     (e.g. landing/desktop, dashboard/main)
```

Not all pages required. Create based on Confirmed Spec. Minimum: cover, foundations, atoms, one screens-* page.

## Board Positioning

For board positioning (horizontal flow with 100px gaps) and page navigation code,
see `uiux-design-penpot/SKILL.md` → "Positioning New Boards" and "Page, Viewport & Events".

## Design System Board Dimensions

| Board | Width | Height | Notes |
|-|-|-|-|
| Colors | 600–900px | Dynamic | Based on number of colors; ~100px per row of 6 swatches |
| Typography | 800px | Dynamic | ~60–80px per text style |
| Spacing | 600px | Dynamic | ~48px per spacing value |
| Border Radius | 600px | Dynamic | ~80px per radius value |
| Shadows | 600px | Dynamic | ~120px per elevation level |

### Colors Board Layout

```
+------------------------------------------------------+
| Colors                                               |  Board: 800 × dynamic
+------------------------------------------------------+
|                                                      |
| PRIMITIVES                                           |  Section header
| +----+ +----+ +----+ +----+ +----+ +----+            |
| | 50 | |100 | |200 | |300 | |400 | |500 |            |  Row 1: Neutral scale
| +----+ +----+ +----+ +----+ +----+ +----+            |
| +----+ +----+ +----+ +----+ +----+ +----+            |
| |600 | |700 | |800 | |900 | |950 | |    |            |  Row 2: Neutral cont.
| +----+ +----+ +----+ +----+ +----+ +----+            |
|                                                      |
| +----+ +----+ +----+ +----+ +----+ +----+            |
| | 50 | |100 | |200 | |300 | |400 | |500 |            |  Primary scale
| +----+ +----+ +----+ +----+ +----+ +----+            |
|                                                      |
| SEMANTIC                                             |  Section header
| +----+ +----+ +----+ +----+ +----+ +----+            |
| | BG | | BG | |Text| |Text| |Bord| |Actv|            |  Semantic colors
| |Surf| |Prim| |Prim| | Sec| | Def| | Def|            |
| +----+ +----+ +----+ +----+ +----+ +----+            |
|                                                      |
| FEEDBACK                                             |
| +----+ +----+ +----+ +----+                          |
| |Succ| |Warn| |Dang| |Info|                          |  Feedback colors
| +----+ +----+ +----+ +----+                          |
+------------------------------------------------------+

Swatch: 64×64px, 16px gap, 6 per row
Section header: 20px Inter Bold, 24px gap below
Board padding: 24px all sides
```

### Typography Board Layout

```
+------------------------------------------------------+
| Typography                                           |  Board: 800 × dynamic
+------------------------------------------------------+
|                                                      |
| Display — Inter Bold / 48px / 1.25                   |  Meta line (12px, gray)
| Display Heading Text                                 |  Sample (actual size)
|                                                      |  48px gap
| H1 — Inter Bold / 36px / 1.25                        |
| Heading Level One                                    |
|                                                      |
| H2 — Inter Semibold / 24px / 1.25                    |
| Heading Level Two                                    |
|                                                      |
| Body — Inter Regular / 16px / 1.5                    |
| Body text for main content areas and paragraphs.     |
| This sample shows how running text appears at the    |
| default body size.                                   |
|                                                      |
| Caption — Inter Medium / 12px / 1.5 / UPPERCASE      |
| CAPTION TEXT FOR LABELS AND METADATA                 |
|                                                      |
+------------------------------------------------------+

Meta line: 12px Inter Regular, #9CA3AF
Sample text: actual font size/weight/color
Row gap: max(fontSize + 32, 48)px
Board padding: 32px all sides
```

## Component Board Dimensions

| Board | Width | Height | Notes |
|-|-|-|-|
| Buttons | 800–1000px | Dynamic | 4 states × N variants; ~80px per variant row |
| Form Inputs | 800px | Dynamic | 4 states × input types; ~120px per input type |
| Cards | 800px | Dynamic | Based on card count and size |
| Navigation | Device width | Component height | Varies by nav type |

### Component Board Layout Pattern

All component boards follow the same structure: **variant rows × state columns**.

```
+--------------------------------------------------------------------+
| Component Name                                                     |
+--------------------------------------------------------------------+
|                                                                    |
|           DEFAULT      HOVER        ACTIVE       DISABLED          |  State headers
|                                                                    |
| PRIMARY   +--------+  +--------+  +--------+  +--------+           |
|           | Button |  | Button |  | Button |  | Button |           |  Variant row 1
|           +--------+  +--------+  +--------+  +--------+           |
|                                                                    |
| SECONDARY +--------+  +--------+  +--------+  +--------+           |
|           | Button |  | Button |  | Button |  | Button |           |  Variant row 2
|           +--------+  +--------+  +--------+  +--------+           |
|                                                                    |
| GHOST     +--------+  +--------+  +--------+  +--------+           |
|           | Button |  | Button |  | Button |  | Button |           |  Variant row 3
|           +--------+  +--------+  +--------+  +--------+           |
|                                                                    |
+--------------------------------------------------------------------+

Grid layout:
- Columns: variant label (120px fixed) + state columns (flex 1 each)
- Rows: header (32px fixed) + variant rows (auto height)
- Column gap: 16px
- Row gap: 24px
- Board padding: 24px
```

### Variant Label Column

Each row starts with a text label identifying the variant:

```
Variant labels: 12px Inter Semibold, UPPERCASE, #9CA3AF
Position: left-aligned in first grid column
Vertically centered with the component in that row
```

### State Column Headers

Top row contains state labels:

```
State headers: 12px Inter Semibold, UPPERCASE, #9CA3AF
Position: centered in each column
```

### Focus State

Focus state is typically shown as default + focus ring overlay rather than a separate column.
Create it as the default state with an additional border:

```javascript
// Focus state = default appearance + focus ring
const focusRing = penpot.createRectangle();
focusRing.resize(componentWidth + 4, componentHeight + 4);
focusRing.fills = [];
focusRing.strokes = [{
  strokeColor: '#3B82F6', strokeOpacity: 1,
  strokeWidth: 2, strokeStyle: 'solid', strokeAlignment: 'outer'
}];
focusRing.borderRadius = componentRadius + 2;
// Position centered around the default component
```

## Sample Screen Board Dimensions

| Target | Board Size | Notes |
|-|-|-|
| iPhone SE | 375 × 667 | Small mobile |
| iPhone 14 | 390 × 844 | Standard mobile |
| iPhone 14 Pro Max | 430 × 932 | Large mobile |
| Android standard | 360 × 800 | Common Android |
| iPad | 820 × 1180 | Tablet |
| Desktop | 1440 × 900 | Standard desktop |
| Desktop HD | 1920 × 1080 | Full HD desktop |

### Mobile Screen Structure

```
+-------------------------+
| ## Status Bar (44px) ## |  Background matches nav or content
+-------------------------+
| Header (56px)           |  App name, back button, actions
| - - - - - - - - - - - - |
|                         |
| Content Area            |  Scrollable
| Padding: 16px horiz     |
|                         |
| +---------------------+ |  Cards, lists, forms
| |     Component       | |
| +---------------------+ |
|                         |
| +---------------------+ |
| |     Component       | |
| +---------------------+ |
|                         |
+-------------------------+
| Bottom Nav (84px)       |  Includes safe area (34px)
+-------------------------+
```

### Desktop Dashboard Structure

```
+------------------------------------------------------+
| Top Bar (64px)                                       |
| Logo        Search                       User Menu   |
+--------+---------------------------------------------+
|        | Page Title + Actions                        |
| Side   +---------------------------------------------+
| bar    | +------+ +------+ +------+ +------+         |
|        | |Metric| |Metric| |Metric| |Metric|         |  Metric cards row
| 240px  | +------+ +------+ +------+ +------+         |
|        +---------------------------------------------+
| Nav    | +------------------------+ +--------------+ |
| items  | |                        | |              | |  Main content area
|        | |  Primary Content       | |  Side Panel  | |
|        | |  (Chart, Table, etc.)  | |              | |
|        | |                        | |              | |
|        | +------------------------+ +--------------+ |
+--------+---------------------------------------------+
```

## Execution Sequence

### Recommended Board Creation Order

```
1. Create "cover" page
     Create version-info board               (1 call)

2. Switch to "foundations" page
     Create colors/primitives board          (1-2 calls)
     Create colors/semantic board            (1 call)
     Create typography/scale board           (1 call)
     Create spacing/scale board              (1 call)
     Create elevation/levels board           (1 call)

3. Switch to "atoms" page
     Create button/variants board            (1 call per variant×state)
     Assemble + register button components   (1 call)
     Create input/variants board             (similar pattern)
     Create toggle/variants board            (similar pattern)
     ...per Confirmed Spec

4. Switch to "molecules" page (if needed)
     Create card/variants board
     Create form-field/variants board
     ...per Confirmed Spec

5. Switch to "organisms" page (if needed)
     Create header-navbar/variants board
     ...per Confirmed Spec

6. Switch to "screens-*" page
     Create main board                       (1 call)
     Build layout structure                  (1-2 calls)
     Instantiate components                  (1-2 calls)
     Apply content and final style           (1-2 calls)
```

**Total estimated calls:** 25–40 `execute_code` calls for a typical design system
with 4 component types + sample screen.

### Visual Validation Points

Export and check at these milestones:

1. After Colors board → verify palette looks correct
2. After Typography board → verify font renders correctly
3. After first component type (Buttons) → verify style matches spec
4. After sample screen layout → verify before adding content
5. Final export of complete sample screen → final validation

Use `mcp__penpot__export_shape` with the board ID to get a PNG for inspection.

## Naming Conventions

### Page Names (from penpot-design-system-guide.md)

cover, foundations, atoms, molecules, organisms, patterns, screens-*

### Frame Names

Follow `{page-context}/{frame-purpose}`:

```
foundations:    colors/primitives, colors/semantic, typography/scale, spacing/scale
atoms:         button/variants, button/anatomy, input/variants
molecules:     card/variants, form-field/variants
organisms:     header-navbar/variants, data-table/variants
screens-*:     dashboard/main, landing/hero
```

### Component Registration Names

Follow `{page-context}/{component-name}/{variant-property}/{variant-value}`:

```
atoms/button/appearance/primary
atoms/button/appearance/secondary
atoms/button/appearance/ghost
atoms/input/state/default
atoms/input/state/error
molecules/card/type/content
molecules/card/type/metric
```

### Asset Names

Color assets (slash-separated):  `primitives/blue-50`, `semantic/bg-body`, `semantic/action-primary-bg`
Typography assets:               `heading/h1`, `body/md`, `caption/default`, `label/sm`

Shape lookup: `penpotUtils.findShapes(s => s.name.includes('button/'))`

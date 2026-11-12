# Confirmation Templates

Output formats and interaction patterns for Phase 1 (Design Inventory) and Phase 2
(User Confirmation).

## Design Inventory Format

Present the Phase 1 extraction in this structure. Only populate sections where evidence
exists in the screenshots.

```
## Design Inventory

### Initial Assessment
PLATFORM: [mobile/web/desktop]  DESIGN LANGUAGE: [material/iOS HIG/custom]
LAYOUT: [single-column/sidebar+content/dashboard grid]
DENSITY: [compact/comfortable/spacious]  COLOR MODE: [light/dark/mixed]

### 1. Color Palette

| # | Color | Hex | Observed In | Suggested Token |
|-|-|-|-|-|
| 1 | [description] | #XXXXXX | [specific element] | color.[category].[name] |
| 2 | ... | ... | ... | ... |

Organized by role:
- **Brand:** primary, secondary accent
- **Neutral:** backgrounds, surfaces, text, borders
- **Semantic:** success, warning, error, info
- **Accent:** additional highlight colors

### 2. Typography

| # | Style | Family (confidence) | Size | Weight | Case | Tracking | Observed In |
|-|-|-|-|-|-|-|-|
| 1 | Display | Inter (high) | ~32px | Bold (700) | Normal | Tight | Page titles |
| 2 | Body | Inter (high) | ~16px | Regular (400) | Normal | Normal | Main content |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 3. Spacing

Base unit: [N]px

| Scale | Value | Multiplier | Used For |
|-|-|-|-|
| 2xs | [N]px | base × 0.5 | [context] |
| xs | [N]px | base × 1 | [context] |
| sm | [N]px | base × 2 | [context] |
| md | [N]px | base × 3 | [context] |
| lg | [N]px | base × 4 | [context] |
| xl | [N]px | base × 6 | [context] |
| 2xl | [N]px | base × 8 | [context] |

Component padding: Buttons [vals], Cards [vals], Inputs [vals]
Gap patterns: Form fields [N]px, Button groups [N]px, Sections [N]px

### 4. Layout Structure

Grid: [type], [N] columns, ~[N]px gutter, ~[N]px margin
Section map:
  [Section]: [position, ~dimensions, role]
  [Section]: [position, ~dimensions, role]
Visual hierarchy:
  1. [Element] — draws attention via [mechanism]
  2. [Element] — secondary via [mechanism]
  3. [Element] — tertiary via [mechanism]
Alignment: [left/center/mixed]

### 5. Border Radius

| Value | Where | Suggested Token |
|-|-|-|
| [N]px | [elements] | radius.[name] |

### 6. Shadows & Depth

Depth strategy: [borders-only / subtle-shadows / layered-shadows / surface-shifts]

| Level | Values (approx) | Used For |
|-|-|-|
| [N] | [offset blur spread color] | [context] |

Border treatments: [descriptions]
Elevation map: Level 0 [elements], Level 1 [elements], ...
Divider pattern: [description]

### 7. Component Inventory

| # | Component | Variants Detected | States Visible | States Needed | Notes |
|-|-|-|-|-|-|
| 1 | [name] | [list] | [list] | [list] | [characteristics] |

### 8. Iconography
Style: [outlined/filled/duotone], Weight: [thin/regular/bold]
Size: ~[N]px, Set: [identified or "unknown — [description]"]

### 9. Additional Patterns
[Gradients, glassmorphism, textures, illustrations, image treatment, etc. — or "none"]

### 10. Known Gaps (MANDATORY)
Cannot determine from static screenshots:
  - [ ] [gap item]
Low confidence extractions:
  - [ ] [item] — [reason]
Suggested next steps:
  - [how to fill gaps]
```

## Phase 2 Interaction Patterns

### Category-Level Review (Step 2a)

Present the inventory, then:

```
For each category, let me know:
- ✅ Looks good as-is
- ✏️ Needs adjustments (I'll ask for details)
- ❌ Skip this category
- ➕ Add something not in the screenshots

Categories:
 1. Color Palette — [X colors extracted, organized by role]
 2. Typography — [X text styles, font: [name] (confidence)]
 3. Spacing — [N]px base unit, [X] scale values
 4. Layout Structure — [grid type], [X] sections mapped
 5. Border Radius — [X] distinct values
 6. Shadows & Depth — [strategy], [X] elevation levels
 7. Components — [X] detected, [Y] gaps flagged
 8. Iconography — [summary or "none detected"]
 9. Additional Patterns — [summary or "none"]
10. Known Gaps — [X] items need your decisions
```

### Gaps Category Handling

The Gaps category (10) is special — don't ask "confirm or adjust." Instead, present each
gap as a decision with a proposed default:

```
These items couldn't be determined from the screenshots. Here are my proposals:

HOVER STATES: 10% darker background for hover, 20% darker for active. OK?
FOCUS RING: 2px solid, primary color, 2px offset. OK?
DISABLED STATE: 50% opacity on all interactive elements. OK?
FONT FAMILY: Best guess is Inter (confidence: medium). Confirm or suggest alternative?
ERROR STATES (inputs): Red border (#EF4444) + error text below field. OK?
LOADING STATES: Not visible — skip for now, or add skeleton patterns?
```

### Drill-Down Examples (Step 2b)

When a user marks a category as ✏️, present individual elements. Common adjustments:

**Colors:**
- "Make the accent more saturated"
- "Add a secondary accent in orange"
- "Dark background should be pure black, not dark green"

**Typography:**
- "Use Geist instead of Inter"
- "All button labels should be uppercase"
- "Scale heading sizes down 20%"

**Components:**
- "Skip the bottom navigation"
- "Add a dropdown — not in screenshots but I need it"
- "Add a modal/dialog component"

**Spacing:**
- "Use 4px base grid, not 8px"
- "Card padding should be 20px"

**Layout:**
- "Sidebar should be 280px, not 240px"
- "Sample screen should be mobile (375×812), not desktop"

**Shadows & Depth:**
- "This should be borders-only, no shadows"
- "Make card shadows more pronounced"

## Confirmed Spec Format (Step 2c)

Present this clean summary after all adjustments. Require explicit "go ahead" before Phase 3.

```
## Confirmed Spec — Ready to Generate

### Colors: [X colors]
| Token | Hex | Role |
|-|-|-|
| color.[...] | #XXXXXX | [usage] |

### Typography: [X styles]
| Level | Family | Size | Weight | Notes |
|-|-|-|-|-|
| [name] | [family] | [size] | [weight] | [case, tracking] |

### Spacing: [N]px base unit
| Token | Value | Usage |
|-|-|-|
| space.[...] | [N]px | [context] |

### Layout: [platform], [W×H] target
[section map, grid structure]

### Depth Strategy: [strategy]
[shadow levels, border treatments]

### Border Radius: [X values]
| Token | Value |
|-|-|
| radius.[...] | [N]px |

### Components to Generate: [X]
| # | Component | Variants | States |
|-|-|-|-|
| 1 | [name] | [list] | [list] |

### Resolved Gaps
[decisions made during confirmation — hover rules, missing states, confirmed fonts, etc.]

### Output Plan
- Token files: tokens.json, design-tokens.css, main.css
- Penpot pages: cover, foundations, atoms [+ molecules, organisms, patterns, screens-* as needed]
- Estimated MCP calls: ~[N]

Shall I proceed with generation?
```

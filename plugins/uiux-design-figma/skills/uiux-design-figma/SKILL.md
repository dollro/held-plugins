---
name: uiux-design-figma
description: "Creates and reviews UI/UX designs in Figma through figma-console-mcp tools: screens for web, mobile and desktop, design systems with components and variables, dashboards, forms, navigation and landing pages, with accessibility and platform guidelines (iOS, Android, Material). Use for \"design in figma\", \"figma design system\", \"figma component library\", \"figma variables\". For Penpot use uiux-design-penpot."
---

# Figma UI/UX Design Guide

Create professional, user-centered designs in Figma using the `figma-console-mcp` MCP server and proven UI/UX principles.

## Available MCP Tools

### Navigation & Status

| Tool | Purpose |
|-|-|
| `figma_navigate` | Open a Figma URL and start monitoring |
| `figma_get_status` | Check connection and transport status |
| `figma_reconnect` | Reconnect to Figma Desktop |

### Design Creation

| Tool | Purpose |
|-|-|
| `figma_execute` | **Power tool** — run any Figma Plugin API code to create/modify designs |
| `figma_arrange_component_set` | Organize variants into a professional component set with labels |
| `figma_set_description` | Add markdown descriptions to components (visible in Dev Mode) |

### Variable / Token Management

| Tool | Purpose |
|-|-|
| `figma_setup_design_tokens` | Create collection + modes + variables atomically in one call |
| `figma_create_variable_collection` | Create a new variable collection with modes |
| `figma_create_variable` | Create a single COLOR, FLOAT, STRING, or BOOLEAN variable |
| `figma_batch_create_variables` | Create up to 100 variables in one call (10-50x faster) |
| `figma_batch_update_variables` | Update up to 100 variable values in one call |
| `figma_update_variable` | Update a single variable value in a specific mode |
| `figma_rename_variable` | Rename a variable while preserving values |
| `figma_delete_variable` / `figma_delete_variable_collection` | Delete variables or entire collections |
| `figma_add_mode` / `figma_rename_mode` | Add or rename modes in a collection |
| `figma_get_variables` | Extract variables with optional CSS/Tailwind/Sass exports |
| `figma_get_token_values` | Get variable values organized by collection and mode |

### Node Manipulation

| Tool | Purpose |
|-|-|
| `figma_resize_node` / `figma_move_node` | Resize or reposition a node |
| `figma_clone_node` / `figma_delete_node` / `figma_rename_node` | Clone, delete, or rename nodes |
| `figma_set_text` | Set text content of a text node |
| `figma_set_fills` / `figma_set_strokes` | Set fill colors or stroke colors |
| `figma_create_child` | Create a child node inside a parent |
| `figma_set_image_fill` | Set an image fill on nodes |

### Component Management

| Tool | Purpose |
|-|-|
| `figma_search_components` | Find components by name (local file + published libraries) |
| `figma_get_library_components` | Discover components from published team libraries |
| `figma_get_component_details` | Get detailed info about a specific component |
| `figma_instantiate_component` | Create a component instance (supports cross-library) |
| `figma_add_component_property` / `figma_edit_component_property` / `figma_delete_component_property` | Manage component properties |

### Design System Extraction

| Tool | Purpose |
|-|-|
| `figma_get_design_system_kit` | **Full design system in one call** — tokens, components, styles, visual specs |
| `figma_get_design_system_summary` | High-level overview (counts, categories, page structure) |
| `figma_get_styles` | Get color, text, effect styles |
| `figma_get_component` | Get component data (metadata or reconstruction spec) |
| `figma_get_file_data` / `figma_get_file_for_plugin` | File structure and data |

### Visual Debugging & Lint

| Tool | Purpose |
|-|-|
| `figma_take_screenshot` | Capture screenshots (plugin, full-page, or viewport) |
| `figma_lint_design` | WCAG accessibility and design quality checks |

## Quick Reference

| Task | Reference File |
|-|-|
| Component specs (buttons, forms, nav) | `uiux-design-system/references/component-patterns.md` |
| Accessibility (contrast, touch targets) | `uiux-design-system/references/accessibility.md` |
| Screen sizes & platform specs | `uiux-design-system/references/platform-guidelines.md` |
| Color conversion utilities | `uiux-design-system/references/color-utilities.md` |
| Token binding strategy | `uiux-design-system/references/token-binding-strategy.md` |
| Mapped token categories (text/icon/surface/border) | `uiux-design-system/references/mapped-tokens.md` |
| Design system template & checklist | `uiux-design-system/references/design-system-template.md` |
| Multi-brand & dark mode strategy | `uiux-design-system/references/theming-multi-brand.md` |
| Figma MCP tool catalog | [figma-api-reference.md](references/figma-api-reference.md) |
| Figma design system guide | [figma-design-system-guide.md](references/figma-design-system-guide.md) |
| Layout decision guide (**read before step 5**) | [generation-recipes.md § Layout Selection Guide](references/generation-recipes.md) + `uiux-design-system/references/layout-patterns.md` |
| Reusable figma_execute templates | [generation-recipes.md](references/generation-recipes.md) |
| DTCG to Figma variable mapping | [variable-mapping.md](references/variable-mapping.md) |
| Variable binding (resolver, sweep) | [variable-binding.md](references/variable-binding.md) |
| MCP server setup | [setup-troubleshooting.md](references/setup-troubleshooting.md) |

## Core Design Principles

### The Golden Rules

1. **Clarity over cleverness**: Every element must have a purpose
2. **Consistency builds trust**: Reuse patterns, colors, and components
3. **User goals first**: Design for tasks, not features
4. **Accessibility is not optional**: Design for everyone
5. **Test with real users**: Validate assumptions early

### Visual Hierarchy (Priority Order)

1. **Size**: Larger = more important
2. **Color/Contrast**: High contrast draws attention
3. **Position**: Top-left (LTR) gets seen first
4. **Whitespace**: Isolation emphasizes importance
5. **Typography weight**: Bold stands out

## Design Workflow

1. **Check for design system first**: Ask user if they have existing tokens/specs, or discover from `figma_get_design_system_kit`
2. **Understand the file**: Use `figma_get_file_data` or `figma_get_file_for_plugin` to see page structure
3. **Find elements**: Use `figma_search_components` for library components, or `figma_execute` with `figma.currentPage.findAll()` to locate nodes
4. **Create/modify**: Use `figma_execute` with the Figma Plugin API, or dedicated tools like `figma_set_fills`, `figma_set_text`
5. **Apply layout**: Choose the right auto-layout pattern for each container:
   - **Horizontal** auto-layout: items in a row (nav, toolbar). For equal-width columns, set `layoutSizingHorizontal = 'FILL'` on every child
   - **Vertical** auto-layout: items in a column (card internals, sidebar). For push-to-bottom, set middle child `layoutSizingVertical = 'FILL'`
   - **Wrap** (`layoutWrap = 'WRAP'`): tags, chip lists, responsive card grids that reflow
   - **Nested**: outer `HORIZONTAL` (sidebar + main), inner `VERTICAL` (content stacking) — this is how Figma achieves 2D page structure
   - **Before generating**: Read `generation-recipes.md` § "Layout Selection Guide" for concrete patterns. Do not use auto-layout VERTICAL for everything
6. **Set up variables**: Use `figma_setup_design_tokens` or `figma_batch_create_variables`
7. **Validate**: `figma_take_screenshot` for visual check, `figma_lint_design` for accessibility

## Design System Handling

**Before creating designs, determine if the user has an existing design system:**

1. **Ask the user**: "Do you have a design system or brand guidelines to follow?"
2. **Discover from Figma**: Use `figma_get_design_system_kit` or `figma_get_design_system_summary`

```javascript
// Discover existing patterns via figma_execute
const collections = figma.variables.getLocalVariableCollections();
const components = figma.currentPage.findAll(n => n.type === 'COMPONENT');
return {
  componentCount: components.length,
  variableCollections: collections.map(c => ({
    name: c.name, modes: c.modes.map(m => m.name), variableCount: c.variableIds.length
  }))
};
```

**If user HAS a design system:** use their colors, spacing, typography, and naming conventions.

**If user has NO design system:** use the default tokens below, offer to establish patterns, reference `uiux-design-system/references/component-patterns.md`.

### Mapped Token Categories

When setting up Figma variable collections, structure the mapped/component tier into four categories matching the design system architecture:

- **text/** — `text/heading`, `text/body`, `text/action`, `text/on-action`, `text/disabled`, `text/error`, `text/success`
- **icon/** — mirrors text tokens (`icon/default` = `text/body`, `icon/action` = `text/action`, etc.)
- **surface/** — `surface/page`, `surface/default`, `surface/action`, `surface/action-hover`, `surface/action-hover-light`, `surface/disabled`
- **border/** — `border/default`, `border/action`, `border/focus`, `border/disabled`, `border/error`

Each category should include state variants (default, hover, focus, disabled, error, success). Add Light/Dark modes to the collection and remap semantic values per mode.

For the complete token tables with light/dark mode values, read `uiux-design-system/references/mapped-tokens.md`.

**Internal components:** Prefix private building blocks with a dot (`.menu-item`, `.tab-item`) — Figma won't publish them to the library. Only composed components (`Menu`, `Tab Bar`) should be published.

## Key Figma API Gotchas

- **Desktop Bridge required** for all write operations — `figma_get_status` must return `setup.valid: true`
- **`figma_execute` runs in the Figma Plugin API sandbox** — `figma.*` globals available, web APIs (`document`, `window`, `fetch`) are NOT
- **Session-specific nodeIds** — IDs become stale after plugin restarts; re-search before reusing
- **Font loading is mandatory** — `await figma.loadFontAsync({family, style})` before setting `text.characters` or `text.fontName`
- **Colors use 0-1 normalized RGB** — `{ r: 0.23, g: 0.51, b: 0.96 }` not `{ r: 59, g: 130, b: 245 }`. Helper: `r/255, g/255, b/255`
- **Auto Layout properties**: `layoutMode`, `layoutWrap` (`'WRAP'`/`'NO_WRAP'`), `primaryAxisSizingMode`, `counterAxisSizingMode`, `itemSpacing`, `counterAxisSpacing` (wrap row gap), `paddingLeft/Right/Top/Bottom`, `primaryAxisAlignItems`, `counterAxisAlignItems`
- **Variables require a collection first** — create collection, then variables within it
- **`figma_execute` default timeout is 5s (max 30s)** — keep operations focused, split large tasks
- **Enterprise plan needed for REST Variables API** — Plugin API (via Desktop Bridge) works on all plans
- **Width/height are NOT directly settable** — use `node.resize(w, h)` instead
- **`createText()` default font** — must load and set the desired font before changing characters

### Hex to Figma RGB (inline helper)

```javascript
function hexToRgb(hex) {
  const h = hex.replace('#', '');
  return {
    r: parseInt(h.substring(0, 2), 16) / 255,
    g: parseInt(h.substring(2, 4), 16) / 255,
    b: parseInt(h.substring(4, 6), 16) / 255
  };
}
// hexToRgb('#3B82F6') -> { r: 0.231, g: 0.510, b: 0.965 }
```

More converters (HSL, RGB, OKLCH, palette generation, contrast checks) in `uiux-design-system/references/color-utilities.md`.

## figma_execute Patterns

### Frame with Auto-Layout

```javascript
const frame = figma.createFrame();
frame.name = "Card";
frame.resize(320, 200);
frame.cornerRadius = 12;
frame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
frame.layoutMode = "VERTICAL";
frame.primaryAxisSizingMode = "AUTO";
frame.counterAxisSizingMode = "FIXED";
frame.itemSpacing = 16;
frame.paddingLeft = frame.paddingRight = 24;
frame.paddingTop = frame.paddingBottom = 24;
frame.effects = [{
  type: 'DROP_SHADOW', color: { r: 0, g: 0, b: 0, a: 0.1 },
  offset: { x: 0, y: 4 }, radius: 12, spread: 0, visible: true
}];
```

### Text (async font loading required)

```javascript
await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
const heading = figma.createText();
heading.characters = "Card Title";
heading.fontName = { family: "Inter", style: "Semi Bold" };
heading.fontSize = 20;
heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.09, b: 0.15 } }];
```

### Components and Instances

```javascript
const comp = figma.createComponent();
comp.name = "Button";
comp.resize(120, 40);
comp.cornerRadius = 8;
comp.layoutMode = "HORIZONTAL";
comp.primaryAxisAlignItems = "CENTER";
comp.counterAxisAlignItems = "CENTER";
comp.fills = [{ type: 'SOLID', color: { r: 0.23, g: 0.51, b: 0.96 } }];

await figma.loadFontAsync({ family: "Inter", style: "Medium" });
const label = figma.createText();
label.characters = "Button";
label.fontName = { family: "Inter", style: "Medium" };
label.fontSize = 14;
label.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
comp.appendChild(label);

const instance = comp.createInstance(); // creates a linked instance
```

### Fills, Strokes, Effects

```javascript
// Solid fill
node.fills = [{ type: 'SOLID', color: { r: 0.23, g: 0.51, b: 0.96 } }];
// Semi-transparent
node.fills = [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 }, opacity: 0.5 }];
// Strokes
node.strokes = [{ type: 'SOLID', color: { r: 0.82, g: 0.84, b: 0.86 } }];
node.strokeWeight = 1;
node.strokeAlign = 'INSIDE'; // 'CENTER' | 'INSIDE' | 'OUTSIDE'
```

## Variable / Token Management

### Atomic Setup (Recommended for New Systems)

Use `figma_setup_design_tokens` for single-call setup — values keyed by **mode name** (not ID):

```
figma_setup_design_tokens({
  collectionName: "Brand Tokens",
  modes: ["Light", "Dark"],
  tokens: [
    { name: "color/primary", resolvedType: "COLOR",
      values: { "Light": "#3B82F6", "Dark": "#60A5FA" } },
    { name: "color/background", resolvedType: "COLOR",
      values: { "Light": "#FFFFFF", "Dark": "#111827" } },
    { name: "spacing/md", resolvedType: "FLOAT",
      values: { "Light": 16, "Dark": 16 } }
  ]
})
```

### Batch Operations

`figma_batch_create_variables` — up to 100/call, 10-50x faster. Values keyed by **mode ID**:

```
figma_batch_create_variables({
  collectionId: "VariableCollectionId:123:456",
  variables: [
    { name: "colors/primary/500", resolvedType: "COLOR",
      valuesByMode: { "1:0": "#3B82F6", "1:1": "#60A5FA" } }
  ]
})
```

### DTCG Type Mapping

| DTCG Type | Figma Type | Notes |
|-|-|-|
| `color` | `COLOR` | Hex string `"#RRGGBB"` |
| `dimension`, `spacing`, `sizing` | `FLOAT` | Numeric value |
| `fontFamily` | `STRING` | Font family name |
| `number`, `opacity`, `borderRadius`, `borderWidth` | `FLOAT` | Numeric value |
| `boolean` | `BOOLEAN` | `true` / `false` |

### Reading Variables

`figma_get_variables` with `enrich: true` for CSS/Tailwind exports, or `figma_get_token_values` for a quick overview.

## Variable Binding

### Greenfield (new designs)

Set the visual value first, then bind the variable via `figma_execute`:

```javascript
const collections = figma.variables.getLocalVariableCollections();
const vars = collections[0].variableIds.map(id => figma.variables.getVariableById(id));
const primaryVar = vars.find(v => v.name === "color/primary");
node.fills = [{ type: 'SOLID', color: { r: 0.23, g: 0.51, b: 0.96 } }];
node.setBoundVariable('fills', 0, primaryVar);
```

### Brownfield (existing nodes)

Sweep nodes, read `node.boundVariables`, match unbound fills to variables and bind them.

- **No toggle issue** (unlike Penpot) — `setBoundVariable` is idempotent
- See [variable-binding.md](references/variable-binding.md) for full patterns
- See `uiux-design-system/references/token-binding-strategy.md` for confidence scoring

## Auto Layout Patterns

```javascript
// Vertical stack
const frame = figma.createFrame();
frame.layoutMode = 'VERTICAL';
frame.primaryAxisSizingMode = 'AUTO';   // height grows with content
frame.counterAxisSizingMode = 'FIXED';  // fixed width
frame.itemSpacing = 16;
frame.paddingLeft = frame.paddingRight = 24;
frame.paddingTop = frame.paddingBottom = 24;

// Child sizing (set AFTER appending to auto-layout parent)
parent.appendChild(child);
child.layoutSizingHorizontal = 'FILL';  // 'FIXED' | 'HUG' | 'FILL'
child.layoutSizingVertical = 'HUG';

// Alignment: 'MIN' | 'CENTER' | 'MAX' | 'SPACE_BETWEEN'

// Wrap (responsive grid-like behavior)
frame.layoutWrap = 'WRAP';           // 'WRAP' | 'NO_WRAP'
frame.counterAxisSpacing = 16;       // gap between wrapped rows
// Children with minWidth will wrap when container narrows
```

## Component Patterns

### Creating Variants

```javascript
const defaultBtn = figma.createComponent();
defaultBtn.name = "State=Default";
const hoverBtn = figma.createComponent();
hoverBtn.name = "State=Hover";
// Combine into a component set (purple dashed border)
const componentSet = figma.combineAsVariants([defaultBtn, hoverBtn], figma.currentPage);
componentSet.name = "Button";
```

### Instantiating (cross-library)

```
figma_instantiate_component({
  componentKey: "abc123def456",
  x: 100, y: 200,
  overrides: { "Button Label": "Click Me", "Show Icon": true }
})
```

### Arranging Variants

```
figma_arrange_component_set({
  componentSetId: "123:456",
  options: { gap: 24, cellPadding: 20, columnProperty: "State" }
})
```

## Default Design Tokens

**Use these defaults only when user has no design system. Always prefer user's tokens if available.**

### Spacing Scale (8px base)

| Token | Value | Usage |
|-|-|-|
| `spacing/xs` | 4px | Tight inline elements |
| `spacing/sm` | 8px | Related elements |
| `spacing/md` | 16px | Default padding |
| `spacing/lg` | 24px | Section spacing |
| `spacing/xl` | 32px | Major sections |
| `spacing/2xl` | 48px | Page-level spacing |

### Typography Scale

| Level | Size | Weight | Usage |
|-|-|-|-|
| Display | 48-64px | Bold | Hero headlines |
| H1 | 32-40px | Bold | Page titles |
| H2 | 24-28px | Semi Bold | Section headers |
| H3 | 20-22px | Semi Bold | Subsections |
| Body | 16px | Regular | Main content |
| Small | 14px | Regular | Secondary text |
| Caption | 12px | Regular | Labels, hints |

### Color Usage

| Purpose | Recommendation |
|-|-|
| Primary | Main brand color, CTAs |
| Secondary | Supporting actions |
| Success | #22C55E range (confirmations) |
| Warning | #F59E0B range (caution) |
| Error | #EF4444 range (errors) |
| Neutral | Gray scale for text/borders |

## Common Layouts

### Mobile Screen (375x812)

```text
+-----------------------------+
| Status Bar (44px)           |
+-----------------------------+
| Header/Nav (56px)           |
+-----------------------------+
|                             |
| Content Area (Scrollable)   |
| Padding: 16px horizontal    |
|                             |
+-----------------------------+
| Bottom Nav/CTA (84px)       |
+-----------------------------+
```

### Desktop Dashboard (1440x900)

```text
+------+-------------------------------+
|      | Header (64px)                 |
| Side +-------------------------------+
| bar  | Page Title + Actions          |
| 240  +-------------------------------+
| px   | Content Grid                  |
|      | [Card] [Card] [Card] [Card]   |
+------+-------------------------------+
```

## Component Checklist

### Buttons

- [ ] Clear, action-oriented label (2-3 words)
- [ ] Minimum touch target: 44x44px
- [ ] Visual states: default, hover, active, disabled, loading
- [ ] Sufficient contrast (3:1 against background)
- [ ] Consistent border radius across app

### Forms

- [ ] Labels above inputs (not just placeholders)
- [ ] Required field indicators
- [ ] Error messages adjacent to fields
- [ ] Logical tab order
- [ ] Input types match content (email, tel, etc.)

### Navigation

- [ ] Current location clearly indicated
- [ ] Consistent position across screens
- [ ] Maximum 7 +/- 2 top-level items
- [ ] Touch-friendly on mobile (48px targets)

## Accessibility Quick Checks

1. **Color contrast**: Text 4.5:1, Large text 3:1
2. **Touch targets**: Minimum 44x44px
3. **Focus states**: Visible keyboard focus indicators
4. **Alt text**: Meaningful descriptions for images
5. **Hierarchy**: Proper heading levels (H1 > H2 > H3)
6. **Color independence**: Never rely solely on color

Use `figma_lint_design` to automate:

```
figma_lint_design({ rules: ["wcag"] })           // all accessibility checks
figma_lint_design({ rules: ["design-system"] })   // token/style hygiene
```

## Design Review Checklist

Before finalizing any design:

- [ ] Visual hierarchy is clear
- [ ] Consistent spacing and alignment
- [ ] Typography is readable (16px+ body text)
- [ ] Color contrast meets WCAG AA
- [ ] Interactive elements are obvious
- [ ] Mobile-friendly touch targets
- [ ] Loading/empty/error states considered
- [ ] Consistent with design system

## Validating Designs

| Check | Method |
|-|-|
| Accessibility compliance | `figma_lint_design` with `rules: ["wcag"]` |
| Design system hygiene | `figma_lint_design` with `rules: ["design-system"]` |
| Visual correctness | `figma_take_screenshot` and inspect |
| Token coverage | `figma_get_design_system_kit` with `enrich: true` |
| Component inventory | `figma_get_design_system_summary` |

## Tips for Great Designs

1. **Start with content**: Real content reveals layout needs
2. **Design mobile-first**: Constraints breed creativity
3. **Use a grid**: 8px base grid keeps things aligned
4. **Limit colors**: 1 primary + 1 secondary + neutrals
5. **Limit fonts**: 1-2 typefaces maximum
6. **Embrace whitespace**: Breathing room improves comprehension
7. **Be consistent**: Same action = same appearance everywhere
8. **Provide feedback**: Every action needs a response

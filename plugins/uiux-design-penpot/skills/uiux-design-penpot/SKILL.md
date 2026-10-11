---
name: uiux-design-penpot
description: "Creates and reviews UI/UX designs in Penpot through its MCP tools: screens for web, mobile and desktop, design systems with components and tokens, dashboards, forms, navigation and landing pages, with accessibility and platform guidelines (iOS, Android, Material). Use for \"design a UI\", \"create interface\", \"design dashboard\", \"design landing page\" in Penpot or when no design tool is named. For Figma use uiux-design-figma."
---

# Penpot UI/UX Design Guide

Create professional, user-centered designs in Penpot using the `penpot/penpot-mcp` MCP server and proven UI/UX principles.

## Available MCP Tools

| Tool | Purpose |
| ---- | ------- |
| `mcp__penpot__execute_code` | Run JavaScript in Penpot plugin context to create/modify designs |
| `mcp__penpot__export_shape` | Export shapes as PNG/SVG for visual inspection |
| `mcp__penpot__import_image` | Import images (icons, photos, logos) into designs |
| `mcp__penpot__penpot_api_info` | Retrieve Penpot API documentation |

## MCP Server Setup

The Penpot MCP tools require the `penpot/penpot-mcp` server running locally. For detailed installation and troubleshooting, see [setup-troubleshooting.md](references/setup-troubleshooting.md).

### Before Setup: Check If Already Running

**Always check if the MCP server is already available before attempting setup:**

1. **Try calling a tool first**: Attempt `mcp__penpot__penpot_api_info` - if it succeeds, the server is running and connected. No setup needed.

2. **If the tool fails**, ask the user:
   > "The Penpot MCP server doesn't appear to be connected. Is the server already installed and running? If so, I can help troubleshoot. If not, I can guide you through the setup."

3. **Only proceed with setup instructions if the user confirms the server is not installed.**

### Quick Start (Only If Not Installed)

```bash
# Clone and install
git clone https://github.com/penpot/penpot-mcp.git
cd penpot-mcp
npm install

# Build and start servers
npm run bootstrap
```

Then in Penpot:
1. Open a design file
2. Go to **Plugins** → **Load plugin from URL**
3. Enter: `http://localhost:4400/manifest.json`
4. Click **"Connect to MCP server"** in the plugin UI

### VS Code Configuration

Add to `settings.json`:
```json
{
  "mcp": {
    "servers": {
      "penpot": {
        "url": "http://localhost:4401/sse"
      }
    }
  }
}
```

### Troubleshooting (If Server Is Installed But Not Working)

| Issue | Solution |
| ----- | -------- |
| Plugin won't connect | Check servers are running (`npm run start:all` in penpot-mcp dir) |
| Browser blocks localhost | Allow local network access prompt, or disable Brave Shield, or try Firefox |
| Tools not appearing in client | Restart VS Code/Claude completely after config changes |
| Tool execution fails/times out | Ensure Penpot plugin UI is open and shows "Connected" |
| "WebSocket connection failed" | Check firewall allows ports 4400, 4401, 4402 |
| "No Penpot plugin instances are currently connected" | Plugin disconnected — reopen plugin panel in Penpot, click "Connect to MCP server" again. There is no auto-reconnect |
| Plugin disconnects during token/theme operations | See "Connection Stability" section below |

### Connection Stability (as of Penpot 2.13.x — newer versions may resolve these)

The MCP plugin communicates via WebSocket (port 4402). There is **no automatic reconnection** — if the connection drops, you must manually reconnect from the plugin UI.

**Common disconnect triggers:**
- **Plugin UI panel closed** (even accidentally) — immediately kills the connection
- **30-second execution timeout** — the bridge auto-rejects long-running tasks
- **Async property propagation** — operations like `theme.toggleActive()` and `set.toggleActive()` trigger internal async updates. Reading properties immediately after can cause race conditions or crashes
- **Heavy token/theme operations** in a single `execute_code` call

**Workarounds:**
- **Keep the plugin UI panel visible** at all times — closing it kills the connection
- **Split token/theme operations across multiple `execute_code` calls** — don't create tokens, activate themes, and read results in one call
- **Don't read properties immediately after toggling** — the async state hasn't propagated yet. A `waitForSync()` API has been proposed ([penpot-mcp #27](https://github.com/penpot/penpot-mcp/issues/27)) but is not yet available
- **If disconnected**: reopen plugin panel → click "Connect to MCP server" → retry the failed operation
- **Verify connection**: access `http://localhost:4403/` (REPL server) to test WebSocket connectivity independently

## Quick Reference

| Task | Reference File |
|-|-|
| MCP server installation & troubleshooting | [setup-troubleshooting.md](references/setup-troubleshooting.md) |
| MCP API known issues & workarounds | [mcp-known-issues.md](references/mcp-known-issues.md) |
| Penpot design system implementation (pages, frames, naming, assets) | [penpot-design-system-guide.md](references/penpot-design-system-guide.md) |
| Component specs (buttons, forms, nav) | `uiux-design-system/references/component-patterns.md` |
| Accessibility (contrast, touch targets) | `uiux-design-system/references/accessibility.md` |
| Mapped token categories (text/icon/surface/border) | `uiux-design-system/references/mapped-tokens.md` |
| Design system template & checklist | `uiux-design-system/references/design-system-template.md` |
| Multi-brand & dark mode strategy | `uiux-design-system/references/theming-multi-brand.md` |
| Screen sizes & platform specs | `uiux-design-system/references/platform-guidelines.md` |
| Full Penpot Plugin API reference | [penpot-api-reference.md](references/penpot-api-reference.md) |
| Color conversion utilities (OKLCH→hex, HSL→hex) | `uiux-design-system/references/color-utilities.md` |
| Penpot color API patterns (fills, gradients, library) | [penpot-color-patterns.md](references/penpot-color-patterns.md) |
| Token binding (resolver, toggle guard, brownfield sweep) | [token-binding.md](references/token-binding.md) |
| Prototyping, interactions & animations | [prototyping-interactions.md](references/prototyping-interactions.md) |
| Flex vs Grid layout decision (**read before step 5**) | [generation-recipes.md § Layout Selection Guide](references/generation-recipes.md) + `uiux-design-system/references/layout-patterns.md` |
| Reusable execute_code generation templates | [generation-recipes.md](references/generation-recipes.md) |

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

1. **Check for design system first**: Ask user if they have existing tokens/specs, or discover from current Penpot file
2. **Understand the page**: Call `mcp__penpot__execute_code` with `penpotUtils.shapeStructure()` to see hierarchy
3. **Find elements**: Use `penpotUtils.findShapes()` or `penpot.currentPage.findShapes({name, type})` to locate elements
4. **Create/modify**: Use `penpot.createBoard()`, `createRectangle()`, `createEllipse()`, `createText()`, `createPath()`, `createShapeFromSvg()` etc.
5. **Apply layout**: Choose the right layout method for each container:
   - **Flex** (`addFlexLayout()`): 1D content flow — items in a row/column, wrapping tags, nav items. Items size to their content
   - **Grid** (`addGridLayout()`): 2D structure or parent-controlled equal sizing — card grids (`'flex', 1` tracks), dashboards, page layouts (sidebar + header + main)
   - **Nested**: Grid for outer structure, flex for inner component layout (e.g., grid of cards where each card uses flex column internally)
   - **Rule of thumb**: If you're setting properties on *children* to fix sizing, use Grid instead (parent controls layout)
   - **Before generating**: Read `generation-recipes.md` § "Layout Selection Guide" for concrete Penpot API patterns. Do not default to flex for everything
6. **Add effects**: Apply shadows, blur, strokes, blend modes as needed
7. **Set up prototyping**: Add interactions, flows, overlays for click-through prototypes
8. **Validate**: Call `mcp__penpot__export_shape` to visually check your work

## Design System Handling

**Before creating designs, determine if the user has an existing design system:**

1. **Ask the user**: "Do you have a design system or brand guidelines to follow?"
2. **Discover from Penpot**: Check for existing components, colors, and patterns

```javascript
// Discover existing design patterns in current file
const allShapes = penpotUtils.findShapes(() => true, penpot.root);

// Find existing colors in use
const colors = new Set();
allShapes.forEach(s => {
  if (s.fills) s.fills.forEach(f => colors.add(f.fillColor));
});

// Find existing text styles (font sizes, weights)
const textStyles = allShapes
  .filter(s => s.type === 'text')
  .map(s => ({ fontSize: s.fontSize, fontWeight: s.fontWeight }));

// Find existing components
const components = penpot.library.local.components;

return { colors: [...colors], textStyles, componentCount: components.length };
```

**If user HAS a design system:**

- Use their specified colors, spacing, typography
- Match their existing component patterns
- Follow their naming conventions

**If user has NO design system:**

- Use the default tokens below as a starting point
- Offer to help establish consistent patterns
- Reference specs in `uiux-design-system/references/component-patterns.md`

### Mapped Token Categories

When setting up Penpot token sets, structure the mapped/component tier into four categories matching the design system architecture:

- **text/** — `text/heading`, `text/body`, `text/action`, `text/on-action`, `text/disabled`, `text/error`, `text/success`
- **icon/** — mirrors text tokens (`icon/default` = `text/body`, `icon/action` = `text/action`, etc.)
- **surface/** — `surface/page`, `surface/default`, `surface/action`, `surface/action-hover`, `surface/action-hover-light`, `surface/disabled`
- **border/** — `border/default`, `border/action`, `border/focus`, `border/disabled`, `border/error`

Each category should include state variants (default, hover, focus, disabled, error, success). Add Light/Dark theme sets and remap semantic values per theme.

For the complete token tables with light/dark mode values, read `uiux-design-system/references/mapped-tokens.md`.

**Internal components:** Prefix private building blocks with a dot (`.menu-item`, `.tab-item`) so they don't appear in the assets panel for end users. Only composed components (`Menu`, `Tab Bar`) should be registered as library components.

## Key Penpot API Gotchas

- **Penpot only accepts hex colors** (`#RRGGBB`) — CSS functions like `oklch()`, `hsl()`, `rgb()` do NOT work. See `uiux-design-system/references/color-utilities.md` for converters
- **No DOM in execute_code** — `document`, `window`, `getComputedStyle` are undefined. All code must be pure JavaScript math
- `width`/`height` are READ-ONLY → use `shape.resize(w, h)`
- `rotation` is READ-ONLY → use `shape.rotate(angle, center?)`
- `parentX`/`parentY` are READ-ONLY → use `penpotUtils.setParentXY(shape, x, y)`
- Use `insertChild(index, shape)` for z-ordering (not `appendChild`)
- Flex children array order is REVERSED for `dir="column"` or `dir="row"`
- After `text.resize()`, reset `growType` to `"auto-width"` or `"auto-height"`
- Grid `appendChild(child, row, column)` requires row/column — unlike flex's `appendChild(child)`
- `"fill"` token property maps to `fillColor` of the first fill, not the fills array
- **`createText('')` returns null** — empty strings produce null, not a Text shape. Always guard: `if (!content?.trim()) return null`. Spaces (`'  '`) work fine
- **Slash normalization** — `board.name = 'atoms/button'` becomes `'atoms / button'` (spaces injected). Use `.includes()` for name matching, never exact `===`
- **`createComponent` doubles the name** — prepends shape name to component name. Fix after registration by trimming the duplicate prefix. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **`comp.name` returns leaf only** — use `comp.mainInstance().name` for the full slash-separated path
- **`openPage()` context switch** — on upstream Penpot, `openPage()` may not switch the plugin execution context. Branch fix available. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **`layoutChild` is null before parenting** — always `parent.appendChild(child)` first, then access `child.layoutChild`
- **`applyToken()` with explicit properties silently fails** for some non-color token types (confirmed: `fontFamilies`). Only pass `'fill'`/`'strokeColor'` for color tokens. For all other types, **omit the properties arg**. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **Token API arg style is version-dependent** — object form (`addSet({ name: "x" })`) and positional form (`addSet("x")`) swap behavior between Penpot versions. Test both at project start. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **Child positioning is page-absolute** — after `board.appendChild(child)`, `child.x = N` sets page coordinates, not board-relative. Use `penpotUtils.setParentXY(child, relX, relY)` or flex/grid layouts. Nested boards need recursive fixing. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **Async property updates** (Penpot ≤2.13.x) — after `toggleActive()`, `resize()`, or `growType` changes, computed properties (e.g. `height`) update async (~100ms). Don't read them in the same `execute_code` call — use a follow-up call instead

### OKLCH to Hex (inline helper)

When working with OKLCH colors (Tailwind v4, modern design systems), use this converter:

```javascript
function oklchToHex(L, C, H) {
  const hRad = H * Math.PI / 180;
  const a = C * Math.cos(hRad), b = C * Math.sin(hRad);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  let r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  let bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
  const gamma = v => v > 0.0031308 ? 1.055 * Math.pow(v, 1/2.4) - 0.055 : 12.92 * v;
  const toByte = v => Math.max(0, Math.min(255, Math.round(gamma(Math.max(0, v)) * 255)));
  return '#' + [r, g, bl].map(v => toByte(v).toString(16).padStart(2, '0')).join('').toUpperCase();
}
// oklchToHex(1, 0, 0) → '#FFFFFF'  |  oklchToHex(0, 0, 0) → '#000000'
```

More converters (HSL, RGB, palette generation, contrast checks) in `uiux-design-system/references/color-utilities.md`.
Penpot-specific color API patterns (fills, gradients, library) in [penpot-color-patterns.md](references/penpot-color-patterns.md).

## Positioning New Boards

**Always check existing boards before creating new ones** to avoid overlap:

```javascript
// Find all existing boards and calculate next position
const boards = penpotUtils.findShapes(s => s.type === 'board', penpot.root);
let nextX = 0;
const gap = 100; // Space between boards

if (boards.length > 0) {
  // Find rightmost board edge
  boards.forEach(b => {
    const rightEdge = b.x + b.width;
    if (rightEdge + gap > nextX) {
      nextX = rightEdge + gap;
    }
  });
}

// Create new board at calculated position
const newBoard = penpot.createBoard();
newBoard.x = nextX;
newBoard.y = 0;
newBoard.resize(375, 812);
```

**Board spacing guidelines:**

- Use 100px gap between related screens (same flow)
- Use 200px+ gap between different sections/flows
- Align boards vertically (same y) for visual organization
- Group related screens horizontally in user flow order

## Shape Operations

Beyond `createBoard()`, `createRectangle()`, `createText()`:

| Method | Returns | Purpose |
|-|-|-|
| `penpot.createEllipse()` | Ellipse | Circle/oval shapes |
| `penpot.createPath()` | Path | Custom vector paths |
| `penpot.createBoolean(type, shapes)` | Boolean | Union, difference, intersection, exclude |
| `penpot.createShapeFromSvg(svgString)` | Group | Import SVG as shapes |
| `penpot.group(shapes)` | Group | Group shapes together |
| `penpot.ungroup(group)` | void | Ungroup |
| `shape.clone()` | Shape | Duplicate a shape |
| `shape.remove()` | void | Delete a shape |
| `shape.rotate(angle, center?)` | void | Rotate in degrees |
| `shape.export(config)` | Promise\<Uint8Array\> | Programmatic export |

### Z-Ordering & Alignment

```javascript
shape.bringToFront();    // top of stack
shape.bringForward();    // one step up
shape.sendToBack();      // bottom of stack
shape.sendBackward();    // one step down

penpot.alignHorizontal(shapes, 'center'); // 'left' | 'center' | 'right'
penpot.alignVertical(shapes, 'top');      // 'top' | 'center' | 'bottom'
penpot.distributeHorizontal(shapes);      // even spacing
penpot.distributeVertical(shapes);
```

## Grid Layout

Boards support grid layout in addition to flex:

```javascript
const board = penpot.createBoard();
board.resize(600, 400);
const grid = board.addGridLayout();

// Add tracks — types: "flex", "fixed", "percent", "auto"
grid.addColumn('fixed', 200);  // sidebar
grid.addColumn('flex', 1);     // main content
grid.addRow('fixed', 64);      // header
grid.addRow('flex', 1);        // body

// Place children at specific row/column
grid.appendChild(sidebar, 0, 0);   // row 0, col 0
grid.appendChild(header, 0, 1);    // row 0, col 1
grid.appendChild(content, 1, 1);   // row 1, col 1
```

Grid shares the same padding/gap/sizing properties as flex (`rowGap`, `columnGap`, `horizontalPadding`, etc.).

## Effects

```javascript
// Drop shadow
shape.shadows = [{
  style: 'drop-shadow', offsetX: 0, offsetY: 4,
  blur: 12, spread: 0,
  color: { color: '#000000', opacity: 0.15 }
}];

// Inner shadow
shape.shadows = [{ style: 'inner-shadow', offsetX: 0, offsetY: 2, blur: 4, spread: 0, color: { color: '#000000', opacity: 0.1 } }];

// Blur
shape.blur = { type: 'layer-blur', value: 8 };

// Strokes
shape.strokes = [{
  strokeColor: '#D1D5DB', strokeOpacity: 1,
  strokeStyle: 'solid',  // 'solid' | 'dotted' | 'dashed'
  strokeWidth: 1,
  strokeAlignment: 'inner' // 'center' | 'inner' | 'outer'
}];
```

Blend modes: `normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color-dodge`, `color-burn`, `hard-light`, `soft-light`, `difference`, `exclusion`, `hue`, `saturation`, `color`, `luminosity`

## Text & Typography

```javascript
// Create styled text
const text = penpot.createText('Hello World');
text.fontFamily = 'Inter';
text.fontSize = '24';
text.fontWeight = '600';
text.align = 'center';

// Per-character styling with TextRange
const range = text.getRange(0, 5); // "Hello"
range.fontWeight = '700';
range.fills = [{ fillColor: '#3B82F6' }];

// Apply library typography
const typo = penpot.library.local.typographies.find(t => t.name === 'Heading');
if (typo) text.applyTypography(typo);

// Font discovery
const inter = penpot.fonts.findByName('Inter');
const allFonts = penpot.fonts.all;
```

## Library Management

```javascript
// Create library color
const libColor = penpot.library.local.createColor();
libColor.name = 'Primary';
libColor.path = 'Brand';
libColor.color = '#3B82F6';

// Use library colors as fills/strokes
shape.fills = [libColor.asFill()];
shape.strokes = [libColor.asStroke()];

// Create library typography
const libTypo = penpot.library.local.createTypography();
libTypo.name = 'Body';
const font = penpot.fonts.findByName('Inter');
if (font) libTypo.setFont(font);
libTypo.fontSize = '16';

// Create component from shapes
const component = penpot.library.local.createComponent([shape1, shape2]);
const instance = component.instance(); // create instance

// Color operations
const colors = penpot.shapesColors(penpot.selection); // discover colors
penpot.replaceColor(penpot.selection, { color: '#FF0000' }, { color: '#3B82F6' }); // swap
```

## Design Tokens API

Penpot has a built-in design tokens system (17 token types). **Important:** the arg style (object vs positional) is version-dependent — test both at project start. See [mcp-known-issues.md](references/mcp-known-issues.md) for full details.

```javascript
const catalog = penpot.library.local.tokens;

// Create a token set — test both arg styles at project start
catalog.addSet("Brand/Colors"); // positional — OR: addSet({ name: "Brand/Colors" })

// Read back for reliable proxy (addSet return value may have empty id)
const set = catalog.sets.find(s => s.name === "Brand/Colors");

// Add tokens — (type, name, value) or ({ type, name, value })
// 17 types (use EXACT strings): borderRadius, borderWidth, color,
// dimension, fontFamilies (NOT fontFamily), fontSizes (NOT fontSize),
// fontWeights, letterSpacing, number, opacity, rotation, shadow,
// sizing, spacing, textCase, textDecoration, typography
set.addToken("color", "primary", "#3B82F6");
set.addToken("spacing", "md", "16");          // string, not number
set.addToken("borderRadius", "lg", "12");     // string, not number
set.addToken("spacing", "ref", "{spacing.md}"); // references work

// Activate set
if (!set.active) set.toggleActive();

// Create and activate themes — POSITIONAL args: (group, name)
catalog.addTheme("Mode", "Light");
catalog.addTheme("Mode", "Dark");

// Apply token to shape
const token = set.tokens.find(t => t.name === "primary");
shape.applyToken(token, 'fill'); // TokenColorProps: 'fill' | 'strokeColor'
```

**Gotchas:** `catalog.sets` crashes on files with no tokens — create a set first. Duplicate token names silently return `undefined`. See [mcp-known-issues.md](references/mcp-known-issues.md) for the full working flow and all workarounds.

### Token Binding

**Every shape should be bound to its semantic token** — not just have a hardcoded hex value. Without binding, changing a token value won't propagate to shapes.

- **Greenfield** (creating new shapes): bind tokens inline during creation. See [generation-recipes.md](references/generation-recipes.md) for the `initTokenResolver()` + `tokenMap` pattern.
- **Brownfield** (existing file with unbound tokens): run the binding sweep from [token-binding.md](references/token-binding.md). Auto-applies high-confidence bindings, surfaces ambiguous ones for user confirmation.
- **Strategy & confidence scoring**: see `uiux-design-system/references/token-binding-strategy.md` for the tool-agnostic methodology.

**Trigger phrases:** "bind tokens to shapes", "wire up tokens", "audit token bindings", "tokens aren't applied", "tokens aren't working".

**Critical:** `applyToken()` is a **toggle** in Penpot — calling it on an already-bound shape unbinds the token. Always check `shape.tokens` before applying. See [token-binding.md](references/token-binding.md) for the `applySafe()` toggle guard.

## Page, Viewport & Events

```javascript
// Page management
const page = penpot.createPage();
page.name = 'Settings';
penpot.openPage(page);

// Find shapes on current page (built-in — no penpotUtils needed)
const buttons = penpot.currentPage.findShapes({ nameLike: 'btn-' });
const boards = penpot.currentPage.findShapes({ type: 'board' });
const shape = penpot.currentPage.getShapeById('some-id');

// Viewport control
penpot.viewport.zoomIntoView(shapes);  // zoom to fit shapes
penpot.viewport.zoomToFitAll();        // zoom to fit all
penpot.viewport.zoom = 1.5;           // set zoom level (1 = 100%)

// Events
const id = penpot.on('selectionchange', (ids) => { /* shape IDs */ });
penpot.off(id); // remove listener
// Events: pagechange, filechange, selectionchange, themechange, shapechange, contentsave

// History — batch operations as single undo step
const blockId = penpot.history.undoBlockBegin();
// ... multiple operations ...
penpot.history.undoBlockFinish(blockId);

// Upload media
const imgData = await penpot.uploadMediaUrl('logo', 'https://example.com/logo.png');
```

## Prototyping

Add interactive behaviors for view mode. See [prototyping-interactions.md](references/prototyping-interactions.md) for full guide.

```javascript
// Navigate on click
shape.addInteraction('click', {
  type: 'navigate-to', destination: targetBoard,
  animation: { type: 'slide', direction: 'left', duration: 300, easing: 'ease-in-out' }
});

// Open overlay modal
shape.addInteraction('click', {
  type: 'open-overlay', destination: modalBoard,
  position: 'center', closeWhenClickOutside: true, addBackgroundOverlay: true
});

// Triggers: 'click' | 'mouse-enter' | 'mouse-leave' | 'after-delay'
// Actions: navigate-to | open-overlay | toggle-overlay | close-overlay | previous-screen | open-url

// Create a flow entry point
penpot.currentPage.createFlow('Main Flow', startBoard);
```

## Default Design Tokens

**Use these defaults only when user has no design system. Always prefer user's tokens if available.**

### Spacing Scale (8px base)

| Token | Value | Usage |
| ----- | ----- | ----- |
| `spacing-xs` | 4px | Tight inline elements |
| `spacing-sm` | 8px | Related elements |
| `spacing-md` | 16px | Default padding |
| `spacing-lg` | 24px | Section spacing |
| `spacing-xl` | 32px | Major sections |
| `spacing-2xl` | 48px | Page-level spacing |

### Typography Scale

| Level | Size | Weight | Usage |
| ----- | ---- | ------ | ----- |
| Display | 48-64px | Bold | Hero headlines |
| H1 | 32-40px | Bold | Page titles |
| H2 | 24-28px | Semibold | Section headers |
| H3 | 20-22px | Semibold | Subsections |
| Body | 16px | Regular | Main content |
| Small | 14px | Regular | Secondary text |
| Caption | 12px | Regular | Labels, hints |

### Color Usage

| Purpose | Recommendation |
| ------- | -------------- |
| Primary | Main brand color, CTAs |
| Secondary | Supporting actions |
| Success | #22C55E range (confirmations) |
| Warning | #F59E0B range (caution) |
| Error | #EF4444 range (errors) |
| Neutral | Gray scale for text/borders |

## Common Layouts

### Mobile Screen (375×812)

```text
┌─────────────────────────────┐
│ Status Bar (44px)           │
├─────────────────────────────┤
│ Header/Nav (56px)           │
├─────────────────────────────┤
│                             │
│ Content Area                │
│ (Scrollable)                │
│ Padding: 16px horizontal    │
│                             │
├─────────────────────────────┤
│ Bottom Nav/CTA (84px)       │
└─────────────────────────────┘

```

### Desktop Dashboard (1440×900)

```text
┌──────┬──────────────────────────────────┐
│      │ Header (64px)                    │
│ Side │──────────────────────────────────│
│ bar  │ Page Title + Actions             │
│      │──────────────────────────────────│
│ 240  │ Content Grid                     │
│ px   │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │
│      │ │Card │ │Card │ │Card │ │Card │ │
│      │ └─────┘ └─────┘ └─────┘ └─────┘ │
│      │                                  │
└──────┴──────────────────────────────────┘

```

## Component Checklist

### Buttons

- [ ] Clear, action-oriented label (2-3 words)
- [ ] Minimum touch target: 44×44px
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
- [ ] Maximum 7±2 top-level items
- [ ] Touch-friendly on mobile (48px targets)

## Accessibility Quick Checks

1. **Color contrast**: Text 4.5:1, Large text 3:1
2. **Touch targets**: Minimum 44×44px
3. **Focus states**: Visible keyboard focus indicators
4. **Alt text**: Meaningful descriptions for images
5. **Hierarchy**: Proper heading levels (H1→H2→H3)
6. **Color independence**: Never rely solely on color

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

Use these validation approaches with `mcp__penpot__execute_code`:

| Check | Method |
| ----- | ------ |
| Elements outside bounds | `penpotUtils.analyzeDescendants()` with `isContainedIn()` |
| Text too small (<12px) | `penpotUtils.findShapes()` filtering by `fontSize` |
| Missing contrast | Call `mcp__penpot__export_shape` and visually inspect |
| Hierarchy structure | `penpotUtils.shapeStructure()` to review nesting |

### Export CSS

Use `penpot.generateStyle(selection, { type: 'css', includeChildren: true })` via `mcp__penpot__execute_code` to extract CSS from designs.

## Tips for Great Designs

1. **Start with content**: Real content reveals layout needs
2. **Design mobile-first**: Constraints breed creativity
3. **Use a grid**: 8px base grid keeps things aligned
4. **Limit colors**: 1 primary + 1 secondary + neutrals
5. **Limit fonts**: 1-2 typefaces maximum
6. **Embrace whitespace**: Breathing room improves comprehension
7. **Be consistent**: Same action = same appearance everywhere
8. **Provide feedback**: Every action needs a response

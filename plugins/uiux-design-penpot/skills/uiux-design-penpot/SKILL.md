---
name: uiux-design-penpot
description: "Creates and reviews UI/UX designs in Penpot through its MCP tools: screens for web, mobile and desktop, design systems with components and tokens, dashboards, forms, navigation and landing pages, with accessibility and platform guidelines (iOS, Android, Material). Use for \"design a UI\", \"create interface\", \"design dashboard\", \"design landing page\" in Penpot or when no design tool is named. For Figma use uiux-design-figma."
---

# Penpot UI/UX Design Guide

Create professional, user-centered designs in Penpot using the MCP server built into Penpot (2.15+, verified on 2.18) and proven UI/UX principles.

## Available MCP Tools

| Tool | Purpose |
|-|-|
| `mcp__penpot__high_level_overview` | API primer. Call once per session before other Penpot tools (the server asks for this) |
| `mcp__penpot__execute_code` | Run JavaScript in the Penpot plugin context to create/modify designs |
| `mcp__penpot__export_shape` | Export shapes as PNG/SVG for visual inspection (`shapeId` or `"selection"` / `"page"`) |
| `mcp__penpot__penpot_api_info` | Retrieve Penpot API documentation per type/member |

There is **no `import_image` tool** on the built-in server. Import images inside `execute_code` with `await penpot.uploadMediaUrl(name, url)` (set the result as a `fillImage`) or `penpot.createShapeFromSvg(svg)` for icons.

## MCP Server Setup

The server runs inside the user's Penpot instance at `https://<penpot-host>/mcp/stream?userToken=<MCP key>`. It executes code through a **Penpot browser tab** that has a design file open and is connected. For admin enablement, client config and troubleshooting, see [setup-troubleshooting.md](references/setup-troubleshooting.md).

### Before Setup: Check the Connection

1. **Smoke test**: call `mcp__penpot__execute_code` with `return { version: penpot.version, file: penpot.currentFile?.name, page: penpot.currentPage?.name }`.
   - Returns a version and file → ready. Note the version: the workarounds in [mcp-known-issues.md](references/mcp-known-issues.md) are verified for 2.18.
   - Error about no connected plugin or instance → the client reaches the server, but no tab is connected. Ask the user to open the design file and choose **File → MCP Server → Connect**.
   - Penpot tools missing, or 401/404 → client config, key or server problem. Ask whether the MCP server is set up before walking through setup.
2. **Confirm the target**: the tools act on the file and page in the connected tab. Tell the user which file you are working in before you make changes.

### Quick Setup (Only If Not Configured)

1. Admin: `enable-mcp` in `PENPOT_FLAGS`, plus the `penpot-mcp` service. A reverse proxy must forward `/mcp/stream` and the WebSocket on `/mcp/ws`.
2. User: **Your account → Integrations → MCP Server** → turn on Status → create the MCP key → copy the URL.
3. Client (Claude Code): `claude mcp add --transport http --scope local penpot "https://<penpot-host>/mcp/stream?userToken=<key>"`. The key is a secret, so never commit it.
4. Penpot: open a design file → **File → MCP Server → Connect**.

### Connection Behaviour (2.18)

- **One tab** holds the MCP connection (choose it with the MCP status button). Code runs against that tab's current page.
- **Background tabs get throttled or frozen** and tool calls hang until the tab is focused again. Keep the tab visible during long sessions.
- **Idle sessions close after ~60 min.** If calls start failing, reconnect the tab (File → MCP Server → Connect).
- **Tool timeout**: `PENPOT_MCP_TOOL_TIMEOUT_S` (default 120 s). Split large generations into several calls.
- **`await` works** inside `execute_code`. Wait for async updates in the same call (`await new Promise(r => setTimeout(r, 150))`) instead of a follow-up call.
- **No rollback**: shapes created before an exception stay in the file. Store created ids in `storage` so you can clean up.
- **`penpot.currentUser` throws** `Permission user:read is not granted` on 2.18. Don't read user info.

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
| Snippets: shapes, z-order, grid, effects, text, library, page/viewport/events | [penpot-api-reference.md § Snippets](references/penpot-api-reference.md) |
| Color conversion utilities (OKLCH→hex, HSL→hex) | `uiux-design-system/references/color-utilities.md` |
| Penpot color API patterns (fills, gradients, library) | [penpot-color-patterns.md](references/penpot-color-patterns.md) |
| Token binding (resolver, toggle guard, brownfield sweep) | [token-binding.md](references/token-binding.md) |
| Prototyping, interactions & animations | [prototyping-interactions.md](references/prototyping-interactions.md) |
| Flex vs Grid layout decision (**read before step 5**) | [generation-recipes.md § Layout Selection Guide](references/generation-recipes.md) + `uiux-design-system/references/layout-patterns.md` |
| Reusable execute_code generation templates | [generation-recipes.md](references/generation-recipes.md) |

## Design Workflow

Copy this checklist and track progress:

```
Design Progress:
- [ ] 1. Smoke test the connection, note penpot.version and the target file/page
- [ ] 2. Discover the design system (tokens, library components, colors in use)
- [ ] 3. Inspect the page structure (penpotUtils.shapeStructure)
- [ ] 4. Pick a free canvas position for new boards
- [ ] 5. Build with layouts (grid outside, flex inside) and bind tokens inline
- [ ] 6. Export and inspect, fix, export again until it passes
- [ ] 7. Run the review checklists (component, accessibility, design review)
```

**Step 2**: see "Design System Handling" below. Always prefer the user's tokens over the defaults.

**Step 3**: `penpotUtils.shapeStructure(penpot.root, 3)`. Find elements with `penpotUtils.findShapes(predicate, root)`.

**Step 5, choosing a layout:**
- **Flex** (`addFlexLayout()`): 1D flow (rows, columns, wrapping tags, nav items). Items size to their content
- **Grid** (`addGridLayout()`): 2D structure or parent-controlled equal sizing (card grids with `'flex', 1` tracks, dashboards, sidebar + header + main)
- **Nested**: grid for outer structure, flex inside each component
- **Rule of thumb**: if you are setting properties on *children* to fix sizing, use Grid instead
- Read [generation-recipes.md](references/generation-recipes.md) § "Layout Selection Guide" before generating. Do not default to flex for everything

**Step 6, the feedback loop:** call `mcp__penpot__export_shape` on each new board and look at the image. Check for overflow, clipped text, children outside the board, contrast and spacing rhythm. Fix the problem, then export again. Only move on when the export looks right. For programmatic checks, see "Validating Designs" below.

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
- **Slash normalization** — `board.name = 'atoms/button'` becomes `'atoms / button'` (spaces injected). Normalise `" / "` before comparing names, never exact `===` on raw input
- **Component names**: name the shape with the full path (`'Card/Default'`) *before* `createComponent`. The result is `comp.path` `"Card"`, `comp.name` `"Default"`, main instance `"Card / Default"`. Setting `comp.name` with slashes afterwards **appends** to the existing path (`"Button / Button"`), so rename the leaf only. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **`openPage()` is async**: `penpot.currentPage` switches ~300 ms later. `await` before creating shapes and check `currentPage.id`. `createPage()` does not switch pages
- **`layoutChild` is null before parenting** — always `parent.appendChild(child)` first, then access `child.layoutChild`
- **`applyToken()` property names**: on 2.18, `['fontFamilies']` and `['all']` throw `should be a set of strings` (the binding key is `fontFamily`). Pass `'fill'`/`'strokeColor'` only for color tokens. For all other types, **omit the properties arg** and read the key from `shape.tokens`. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **Token API takes object args only** (2.18): `addSet({ name })`, `addToken({ type, name, value })`, `addTheme({ group, name })`. Positional forms throw `Value not valid`
- **Child positioning is page-absolute** — after `board.appendChild(child)`, `child.x = N` sets page coordinates, not board-relative. Use `penpotUtils.setParentXY(child, relX, relY)` or flex/grid layouts. Nested boards need recursive fixing. See [mcp-known-issues.md](references/mcp-known-issues.md)
- **Async property updates**: after `toggleActive()`, `applyToken()`, `openPage()` or `growType` changes, computed properties update asynchronously. `await` 100-300 ms in the same call, or use `await penpot.waitForLayoutUpdate()` for flex/grid layout changes

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

## Design Tokens API

Penpot has a built-in design tokens system (17 token types). On 2.18 every token method takes **object arguments**. See [mcp-known-issues.md](references/mcp-known-issues.md) for full details.

```javascript
const catalog = penpot.library.local.tokens;

// Create a token set (returns a usable proxy; new sets start INACTIVE)
const set = catalog.addSet({ name: "Brand/Colors" });

// Add tokens: object form { type, name, value }
// 17 types (use EXACT strings): borderRadius, borderWidth, color,
// dimension, fontFamilies, fontSizes, fontWeights, letterSpacing,
// number, opacity, rotation, shadow, sizing, spacing, textCase,
// textDecoration, typography
set.addToken({ type: "color", name: "primary", value: "#3B82F6" });
set.addToken({ type: "spacing", name: "md", value: "16" });
set.addToken({ type: "borderRadius", name: "lg", value: "12" });
set.addToken({ type: "spacing", name: "ref", value: "{spacing.md}" }); // references work

// Activate set
if (!set.active) set.toggleActive();

// Themes
catalog.addTheme({ group: "Mode", name: "Light" });
catalog.addTheme({ group: "Mode", name: "Dark" });

// Apply token to shape (toggle! check shape.tokens first)
const token = set.tokens.find(t => t.name === "primary");
if (shape.tokens?.fill !== token.name) shape.applyToken(token, ['fill']); // 'fill' | 'strokeColor'
```

**Gotchas:** Duplicate token names (or a name that collides with an existing group prefix) **throw**. Check `set.tokens` first. On an empty catalog, guard the first `catalog.sets` read with try/catch. See [mcp-known-issues.md](references/mcp-known-issues.md) for the full working flow and all workarounds.

### Token Binding

**Every shape should be bound to its semantic token** — not just have a hardcoded hex value. Without binding, changing a token value won't propagate to shapes.

- **Greenfield** (creating new shapes): bind tokens inline during creation. See [generation-recipes.md](references/generation-recipes.md) for the `initTokenResolver()` + `tokenMap` pattern.
- **Brownfield** (existing file with unbound tokens): run the binding sweep from [token-binding.md](references/token-binding.md). Auto-applies high-confidence bindings, surfaces ambiguous ones for user confirmation.
- **Strategy & confidence scoring**: see `uiux-design-system/references/token-binding-strategy.md` for the tool-agnostic methodology.

**Trigger phrases:** "bind tokens to shapes", "wire up tokens", "audit token bindings", "tokens aren't applied", "tokens aren't working".

**Critical:** `applyToken()` is a **toggle** in Penpot — calling it on an already-bound shape unbinds the token. Always check `shape.tokens` before applying. See [token-binding.md](references/token-binding.md) for the `applySafe()` toggle guard.

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
|-|-|-|
| `spacing-xs` | 4px | Tight inline elements |
| `spacing-sm` | 8px | Related elements |
| `spacing-md` | 16px | Default padding |
| `spacing-lg` | 24px | Section spacing |
| `spacing-xl` | 32px | Major sections |
| `spacing-2xl` | 48px | Page-level spacing |

### Typography Scale

| Level | Size | Weight | Usage |
|-|-|-|-|
| Display | 48-64px | Bold | Hero headlines |
| H1 | 32-40px | Bold | Page titles |
| H2 | 24-28px | Semibold | Section headers |
| H3 | 20-22px | Semibold | Subsections |
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

### Mobile Screen (375×812)

```text
+-----------------------------+
| Status Bar (44px)           |
+-----------------------------+
| Header/Nav (56px)           |
+-----------------------------+
|                             |
| Content Area                |
| (Scrollable)                |
| Padding: 16px horizontal    |
|                             |
+-----------------------------+
| Bottom Nav/CTA (84px)       |
+-----------------------------+

```

### Desktop Dashboard (1440×900)

```text
+------+----------------------------------+
|      | Header (64px)                    |
| Side +----------------------------------+
| bar  | Page Title + Actions             |
|      +----------------------------------+
| 240  | Content Grid                     |
| px   | +-----+ +-----+ +-----+ +-----+  |
|      | |Card | |Card | |Card | |Card |  |
|      | +-----+ +-----+ +-----+ +-----+  |
|      |                                  |
+------+----------------------------------+

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
|-|-|
| Elements outside bounds | `penpotUtils.analyzeDescendants()` with `isContainedIn()` |
| Text too small (<12px) | `penpotUtils.findShapes()` filtering by `fontSize` |
| Missing contrast | Call `mcp__penpot__export_shape` and visually inspect |
| Hierarchy structure | `penpotUtils.shapeStructure()` to review nesting |

### Export CSS

Use `penpot.generateStyle(selection, { type: 'css', includeChildren: true })` via `mcp__penpot__execute_code` to extract CSS from designs.

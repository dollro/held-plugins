# Penpot MCP Known Issues & Workarounds

> API bugs, workarounds and correct patterns for the Penpot MCP server built into Penpot.
> Verified against **Penpot 2.18.5** (built-in MCP, `/mcp/stream`). Older notes came from the standalone `penpot-mcp` server on Penpot ≤2.13.

## Contents

- Status Key
- Token API: Object Arguments Only
- applyToken(): Property Names and Errors
- Async Updates: await Inside the Same Call
- openPage() Is Async
- createText('') Returns Null
- Component Naming
- Absolute vs Relative Positioning
- layoutChild Is Null Before Parenting
- resize() Is a Method, Not a Property
- Permissions: currentUser Needs user:read
- Images: No import_image Tool
- Orphaned Shapes After a Failed Call
- WASM Renderer Crash on Bulk Font Changes + Page Switch
- Quick Reference: Common Pitfalls (2.18)

---

## Status Key

| Status | Meaning |
|-|-|
| **FIXED (2.18)** | Was broken on older versions, verified working on 2.18.5 |
| **PRESENT (2.18)** | Verified still present on 2.18.5 |
| **BY DESIGN** | Correct API behaviour, caller must adapt |
| **UNVERIFIED** | Seen on older versions, not re-tested on 2.18 |

If `penpot.version` is below 2.18, assume the older behaviour and test before relying on any fix listed here.

---

## Token API: Object Arguments Only

**Status: FIXED (2.18)**

On 2.18 the object form is the only working form. Positional arguments throw `Value not valid`.

| Method | Works (2.18) | Throws |
|-|-|-|
| `catalog.addSet` | `addSet({ name: "x" })` | `addSet("x")` |
| `set.addToken` | `addToken({ type: "color", name: "x", value: "#FFF" })` | `addToken("color", "x", "#FFF")` |
| `catalog.addTheme` | `addTheme({ group: "Mode", name: "Light" })` | positional form (not re-tested, assume it throws) |

- `addSet()` returns a usable proxy with a valid `id`. The old read-back workaround is no longer needed.
- New sets start **inactive**. Call `if (!set.active) set.toggleActive()`.
- Numbers are coerced to strings (`value: 16` is stored as `"16"`). Strings are still the safe choice.
- `fontFamilies` values are stored as arrays (`"Inter"` becomes `["Inter"]`).
- References work: `value: "{color.primary}"`.
- Other useful members: `set.remove()`, `set.duplicate()`, `set.tokensByType`, `catalog.getSetById(id)`, `catalog.getThemeById(id)`.

### Duplicate Token Names Throw

**Status: FIXED (2.18)** (it used to return `undefined` silently)

```javascript
set.addToken({ type: "color", name: "color.blue.500", value: "#2563EB" }); // ok
set.addToken({ type: "color", name: "color.blue.500", value: "#FF0000" });
// throws: "A token already exists at the path: color.blue.500 or at a prefix thereof."
```

A name can't be both a token and a group prefix: once `color.blue` is a token, `color.blue.500` is rejected too. Guard with `set.tokens.some(t => t.name === name)` or catch the error.

### catalog.sets on an Empty Catalog

**Status: UNVERIFIED** (crashed on older versions with `No protocol method ITokenSets.get-sets defined for type null`)

Wrap the first `catalog.sets` read in try/catch on a file that has no tokens yet. If it throws, create a set first.

### Token Types

`type` must be one of these exact strings:

| TokenType string | Example value | Notes |
|-|-|-|
| `"borderRadius"` | `"8"` | |
| `"borderWidth"` | `"1"` | |
| `"color"` | `"#2563EB"` | Hex string with `#` |
| `"dimension"` | `"16"` | |
| `"fontFamilies"` | `"Inter"` | Type is plural, but the binding property is `fontFamily` (see applyToken) |
| `"fontSizes"` | `"16"` | Type is plural |
| `"fontWeights"` | `"600"` | |
| `"letterSpacing"` | `"-0.025em"` | |
| `"number"` | `"1.5"` | Unitless |
| `"opacity"` | `"0.5"` | 0-1 range |
| `"rotation"` | `"45"` | Degrees |
| `"shadow"` | `"0 4 6 -1 #0000001A"` | `offsetX offsetY blur spread color` |
| `"sizing"` | `"24"` | |
| `"spacing"` | `"{dimension.4}"` | References work |
| `"textCase"` | `"uppercase"` | |
| `"textDecoration"` | `"underline"` | |
| `"typography"` | — | Composite type |

### Full Working Token Flow (2.18)

```javascript
const catalog = penpot.library.local.tokens;

const prim = catalog.addSet({ name: "primitives" });
prim.addToken({ type: "color", name: "color.blue.500", value: "#2563EB" });
prim.addToken({ type: "dimension", name: "dimension.4", value: "16" });
prim.addToken({ type: "borderRadius", name: "borderRadius.md", value: "8" });
prim.addToken({ type: "spacing", name: "spacing.md", value: "{dimension.4}" });
if (!prim.active) prim.toggleActive();

const sem = catalog.addSet({ name: "semantic" });
sem.addToken({ type: "color", name: "bg.body", value: "{color.blue.500}" });
if (!sem.active) sem.toggleActive();

catalog.addTheme({ group: "Mode", name: "Light" });
catalog.addTheme({ group: "Mode", name: "Dark" });
```

---

## applyToken(): Property Names and Errors

**Status: PRESENT (2.18)**, but now it throws instead of failing silently

Some binding property names differ from the documented `TokenProperty` names. On 2.18.5:

| Call | Result |
|-|-|
| `shape.applyToken(colorToken, ['fill'])` | binds (`shape.tokens` → `{ fill: ... }`) |
| `shape.applyToken(colorToken, 'fill')` | binds (a string is accepted too) |
| `shape.applyToken(colorToken)` | binds to `fill` |
| `text.applyToken(fontFamiliesToken, ['fontFamilies'])` | **throws** `Field 1 is invalid: should be a set of strings` |
| `text.applyToken(fontFamiliesToken, ['all'])` | **throws** the same error |
| `text.applyToken(fontFamiliesToken, ['fontFamily'])` | binds (`shape.tokens` → `{ fontFamily: ... }`) |
| `text.applyToken(fontFamiliesToken)` | binds to `fontFamily` |
| `token.applyToShapes([text], ['fontFamilies'])` | **throws** the same error |

**Safe pattern:**
- Color tokens: pass `'fill'` or `'strokeColor'` to choose fill or stroke.
- Every other type: **omit the properties argument**, then read the key Penpot used from `shape.tokens`.
- If you get `should be a set of strings`, the property name is wrong for this version. It is not a wrong argument shape.
- 2.19 accepts `fontFamilies` as the property name (CHANGES.md #11405). On 2.18, use `fontFamily` or omit the argument.

```javascript
shape.applyToken(colorToken, ['fill']);
shape.applyToken(colorToken, ['strokeColor']);
shape.applyToken(radiusToken);
shape.applyToken(fontFamilyToken);   // binds as "fontFamily"
shape.applyToken(fontSizeToken);
```

**applyToken() is a toggle.** **PRESENT (2.18)**: calling it again with the token that is already bound **unbinds** it, with no error. Always check `shape.tokens` first. See the `applySafe()` guard in [token-binding.md](token-binding.md).

Application is asynchronous: `await` ~100-200 ms before reading `shape.tokens` or the resolved values.

---

## Async Updates: await Inside the Same Call

**Status: BY DESIGN**

`execute_code` runs as an async function body, so top-level `await` works. You no longer need a separate tool call to read async results:

```javascript
const sleep = ms => new Promise(r => setTimeout(r, ms));
text.growType = 'auto-width';
await sleep(150);
return text.width; // updated
```

This applies to `openPage()`, `applyToken()`, `toggleActive()` and `growType` auto-sizing. Keep each call well under the execution timeout (`PENPOT_MCP_TOOL_TIMEOUT_S`, default 120 s).

For flex/grid layout changes, 2.18 adds `penpot.waitForLayoutUpdate()` (present on 2.18.5). Prefer it over a fixed sleep before reading layout-computed sizes.

---

## openPage() Is Async

**Status: FIXED (2.18)**: the switch now works on upstream Penpot. It is no longer synchronous.

```javascript
const page = penpot.createPage();   // does NOT switch to the new page
page.name = 'my-page';
penpot.openPage(page);
penpot.currentPage.name;            // still the old page
await new Promise(r => setTimeout(r, 300));
penpot.currentPage.name;            // "my-page"
penpot.createRectangle();           // lands on my-page
```

Always `await` ~300 ms after `openPage()` before creating shapes, or create the shapes on the next call. Check that `penpot.currentPage.id === page.id`.

---

## createText('') Returns Null

**Status: PRESENT (2.18)**

```javascript
penpot.createText('');    // null
penpot.createText('  ');  // valid Text
penpot.createText('x');   // valid Text
```

**Defensive pattern:**

```javascript
function safeText(content, opts = {}) {
  if (!content || content.trim() === '') return null;
  const t = penpot.createText(content);
  if (!t) return null;
  if (opts.fontFamily) t.fontFamily = opts.fontFamily;
  if (opts.fontSize) t.fontSize = opts.fontSize;
  if (opts.fontWeight) t.fontWeight = opts.fontWeight;
  if (opts.fills) t.fills = opts.fills;
  t.growType = opts.growType || 'auto-width';
  return t;
}
```

---

## Component Naming

### Slash Normalization

**Status: BY DESIGN**

```javascript
board.name = 'atoms/button/primary';
board.name; // "atoms / button / primary" (spaces are added around slashes)
```

Match names loosely, for example by normalising both sides: `s.name.replace(/\s*\/\s*/g, '/') === 'atoms/button'`.

### createComponent Splits Path and Name

**Status: FIXED (2.18)**: the main instance name is no longer doubled.

```javascript
board.name = 'Card/Default';
const comp = penpot.library.local.createComponent([board]);
comp.name;                 // "Default"  (leaf only)
comp.path;                 // "Card"
comp.mainInstance().name;  // "Card / Default"
```

**Name the shape with the full path before `createComponent`**, and don't rename afterwards.

### Setting comp.name With Slashes Appends to the Path

**Status: PRESENT (2.18)**

```javascript
// comp.path === "Button", comp.name === "Primary"
comp.name = 'Button/Primary';
comp.path;                 // "Button / Button" (doubled)
comp.mainInstance().name;  // "Button / Button / Primary"
```

If you must rename after registration, set only the leaf (`comp.name = 'Primary'`). On a component with an empty path, a slashed name is safe (`'Chip'` → `comp.name = 'Chip/Selected'` gives path `Chip`, name `Selected`).

---

## Absolute vs Relative Positioning

**Status: BY DESIGN** (verified on 2.18.5)

After `board.appendChild(child)`, `child.x = 10` uses **page coordinates**. With the board at x=1000, the child ends up at page x=10 (`parentX` -990), outside the board.

```javascript
// WRONG: child ends up outside the board
board.appendChild(child);
child.x = 32;

// CORRECT: relative to the parent
board.appendChild(child);
penpotUtils.setParentXY(child, 32, 100);

// BEST: flex/grid layout positions children for you
board.addFlexLayout();
board.appendChild(child);
```

### Recursive Fix for Nested Boards

```javascript
function fixBoard(board) {
  for (const child of board.children || []) {
    penpotUtils.setParentXY(child, child.x - board.x, child.y - board.y);
    if (child.type === 'board' && child.children?.length) fixBoard(child);
  }
}
```

Use manual positioning only for absolutely positioned overlays (badges, tooltips).

---

## layoutChild Is Null Before Parenting

**Status: BY DESIGN** (verified on 2.18.5)

```javascript
const child = penpot.createRectangle();
child.layoutChild;                           // null
parent.appendChild(child);                   // parent the child FIRST
child.layoutChild.horizontalSizing = 'fix';  // THEN set its layout properties
```

---

## resize() Is a Method, Not a Property

**Status: BY DESIGN**

```javascript
shape.resize(80, 80);           // CORRECT
shape.width = 80;               // no effect (read-only)
shape.resize(80, shape.height); // set width only
shape.parentX = 50;             // no effect (read-only)
penpotUtils.setParentXY(shape, 50, 50);
```

`resize()` on a Text resets `growType` to `"fixed"`. Set it back afterwards.

---

## Permissions: currentUser Needs user:read

**Status: BY DESIGN (2.18)**

With the built-in MCP on 2.18, `penpot.currentUser` and `activeUsers` throw `Permission user:read is not granted`. The cause is that the MCP plugin manifest grants only `library`, `comment` and `content` read/write. No setting can grant `user:read`. 2.19 adds `user:read` to the manifest. Don't read user info in scripts. Everything else used in this skill (file, pages, shapes, library, tokens) works.

---

## Images: No import_image Tool

**Status: 2.18 built-in MCP**

The built-in server exposes only `high_level_overview`, `execute_code`, `export_shape` and `penpot_api_info`. To add images, run one of these inside `execute_code`:

- `await penpot.uploadMediaUrl(name, url)` → `Promise<ImageData>`, then set it as a fill: `shape.fills = [{ fillOpacity: 1, fillImage: imageData }]`
- `penpot.uploadMediaData(name, bytes, mimeType)` for inline data
- `penpot.createShapeFromSvg(svgString)` for icons (preferred for vector icons)

---

## Orphaned Shapes After a Failed Call

**Status: PRESENT (2.18)**

When `execute_code` throws partway through, the shapes it created before the error stay in the file. There is no rollback. On 2.18.5, a call that threw at `applyToken` still left its components and boards behind.

```javascript
const orphans = penpot.root.children.filter(c =>
  !expectedBoardNames.some(n => c.name.includes(n))
);
for (const o of orphans) o.remove();
```

Store the ids of shapes you create in `storage` so you can clean up precisely. Wrap multi-shape operations in try/catch.

---

## WASM Renderer Crash on Bulk Font Changes + Page Switch

**Status: UNVERIFIED**

Bulk `fontFamily` changes across several pages in one `execute_code` call have crashed the WASM text renderer (`_set_shape_text_content → fonts_from_text_content → initialize_viewport`). Data is safe. Reload the file to recover.

**Workaround:** one page per `execute_code` call. Switch the page, `await`, change the fonts, then return.

---

## Quick Reference: Common Pitfalls (2.18)

| Pitfall | Correct Pattern |
|-|-|
| Positional token args | Object form only: `addSet({ name })`, `addToken({ type, name, value })` |
| New set has no effect | Sets start inactive: `if (!set.active) set.toggleActive()` |
| Duplicate token name | Throws. Check `set.tokens` first |
| `applyToken(t, ['fontFamilies'])` throws | Omit properties for non-color tokens. The binding key is `fontFamily` |
| Re-applying a bound token | It's a toggle and unbinds. Check `shape.tokens` first |
| Reading async results | `await sleep(150)` in the same call |
| `openPage()` then create | `await` ~300 ms, check `currentPage.id` |
| Renaming a component with slashes | Name the shape before `createComponent`, rename the leaf only |
| Exact name match after a slash | Normalise `" / "` before comparing |
| `createText('')` | Guard content before calling |
| `layoutChild` before parenting | `parent.appendChild(child)` first |
| `child.x = N` inside a board | `penpotUtils.setParentXY(child, relX, relY)` |
| `penpot.currentUser` | Not permitted. Don't read it |
| Importing images | `penpot.uploadMediaUrl()` / `createShapeFromSvg()` inside `execute_code` |

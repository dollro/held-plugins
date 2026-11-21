# Token Binding — Penpot Implementation

## Contents

- Token Resolver Utility
- Greenfield Pattern — Inline Binding During Creation
- Recommended Brownfield Procedure
- Brownfield Sweep Recipe
- Property Extraction Helpers
- Penpot-Specific Gotchas

Penpot-specific patterns for binding design tokens to shapes. Implements the
strategies defined in `uiux-design-system/references/token-binding-strategy.md`.

> **Key constraint:** `applyToken()` is a **toggle** in Penpot — calling it on an
> already-bound shape **unbinds** the token. Always check `shape.tokens` before applying.

---

## Token Resolver Utility

Reusable helper for `execute_code` calls. Paste at the top of any token-binding script.

```javascript
function initTokenResolver() {
  const catalog = penpot.library.local.tokens;
  const sets = catalog.sets;
  const _cache = {};
  return {
    resolve(setName, tokenName) {
      const key = setName + '/' + tokenName;
      if (_cache[key]) return _cache[key];
      const set = sets.find(s => s.name === setName);
      if (!set) return null;
      const token = set.tokens.find(t => t.name === tokenName);
      _cache[key] = token || null;
      return _cache[key];
    },
    // Look a token up by name: semantic set first, then primitives
    find(tokenName, order = ['semantic', 'primitives']) {
      for (const setName of order) {
        const t = this.resolve(setName, tokenName);
        if (t) return t;
      }
      return null;
    },
    applySafe(shape, token, properties) {
      if (!token) return false;
      // Toggle guard: applyToken() is a toggle, calling twice UNBINDS.
      // shape.tokens maps property -> token name, e.g. { fill: "bg.body", fontFamily: "font.sans" }
      // Color tokens: compare shape.tokens[prop]. Other types (properties omitted):
      // the key is chosen by Penpot, so check Object.values(shape.tokens) instead.
      const existing = shape.tokens || {};
      const props = properties ? [].concat(properties) : null;
      const bound = props
        ? props.every(p => existing[p] === token.name)
        : Object.values(existing).includes(token.name);
      if (bound) return false;
      shape.applyToken(token, props || undefined);
      return true;
    }
  };
}
```

---

## Greenfield Pattern — Inline Binding During Creation

When creating new shapes, set the visual property **and** bind the token in the same pass.

```javascript
// Before (hardcoded):
rect.fills = [{ fillColor: '#3B82F6', fillOpacity: 1 }];

// After (token-bound):
const TR = initTokenResolver();
rect.fills = [{ fillColor: tokenMap['bg.interactive'], fillOpacity: 1 }];
TR.applySafe(rect, TR.resolve('semantic', 'bg.interactive'), 'fill');
```

### Property Strings by Token Type

> **CRITICAL:** on Penpot 2.18, some documented property names are rejected:
> `['fontFamilies']` and `['all']` throw `should be a set of strings` (the real key
> is `fontFamily`). Only pass `'fill'` or `'strokeColor'` for color tokens. For ALL
> other types, **omit the properties argument** and read the key back from `shape.tokens`.
> See `mcp-known-issues.md` § "applyToken(): Property Names and Errors".

| Token type | `properties` arg | Notes |
|-|-|-|
| Color (fill) | `'fill'` | Maps to `fillColor` of the FIRST fill |
| Color (stroke) | `'strokeColor'` | Maps to first stroke color |
| borderRadius | **omit** | |
| shadow | **omit** | |
| spacing | explicit (`paddingLeft`, `rowGap`, ...) | Omitting may silently apply nothing (upstream PR #10668, unverified on 2.18.5). Check `shape.tokens` after |
| sizing | **omit** | |
| fontFamilies | **omit** | 2.18: `'fontFamilies'` throws; binds as `fontFamily` |
| fontSizes | **omit** | |
| fontWeights | **omit** | |
| All other types | **omit** | Safe default — let Penpot resolve the property |

---

## Recommended Brownfield Procedure

**Status: verified on 2.18, Oct 2026** (886 bindings across a component library, 0 visual changes)

Use this for any real file. The quick sweep below is the minimal version without the safety steps. Work **one page per write call** and read [setup-troubleshooting.md § Long-Running Sessions](setup-troubleshooting.md) first: timeouts, batch size and `storage` wipes all apply here.

1. **Dry run.** Classify every candidate (`fill`, `strokeColor`, `borderRadius`, `fontSize`, `fontWeight`) into *auto* (one token) or *ambiguous* (with a reason) per page. Store the plan and report counts plus the ambiguous groups, e.g. `"fill #E8503A (link vs danger)": 7`, before writing anything. Ask the user to settle the ambiguous groups.
2. **Apply in capped batches.** 40 `applyToken` calls per `execute_code` call is reliable (~80 was too slow on a 112-shape page). Return the remaining count. The toggle guard makes every batch idempotent, so a re-run after a timeout is safe.
3. **Verify each page** before moving on (see below), then export one board and look at it.

### Classifier Rules

Build a **context string** for each shape: its own and its ancestors' names, lowercased and joined. Then:

| Candidate | Token family |
|-|-|
| Text fill | `color.text.*` |
| Stroke | `color.border.*` |
| Non-text fill | `color.background.*` / `color.feedback.*` |
| Any color inside a `button` context | `color.interactive.*` (white text → `interactive.<variant>.fg`) |
| `borderRadius` 9999 | `radius.button` / `radius.input` / `radius.badge` by context |
| Same hex maps to two semantic tokens, no context decides | **ambiguous**, ask the user |

- **Skip component copies** (`shape.isComponentCopyInstance()`). Bind the main components; instances inherit.
- **Exclude foundations / reference swatch pages** from semantic sweeps. Their swatches document primitives and must stay on primitive tokens.
- **Token lookup**: resolve a name in the semantic set first, then in primitives (`TR.find(name)` below).

```javascript
function contextOf(shape) {
  const names = [];
  for (let s = shape; s; s = s.parent) names.push((s.name || '').toLowerCase());
  return names.join(' > ');
}

// Re-runnable: recompute the plan from the file instead of trusting storage
function buildPlan(classify) {
  const plan = [], ambiguous = {};
  for (const shape of penpot.currentPage.findShapes()) {
    if (shape.isComponentCopyInstance?.()) continue;
    for (const c of classify(shape, contextOf(shape))) { // -> [{ prop, value, token | reason }]
      if (c.token) plan.push({ id: shape.id, prop: c.prop, value: c.value, token: c.token });
      else { const k = `${c.prop} ${c.value} (${c.reason})`; ambiguous[k] = (ambiguous[k] || 0) + 1; }
    }
  }
  return { plan, ambiguous };
}

async function applyPlan(plan, TR, max = 40) {
  let applied = 0, already = 0;
  for (const item of plan) {
    const shape = penpot.currentPage.getShapeById(item.id);
    const token = TR.find(item.token);
    if (!shape || !token) continue;
    if (applied >= max) break;
    const prop = ['fill', 'strokeColor'].includes(item.prop) ? item.prop : undefined;
    if (TR.applySafe(shape, token, prop)) applied++; else already++;
  }
  await new Promise(r => setTimeout(r, 200));
  return { applied, already, remaining: plan.length - applied - already };
}
```

### Verify After Each Page

For each planned item check (a) `Object.values(shape.tokens)` includes the token name and (b) the visual value is unchanged: fill/stroke hex, `borderRadius`, `fontSize`, `fontWeight`. Report `ok` / `notBound` / `changed`. Anything in `changed` means the token value differs from the hardcoded value. Unbind it and put it in the ambiguous list.

```javascript
function verify(plan) {
  const r = { ok: 0, notBound: [], changed: [] };
  for (const item of plan) {
    const s = penpot.currentPage.getShapeById(item.id);
    if (!s) continue;
    if (!Object.values(s.tokens || {}).includes(item.token)) { r.notBound.push(item); continue; }
    const now = String(extractBindableProps(s)[item.prop] ?? '').toUpperCase();
    if (now !== String(item.value).toUpperCase()) r.changed.push({ ...item, now });
    else r.ok++;
  }
  return { ok: r.ok, notBound: r.notBound.length, changed: r.changed.slice(0, 20) };
}
```

---

## Brownfield Sweep Recipe

Minimal version of the procedure above, without dry run or verification. Sweep an existing page to bind tokens to shapes whose visual properties match token values.

> **One page per `execute_code` call.** WASM renderer crashes on bulk font changes
> combined with page switches. See `mcp-known-issues.md` for details.

```javascript
// --- Paste initTokenResolver() and extractBindableProps() above this line ---

// Reverse map: value → { setName, tokenName, property }
// Build from your token definitions or pass in as a parameter
const REVERSE_MAP = {
  '#3B82F6': { set: 'semantic', token: 'bg.interactive', prop: 'fill' },
  '#EF4444': { set: 'semantic', token: 'bg.danger', prop: 'fill' },
  '#1E293B': { set: 'semantic', token: 'fg.default', prop: 'fill' },
  '8':       { set: 'primitives', token: 'borderRadius.md', prop: undefined },
  // ... extend with all token values
};

const TR = initTokenResolver();
const shapes = penpot.currentPage.findShapes();
let bound = 0;
let skipped = 0;

for (const shape of shapes) {
  const props = extractBindableProps(shape);
  for (const [propKey, value] of Object.entries(props)) {
    const match = REVERSE_MAP[value];
    if (!match) continue;
    const token = TR.resolve(match.set, match.token);
    if (TR.applySafe(shape, token, match.prop)) {
      bound++;
    } else {
      skipped++;
    }
  }
}

return { bound, skipped, totalShapes: shapes.length };
```

---

## Property Extraction Helpers

```javascript
function extractBindableProps(shape) {
  const props = {};
  if (shape.fills?.length && shape.fills[0].fillColor)
    props.fill = shape.fills[0].fillColor;
  if (shape.strokes?.length && shape.strokes[0].strokeColor)
    props.strokeColor = shape.strokes[0].strokeColor;
  if (shape.borderRadius)
    props.borderRadius = String(shape.borderRadius);
  if (shape.shadows?.length)
    props.shadow = shape.shadows.map(s =>
      `${s.offsetX} ${s.offsetY} ${s.blur} ${s.spread} ${s.color?.color || ''}`
    ).join('; ');
  // Text properties
  if (shape.type === 'text') {
    if (shape.fontSize) props.fontSize = String(shape.fontSize);
    if (shape.fontWeight) props.fontWeight = String(shape.fontWeight);
    if (shape.fontFamily) props.fontFamily = shape.fontFamily;
  }
  return props;
}
```

---

## Penpot-Specific Gotchas

| Gotcha | Detail |
|-|-|
| `applyToken()` is a toggle | Calling it on an already-bound shape **unbinds** the token. Read `shape.tokens` first. |
| `shape.tokens` is readonly | Exposes current bindings as an object. Use it to check before calling `applyToken()`. |
| Object args only (2.18) | `addSet({ name })`, `addToken({ type, name, value })`. Positional forms throw. |
| One page per sweep call | Bulk font changes + page switch in a single `execute_code` call crashes WASM renderer. |
| Slash normalization in names | `atoms/button` becomes `atoms / button`. Normalise `" / "` before comparing. |
| Duplicate token names throw | `addToken()` with an existing name (or group prefix) throws. Check `set.tokens` first. |
| `catalog.sets` on empty catalog | Crashed on older versions. Guard the first read with try/catch. |
| `resolvedValue` on shadow tokens | Throws (`…forEach is not a function`) on 2.18. Wrap in try/catch when inventorying all tokens. |
| Non-container top-level shapes | `penpot.root.children` can hold a stray text whose `.children` is undefined. Guard `(b.children \|\| [])`. |
| Large write batches | ~80 `applyToken` calls per call was too slow on 2.18; 40 is reliable. A timed-out call may still have completed. Verify before re-running. |
| `storage` lost after tab reload | Design changes persist, helpers don't. Recompute the plan from the file and resume. |

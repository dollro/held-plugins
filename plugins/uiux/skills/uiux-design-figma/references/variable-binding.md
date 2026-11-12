# Variable Binding — Figma Implementation

Figma-specific patterns for binding design variables to nodes. Implements the
strategies defined in `uiux-design-system/references/token-binding-strategy.md`
(greenfield/brownfield patterns, confidence scoring, coverage reporting).

Use inside `figma_execute` calls to connect visual properties to variables from
the Variables panel.

> **Key advantage over Penpot:** `setBoundVariable()` is **idempotent** — calling it
> on an already-bound node simply re-sets the binding. There is no toggle behavior,
> so no guard checks are needed.

---

## Variable Resolver Utility

Reusable helper for `figma_execute` calls. Paste at the top of any variable-binding script.

```javascript
async function initVarResolver() {
  const collections = await figma.variables.getLocalVariableCollectionsAsync();
  const _cache = {};
  return {
    async resolve(collectionName, varPath) {
      const key = collectionName + '/' + varPath;
      if (_cache[key] !== undefined) return _cache[key];
      const coll = collections.find(c => c.name === collectionName);
      if (!coll) { _cache[key] = null; return null; }
      for (const vid of coll.variableIds) {
        const v = await figma.variables.getVariableByIdAsync(vid);
        if (v && v.name === varPath) { _cache[key] = v; return v; }
      }
      _cache[key] = null;
      return null;
    },
    async bind(node, field, collectionName, varPath) {
      const v = await this.resolve(collectionName, varPath);
      if (v) node.setBoundVariable(field, v);
      return !!v;
    }
  };
}
const VR = await initVarResolver();
```

---

## Binding API

### `node.setBoundVariable(field, variable)`

Sets a variable binding on a node property. Idempotent — safe to call multiple times.

```javascript
const colorVar = await VR.resolve('semantic', 'bg/interactive');
node.setBoundVariable('fills', colorVar);
```

### `node.boundVariables`

Read-only object exposing current bindings. Use to inspect existing state.

```javascript
const bindings = node.boundVariables;
// { fills: [{ type: 'VARIABLE_ALIAS', id: 'VariableID:1:23' }], ... }
```

---

## Property Field Mapping

| Visual Property | `setBoundVariable` field | Variable Type | Notes |
|-|-|-|-|
| Fill color | `'fills'` | COLOR | Binds to first fill's color |
| Stroke color | `'strokes'` | COLOR | Binds to first stroke's color |
| Top-left radius | `'topLeftRadius'` | FLOAT | |
| Top-right radius | `'topRightRadius'` | FLOAT | |
| Bottom-left radius | `'bottomLeftRadius'` | FLOAT | |
| Bottom-right radius | `'bottomRightRadius'` | FLOAT | |
| Corner radius (uniform) | Bind all four individually | FLOAT | No single `cornerRadius` field |
| Item spacing | `'itemSpacing'` | FLOAT | Auto-layout gap |
| Padding top | `'paddingTop'` | FLOAT | |
| Padding right | `'paddingRight'` | FLOAT | |
| Padding bottom | `'paddingBottom'` | FLOAT | |
| Padding left | `'paddingLeft'` | FLOAT | |
| Width | `'width'` | FLOAT | Only for fixed-size nodes |
| Height | `'height'` | FLOAT | Only for fixed-size nodes |
| Opacity | `'opacity'` | FLOAT | 0-1 range |
| Visible | `'visible'` | BOOLEAN | Show/hide |

> **Corner radius:** Figma requires binding each corner separately. There is no
> single `cornerRadius` binding field. Bind all four for uniform radius:
>
> ```javascript
> for (const field of ['topLeftRadius', 'topRightRadius', 'bottomLeftRadius', 'bottomRightRadius']) {
>   await VR.bind(node, field, 'semantic', 'radius/md');
> }
> ```

---

## Greenfield Pattern — Inline Binding During Creation

When creating new nodes, set the visual property **and** bind the variable in the same pass.

```javascript
// Before (hardcoded):
frame.fills = [{ type: 'SOLID', color: { r: 0.23, g: 0.51, b: 0.96 } }];

// After (variable-bound):
frame.fills = [{ type: 'SOLID', color: hexToRgb(tokenMap['bg.interactive']) }];
await VR.bind(frame, 'fills', 'semantic', 'bg/interactive');
```

The visual value acts as a fallback if the variable is deleted. The binding ensures
the node updates when the variable value changes (e.g., switching Light to Dark mode).

---

## Brownfield Sweep Recipe

Sweep an existing page to bind variables to nodes whose visual properties match
variable values.

> **No crash constraint in Figma** — unlike Penpot's WASM renderer, Figma can process
> multiple pages in a single `figma_execute` call without crashing. You can sweep
> the entire file if needed.

```javascript
// --- Paste initVarResolver(), extractBindableProps(), rgbToHex() above this line ---

const REVERSE_MAP = {
  '#3B82F6': { coll: 'semantic', path: 'bg/interactive', field: 'fills' },
  '#EF4444': { coll: 'semantic', path: 'bg/danger', field: 'fills' },
  '#171717': { coll: 'semantic', path: 'text/primary', field: 'fills' },
  '#E5E5E5': { coll: 'semantic', path: 'border/default', field: 'strokes' },
};

const nodes = [];
function collect(node) {
  nodes.push(node);
  if ('children' in node) node.children.forEach(collect);
}
figma.currentPage.children.forEach(collect);

let bound = 0, skipped = 0;
for (const node of nodes) {
  const props = extractBindableProps(node);
  for (const [field, hex] of Object.entries(props)) {
    const match = REVERSE_MAP[hex];
    if (!match || match.field !== field) continue;
    if (await VR.bind(node, field, match.coll, match.path)) bound++;
    else skipped++;
  }
}
return { bound, skipped, totalNodes: nodes.length };
```

---

## Property Extraction Helper

```javascript
function extractBindableProps(node) {
  const props = {};
  if (node.fills && Array.isArray(node.fills) && node.fills.length > 0) {
    const f = node.fills[0];
    if (f.type === 'SOLID' && f.color) {
      props.fills = rgbToHex(f.color.r, f.color.g, f.color.b);
    }
  }
  if (node.strokes && Array.isArray(node.strokes) && node.strokes.length > 0) {
    const s = node.strokes[0];
    if (s.type === 'SOLID' && s.color) {
      props.strokes = rgbToHex(s.color.r, s.color.g, s.color.b);
    }
  }
  if (node.cornerRadius !== undefined && node.cornerRadius !== figma.mixed) {
    props.topLeftRadius = String(node.cornerRadius);
  }
  if (node.type === 'TEXT') {
    if (node.fontSize && node.fontSize !== figma.mixed) {
      props.fontSize = String(node.fontSize);
    }
  }
  return props;
}
```

---

## Figma-Specific Notes

| Topic | Detail |
|-|-|
| `setBoundVariable` is idempotent | Safe to call repeatedly. No toggle/unbind risk. |
| `boundVariables` is read-only | Inspect existing bindings. Returns `VariableAlias` objects. |
| Uniform corner radius | Must bind all four corner fields individually. |
| Color format in Figma API | RGB 0-1 range (`{ r: 0.23, g: 0.51, b: 0.96 }`), not hex. Convert before comparing. |
| No WASM crash on multi-page sweep | Figma handles multi-page operations in a single call. |
| Variable scopes | Variables can be scoped (e.g., `ALL_FILLS`, `STROKE_COLOR`). Check `variable.scopes`. |
| Text fill binding | Bind `'fills'` on the text node itself, same as any other node. |

# DTCG Token Type to Figma Variable Mapping

Maps [Design Tokens Community Group](https://tr.designtokens.org/format/) (DTCG) token
types to their Figma variable equivalents. Use this reference when importing a DTCG
`tokens.json` into Figma via `figma_setup_design_tokens` or `figma_batch_create_variables`.

---

## Type Mapping

Figma supports four variable types: `COLOR`, `FLOAT`, `STRING`, `BOOLEAN`.
Multi-value DTCG types (shadow, typography, border) cannot be represented as a single
Figma variable — split them into individual properties.

| DTCG Type | Figma Type | Notes |
|-|-|-|
| `color` | `COLOR` | Hex to RGBA conversion handled by MCP tools |
| `dimension` | `FLOAT` | Strip unit, store raw number (px assumed) |
| `fontFamily` | `STRING` | |
| `fontWeight` | `FLOAT` | Numeric weight (400, 700, etc.) |
| `duration` | `FLOAT` | Milliseconds as number |
| `cubicBezier` | `STRING` | Serialize as `"0.4, 0, 0.2, 1"` |
| `number` | `FLOAT` | |
| `strokeStyle` | `STRING` | `"solid"`, `"dashed"`, etc. |
| `border` | *split* | `border/width` -> FLOAT, `border/color` -> COLOR, `border/style` -> STRING |
| `transition` | *split* | `transition/duration` -> FLOAT, `transition/easing` -> STRING |
| `shadow` | *split* | `shadow/color` -> COLOR, `shadow/offsetX` -> FLOAT, `shadow/blur` -> FLOAT, etc. |
| `gradient` | *not supported* | Apply via `figma_execute` fills array instead |
| `typography` | *split* | `typography/fontFamily` -> STRING, `typography/fontSize` -> FLOAT, etc. |
| `fontStyle` | `STRING` | `"normal"`, `"italic"` |
| `textDecoration` | `STRING` | `"none"`, `"underline"`, `"line-through"` |
| `textCase` | `STRING` | `"none"`, `"uppercase"`, `"lowercase"`, `"capitalize"` |
| `letterSpacing` | `FLOAT` | Percentage or pixel value |

> **Composite types** (`border`, `shadow`, `typography`, `transition`) must be
> decomposed into individual variables. Use `/` in the variable name to group
> them: `shadow/md/blur`, `shadow/md/color`, `shadow/md/offsetY`.

---

## Token Sets to Collections

| DTCG Concept | Figma Equivalent |
|-|-|
| Token set / file | Variable Collection |
| Token group | Variable name path (using `/` separators) |
| Token value | Variable value for a mode |

### Recommended Collection Structure

| Collection | Contents | Example Variables |
|-|-|-|
| `primitives` | Raw scale values | `color/blue/500`, `spacing/4`, `radius/md` |
| `semantic` | Contextual aliases | `bg/surface`, `text/primary`, `border/default` |
| `component` | Component-specific | `button/padding-x`, `card/radius` |

Create with `figma_setup_design_tokens`:

```javascript
figma_setup_design_tokens({
  collectionName: 'primitives',
  modes: ['Value'],
  tokens: [
    { name: 'color/blue/500', resolvedType: 'COLOR', values: { 'Value': '#3B82F6' } },
    { name: 'spacing/4',      resolvedType: 'FLOAT', values: { 'Value': 16 } },
    { name: 'radius/md',      resolvedType: 'FLOAT', values: { 'Value': 8 } },
  ]
})
```

---

## Token Tiers to Variable Name Paths

DTCG tier structure maps to Figma's `/`-separated variable names, which Figma
renders as collapsible groups in the Variables panel.

| Tier | DTCG Path | Figma Variable Name |
|-|-|-|
| Primitive | `color.blue.500` | `color/blue/500` |
| Semantic | `bg.interactive` | `bg/interactive` |
| Component | `button.background` | `button/background` |

> Use `/` (not `.`) as the separator in Figma variable names. Figma creates
> visual grouping in the Variables panel based on `/` delimiters.

---

## Mode Mapping (Light/Dark Themes)

DTCG tokens handle themes via separate token sets or `$extensions` with mode overrides.
In Figma, themes map to **modes** within a collection.

| DTCG Approach | Figma Equivalent |
|-|-|
| Separate files (`light.json`, `dark.json`) | Single collection with Light and Dark modes |
| `$extensions.mode` overrides | Values per mode in the same variable |
| Contextual alias per theme | Variable alias that changes per mode |

### Create Themed Collection

```javascript
figma_setup_design_tokens({
  collectionName: 'semantic',
  modes: ['Light', 'Dark'],
  tokens: [
    { name: 'bg/surface',    resolvedType: 'COLOR', values: { 'Light': '#FFFFFF', 'Dark': '#1A1A2E' } },
    { name: 'bg/interactive', resolvedType: 'COLOR', values: { 'Light': '#3B82F6', 'Dark': '#60A5FA' } },
    { name: 'text/primary',  resolvedType: 'COLOR', values: { 'Light': '#171717', 'Dark': '#F9FAFB' } },
    { name: 'text/secondary', resolvedType: 'COLOR', values: { 'Light': '#525252', 'Dark': '#A1A1AA' } },
  ]
})
```

### Additional Modes

Add modes to existing collections with `figma_add_mode`:

```javascript
figma_add_mode({
  collectionId: 'VariableCollectionId:123:456',
  modeName: 'High Contrast'
})
```

Figma plan limits: Free = 1 mode, Pro = 4 modes, Enterprise = 40 modes per collection.

---

## Reference / Alias Handling

DTCG uses `{reference}` syntax for aliases:

```json
{ "bg.interactive": { "$value": "{color.blue.500}", "$type": "color" } }
```

Figma supports variable aliases natively. Create via `figma_execute`:

```javascript
// Find the target variable to alias
const target = await VR.resolve('primitives', 'color/blue/500');
const aliasVar = await VR.resolve('semantic', 'bg/interactive');

if (target && aliasVar) {
  // Set the alias: semantic bg/interactive -> primitives color/blue/500
  const coll = (await figma.variables.getLocalVariableCollectionsAsync())
    .find(c => c.name === 'semantic');
  const modeId = coll.modes[0].modeId;

  aliasVar.setValueForMode(modeId, {
    type: 'VARIABLE_ALIAS',
    id: target.id
  });
}
```

> When a variable aliases another, Figma displays the reference chain in the
> Variables panel and resolves the final value at runtime based on the active mode.

# W3C DTCG Token Format Reference

The W3C Design Token Community Group (DTCG) defines a standard JSON format for exchanging design tokens between tools. This specification ensures interoperability across design tools, code generators, and token management platforms.

## File Structure

Token files use the `.tokens` or `.tokens.json` extension with media type `application/design-tokens+json`.

```json
{
  "color": {
    "$type": "color",
    "primary": {
      "$value": "#2563eb",
      "$description": "Brand primary color"
    }
  }
}
```

## Token Properties

| Property | Required | Type | Purpose |
|-|-|-|-|
| `$value` | Yes | any | The token's resolved value |
| `$type` | No* | string | *Required if not inherited from a parent group |
| `$description` | No | string | Human-readable explanation of the token's purpose |
| `$deprecated` | No | boolean or string | Marks the token as deprecated; string value can explain why |
| `$extensions` | No | object | Vendor-specific metadata using reverse domain notation keys |

## Token Types

The DTCG spec defines both simple (single-value) and composite (multi-value) token types. Every token must resolve to exactly one type.

### Simple Types

| Type | Value Format | Example |
|-|-|-|
| `color` | Hex string or object `{ colorSpace, components, alpha }` | `"#2563eb"` |
| `dimension` | Object `{ value, unit }` where unit is `px` or `rem` | `{ "value": 16, "unit": "px" }` |
| `fontFamily` | String or array of strings | `["Inter", "sans-serif"]` |
| `fontWeight` | Number 1–1000 or named string | `600` or `"semibold"` |
| `fontStyle` | String | `"normal"` or `"italic"` |
| `duration` | Object `{ value, unit }` where unit is `ms` or `s` | `{ "value": 200, "unit": "ms" }` |
| `cubicBezier` | Array of 4 numbers `[x1, y1, x2, y2]` | `[0.4, 0, 0.2, 1]` |
| `number` | JSON number | `1.5` |
| `string` | JSON string | `"block"` |

**Unit guidance for `dimension` type:**
- Font sizes: always use `rem` — enables user text scaling (WCAG 1.4.4). Example: `{ "value": 1, "unit": "rem" }` not `{ "value": 16, "unit": "px" }`.
- Spacing and sizing: prefer `rem` for consistency with font scaling. `px` is acceptable for borders, shadows, and values that should not scale with font size.
- Border widths and shadow offsets: use `px` — these are visual details that should remain constant regardless of text size.

### Composite Types

Composite types combine multiple sub-values into a single token. Each sub-value corresponds to a simple type.

| Type | Sub-values |
|-|-|
| `typography` | `fontFamily`, `fontSize`, `fontWeight`, `letterSpacing`, `lineHeight` |
| `shadow` | `color`, `offsetX`, `offsetY`, `blur`, `spread` |
| `border` | `color`, `width`, `style` |
| `transition` | `duration`, `delay`, `timingFunction` |
| `gradient` | Array of `{ color, position }` stops |
| `strokeStyle` | String or object with `dashArray` and `lineCap` |

Example composite token:

```json
{
  "heading": {
    "$type": "typography",
    "$value": {
      "fontFamily": ["Inter", "sans-serif"],
      "fontSize": { "value": 24, "unit": "px" },
      "fontWeight": 700,
      "letterSpacing": { "value": -0.02, "unit": "em" },
      "lineHeight": 1.2
    }
  }
}
```

## Aliases (References)

Aliases let one token reference another's value, creating a single source of truth. They use curly brace syntax with the dot-separated path to the target token:

```json
{
  "color": {
    "$type": "color",
    "brand": { "$value": "#2563eb" },
    "primary": { "$value": "{color.brand}" },
    "action": { "$value": "{color.primary}" }
  }
}
```

**Alias rules:**

- Paths are dot-separated matching the JSON nesting: `{group.subgroup.token}`
- The referenced target must have a `$value` property
- Chained aliases are allowed (A references B which references C)
- Circular references are forbidden and must produce an error
- When a referenced token changes, all aliases pointing to it reflect the new value

## Groups

Groups are JSON objects that do **not** contain a `$value` property. They organize tokens into a hierarchy.

```json
{
  "spacing": {
    "$type": "dimension",
    "$description": "Spacing scale for layout",
    "small": { "$value": { "value": 8, "unit": "px" } },
    "medium": { "$value": { "value": 16, "unit": "px" } },
    "large": { "$value": { "value": 32, "unit": "px" } }
  }
}
```

**Group properties:**

- `$type` — inherited by all child tokens that don't declare their own `$type`
- `$description` — documents the group's purpose
- `$extensions` — vendor metadata for the group
- `$deprecated` — marks all tokens in the group as deprecated

**Type inheritance resolution order:**

1. Token's own `$type` (highest priority)
2. Nearest parent group's `$type`
3. Referenced token's `$type` (for aliases)
4. If none resolves, tools **must not** guess the type — this is an error

## Validation Rules

**Name restrictions:**
- Token and group names must not start with `$` (reserved for spec properties)
- Names must not contain `{`, `}`, or `.` (reserved for alias syntax and path separators)
- Names are case-sensitive (`Primary` and `primary` are distinct tokens)

**Structural rules:**
- Every token must have a resolvable `$type`, either declared directly or inherited from a parent group
- Circular alias references must produce a validation error
- An object cannot be both a token and a group — if it has `$value`, it is a token; otherwise it is a group
- All alias references must resolve to an existing token with a `$value`

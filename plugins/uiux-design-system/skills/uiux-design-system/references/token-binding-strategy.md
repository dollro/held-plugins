# Token Binding Strategy

Tool-agnostic strategy for binding design tokens (variables) to shapes/nodes in any
design tool. This document defines the patterns and algorithms. Tool-specific API calls
(Penpot `applyToken`, Figma `setBoundVariable`, etc.) belong in the respective tool
plugins — not here.

## Two Binding Strategies

### Greenfield (Inline)

Bind tokens at shape creation time. The code that creates a shape knows its semantic
intent — a primary button fill is `bg.interactive`, not "some blue hex". Bind
immediately; don't defer.

```
create shape  ->  set visual value from tokenMap  ->  bind token  ->  done
```

Deferring binding to a later pass loses the semantic context that was available at
creation time and introduces drift between visual values and token assignments.

### Brownfield (Sweep)

For existing files where tokens are defined but not bound to shapes. Walk every shape,
match its property values to tokens via a reverse map, score each candidate, and apply
bindings with confidence thresholds.

Use this when inheriting a file from a workflow that predates token binding, or when
auditing an existing design system for binding coverage.

## Token Map Pattern

After creating tokens, build a `tokenMap` — a plain object mapping every semantic token
name to its resolved value. All generation code uses this map for both visual rendering
AND token binding.

```javascript
const tokenMap = {
  // Colors
  'bg.surface': '#FFFFFF',
  'bg.interactive': '#3B82F6',
  'bg.interactive.hover': '#2563EB',
  'text.primary': '#171717',
  'text.secondary': '#525252',
  'text.on-interactive': '#FFFFFF',
  'border.default': '#E5E5E5',
  'border.focus': '#3B82F6',
  // Spacing (string values — some tools require strings)
  'spacing.sm': '8',
  'spacing.md': '16',
  'spacing.lg': '24',
  // Radius
  'radius.sm': '4',
  'radius.md': '8',
  'radius.lg': '12',
  // ... all semantic tokens
};
```

The visual property (`fillColor`, `borderRadius`) is set from `tokenMap` so the shape
renders correctly. The token binding call links the token so future changes propagate.
Both steps are required — skipping either leaves the shape incomplete.

## Reverse Map Builder (Brownfield)

For brownfield binding, build a reverse map: `{ resolvedValue: [candidateTokens] }`.
This requires resolving reference chains since token values may be references to other
tokens (e.g., `{color.blue.500}` resolves to `#2563EB`).

### Reference Resolver

Follows `{reference}` chains with a cycle guard to produce the final resolved value.

```javascript
function resolveTokenValue(token, allTokenSets) {
  let value = token.value;
  const seen = new Set();
  while (value && value.startsWith('{') && value.endsWith('}')) {
    const refName = value.slice(1, -1);
    if (seen.has(refName)) break;
    seen.add(refName);
    let found = null;
    for (const set of allTokenSets) {
      found = set.tokens.find(t => t.name === refName);
      if (found) break;
    }
    if (!found) break;
    value = found.value;
  }
  return value;
}
```

### Building the Map

```javascript
function buildReverseMap(allTokenSets) {
  const map = {}; // { resolvedValue: [{ set, name, type, tier }] }
  for (const set of allTokenSets) {
    const tier = set.name; // 'primitives' | 'semantic' | 'component'
    for (const token of set.tokens) {
      const resolved = resolveTokenValue(token, allTokenSets);
      if (!map[resolved]) map[resolved] = [];
      map[resolved].push({ set: set.name, name: token.name, type: token.type, tier });
    }
  }
  return map;
}
```

Prefer semantic-tier candidates over primitive-tier when multiple tokens resolve to the
same value. Primitive-only matches indicate a missing semantic token.

## Confidence Scoring Rules

When multiple tokens resolve to the same value, use context signals to pick the best
candidate.

| Signal | Confidence | Logic |
|-|-|-|
| Shape name contains token name | High | Foundations swatches — direct 1:1 match |
| Single semantic candidate for value | High | Only one semantic token resolves to this value |
| Parent board narrows semantic domain | High | Board `btn-primary-*` + fill -> prefer `bg.*` tokens |
| Property type narrows candidates | Medium | strokeColor -> prefer `border.*`; text fill -> prefer `text.*` |
| Shape type narrows candidates | Medium | Text shape -> prefer `text.*` for fill |
| Multiple semantic candidates, no signal | Low | Ambiguous — surface to user |
| Only primitive candidates exist | Low | Semantic token may be missing — flag |

**Thresholds:**
- **High** — auto-apply. No user input needed.
- **Medium** — auto-apply with a note in the binding report.
- **Low** — collect for user confirmation. Do not auto-apply.

## Sweep Algorithm

Pseudocode for the brownfield binding pass. Process one page at a time to avoid
bulk-mutation performance issues in design tool runtimes.

```
for each page:
  build reverse map (once per sweep, reuse across pages)
  for each shape (recursive into nested boards):
    for each bindable property (fill, stroke, radius, shadow, font*):
      currentValue = extract property value from shape
      candidates = reverseMap[currentValue]
      if no candidates: skip

      score each candidate using confidence rules:
        - check shape name vs token name
        - check parent board name for semantic domain
        - check property type (fill/stroke/radius/shadow/font)
        - check shape type (text/rect/frame)
        - prefer semantic tier over primitive tier

      bestCandidate = highest-scoring candidate
      if high or medium confidence:
        queue { shape, token: bestCandidate, property, confidence }
      if low confidence:
        add to pending report

  apply all high/medium bindings via tool-specific API
  return { applied: [...], pending: [...] }
```

## Toggle/Idempotency Guard

Design tools differ in their token application semantics:

- **Toggle semantics** (e.g., Penpot): calling apply on an already-bound shape unbinds
  the token. Applying twice leaves the shape unbound.
- **Idempotent semantics** (e.g., Figma): calling apply on an already-bound shape is a
  no-op. Safe to call multiple times.

Tool plugins MUST implement a **read-before-write guard** appropriate to their tool:

1. Read the shape's current token bindings for the target property.
2. If the desired token is already bound, skip.
3. If a different token is bound, decide whether to replace (usually yes).
4. If no token is bound, apply.

This strategy document specifies the requirement. Each tool plugin implements the
mechanism using its own API for reading existing bindings.

## Coverage Reporting

After binding, generate a per-page coverage report:

```
Page            | Shapes | Bound | Coverage
-|-|-|-
foundations     |     64 |    62 |   96.9%
atoms           |     38 |    35 |   92.1%
molecules       |     27 |    22 |   81.5%
screens-home    |     89 |    68 |   76.4%
```

**Targets:**
- Foundations and atoms pages: >90% of shapes with at least one token binding.
- Screen pages: >70% of shapes with at least one token binding.

Shapes with zero bindings on a foundations page likely indicate missing tokens or
a scoring gap. Shapes with zero bindings on screen pages may be decorative (spacers,
masks) — these are acceptable exclusions.

The report should also list:
- Count of high-confidence bindings applied automatically.
- Count of medium-confidence bindings applied with notes.
- Count of low-confidence items pending user confirmation.
- Any shapes flagged as having only primitive-tier candidates (missing semantic tokens).

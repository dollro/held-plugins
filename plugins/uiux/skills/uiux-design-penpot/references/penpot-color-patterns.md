# Penpot Color Patterns

Penpot-specific color API patterns. For pure-math color converters (OKLCH→hex,
HSL→hex, RGB→hex, contrast checks), see `uiux-design-system/references/color-utilities.md`.

> **Penpot only accepts hex colors** (`#RRGGBB`). CSS functions like `oklch()`,
> `hsl()`, `rgb()` are **not supported**. Convert first using color-utilities.

## Setting fills with hex colors

```javascript
const rect = penpot.createRectangle();
rect.fills = [{ fillColor: '#3B82F6', fillOpacity: 1 }];
```

## Setting gradient fills

```javascript
shape.fills = [{
  fillColorGradient: {
    type: 'linear',
    startX: 0, startY: 0.5,
    endX: 1, endY: 0.5,
    width: 1,
    stops: [
      { color: '#3B82F6', offset: 0 },
      { color: '#8B5CF6', offset: 1 }
    ]
  }
}];
```

## Creating library colors

```javascript
const libColor = penpot.library.local.createColor();
libColor.name = 'Primary';
libColor.path = 'Brand';
libColor.color = '#3B82F6';
libColor.opacity = 1;

// Use in shapes
const fill = libColor.asFill();
const stroke = libColor.asStroke();
shape.fills = [fill];
```

## Discovering and replacing colors

```javascript
// Find all colors in selected shapes
const colors = penpot.shapesColors(penpot.selection);

// Replace a color across shapes
penpot.replaceColor(
  penpot.selection,
  { color: '#FF0000' },  // old
  { color: '#3B82F6' }   // new
);
```

## Converting OKLCH design tokens to Penpot

```javascript
// When applying design tokens that use OKLCH
// (oklchStringToHex is from uiux-design-system/references/color-utilities.md)
const tokens = {
  'primary': 'oklch(0.546 0.245 262.881)',
  'secondary': 'oklch(0.577 0.174 142.496)',
  'surface': 'oklch(0.985 0.002 247.839)',
};

const penpotColors = {};
for (const [name, oklch] of Object.entries(tokens)) {
  penpotColors[name] = oklchStringToHex(oklch);
}
// Now use penpotColors.primary etc. as hex values in fills
```

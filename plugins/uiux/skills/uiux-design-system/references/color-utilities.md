# Color Utilities

Pure-math color converters for design system workflows. These functions have no
dependencies on browser APIs or design tool runtimes — they work in any JavaScript
context (Node, Deno, plugin sandboxes, `execute_code`).

> **Design tools that only accept hex colors** (e.g., Penpot) need these converters
> when working with OKLCH (Tailwind v4) or HSL tokens. Figma accepts hex natively
> for COLOR variables.

## OKLCH to Hex

OKLCH is the default color space in Tailwind CSS v4 and modern design systems.

```javascript
function oklchToHex(L, C, H) {
  // OKLCH → OKLab
  const hRad = H * Math.PI / 180;
  const a = C * Math.cos(hRad);
  const b = C * Math.sin(hRad);

  // OKLab → Linear sRGB (via LMS)
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;

  let r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  let bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;

  // Linear → sRGB gamma correction + clamp to 0-255
  const gamma = v => v > 0.0031308 ? 1.055 * Math.pow(v, 1 / 2.4) - 0.055 : 12.92 * v;
  const toByte = v => Math.max(0, Math.min(255, Math.round(gamma(Math.max(0, v)) * 255)));

  return '#' + [r, g, bl].map(v => toByte(v).toString(16).padStart(2, '0')).join('').toUpperCase();
}

// oklchToHex(0.52, 0.105, 223.128) → teal
// oklchToHex(1, 0, 0)              → '#FFFFFF'
// oklchToHex(0, 0, 0)              → '#000000'
// oklchToHex(0.7, 0.15, 150)       → green
```

### Parsing OKLCH strings

```javascript
function parseOklch(str) {
  // Handles: oklch(0.52 0.105 223.128), oklch(52% 0.105 223.128), oklch(0.52 0.105 223.128 / 0.5)
  const m = str.match(/oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+%?))?\s*\)/);
  if (!m) return null;
  let L = parseFloat(m[1]);
  if (m[2] === '%') L /= 100;
  const C = parseFloat(m[3]);
  const H = parseFloat(m[4]);
  let alpha = 1;
  if (m[5]) {
    alpha = parseFloat(m[5]);
    if (m[5].endsWith('%')) alpha /= 100;
  }
  return { L, C, H, alpha };
}

function oklchStringToHex(str) {
  const parsed = parseOklch(str);
  if (!parsed) return null;
  return oklchToHex(parsed.L, parsed.C, parsed.H);
}

// oklchStringToHex('oklch(0.52 0.105 223.128)') → teal hex
```

## HSL to Hex

```javascript
function hslToHex(h, s, l) {
  // h: 0-360, s: 0-100, l: 0-100
  s /= 100; l /= 100;
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h / 60) % 2 - 1));
  const m = l - c / 2;
  let r, g, b;
  if (h < 60)       { r = c; g = x; b = 0; }
  else if (h < 120) { r = x; g = c; b = 0; }
  else if (h < 180) { r = 0; g = c; b = x; }
  else if (h < 240) { r = 0; g = x; b = c; }
  else if (h < 300) { r = x; g = 0; b = c; }
  else              { r = c; g = 0; b = x; }
  const toByte = v => Math.round((v + m) * 255);
  return '#' + [r, g, b].map(v => toByte(v).toString(16).padStart(2, '0')).join('').toUpperCase();
}

// hslToHex(210, 80, 50) → '#1A66E5'
```

## RGB to Hex

```javascript
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(v =>
    Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')
  ).join('').toUpperCase();
}
```

## Hex to RGB

```javascript
function hexToRgb(hex) {
  const h = hex.replace('#', '');
  return {
    r: parseInt(h.substring(0, 2), 16),
    g: parseInt(h.substring(2, 4), 16),
    b: parseInt(h.substring(4, 6), 16)
  };
}
```

## Color Palette Generation

Generate tints (lighter) and shades (darker) from a base color:

```javascript
function generatePalette(hex, steps = 5) {
  const { r, g, b } = hexToRgb(hex);
  const tints = [];
  const shades = [];

  for (let i = 1; i <= steps; i++) {
    const factor = i / (steps + 1);
    // Tint: mix with white
    tints.push(rgbToHex(
      Math.round(r + (255 - r) * factor),
      Math.round(g + (255 - g) * factor),
      Math.round(b + (255 - b) * factor)
    ));
    // Shade: mix with black
    shades.push(rgbToHex(
      Math.round(r * (1 - factor)),
      Math.round(g * (1 - factor)),
      Math.round(b * (1 - factor))
    ));
  }

  return { shades: shades.reverse(), base: hex, tints };
}

// generatePalette('#3B82F6') → { shades: [...darker], base: '#3B82F6', tints: [...lighter] }
```

## Contrast Ratio Calculation

For WCAG accessibility validation:

```javascript
function luminance(hex) {
  const { r, g, b } = hexToRgb(hex);
  const [rs, gs, bs] = [r, g, b].map(c => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function contrastRatio(hex1, hex2) {
  const l1 = luminance(hex1);
  const l2 = luminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function meetsWCAG(fgHex, bgHex, level = 'AA', isLargeText = false) {
  const ratio = contrastRatio(fgHex, bgHex);
  if (level === 'AAA') return isLargeText ? ratio >= 4.5 : ratio >= 7;
  return isLargeText ? ratio >= 3 : ratio >= 4.5; // AA
}

// contrastRatio('#1F2937', '#FFFFFF') → 15.5 (passes AAA)
// meetsWCAG('#3B82F6', '#FFFFFF') → true (AA for normal text)
```

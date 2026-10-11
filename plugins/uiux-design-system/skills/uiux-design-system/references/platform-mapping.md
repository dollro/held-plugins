# Platform Mapping Reference

How to transform design tokens from the abstract DTCG format into platform-specific code. The token layer is the single source of truth — platform outputs are generated transforms.

## Design-to-Code Pipeline

```
Figma Variables / Penpot Tokens
        ↓ (export JSON)
  tokens.json (W3C DTCG format)
        ↓ (Style Dictionary / Token Transformer)
  design-tokens.css  (CSS Custom Properties)
  main.css           (Tailwind v4 @theme)
  tokens.ts          (TypeScript constants, optional)
```

### Three Layers in CSS

```css
/* Tier 1: Primitives */
:root {
  --color-purple-500: #6C5CE7;
  --color-purple-600: #5A4BD6;
  --color-gray-700: #374151;
  --spacing-400: 1rem;
  --radius-md: 0.5rem;
}

/* Tier 2: Semantic — this is the layer you swap for theming */
:root {
  --color-primary-default: var(--color-purple-500);
  --color-primary-hover: var(--color-purple-600);
  --color-neutral-text: var(--color-gray-700);
}

/* Tier 3: Mapped — references semantics, auto-resolves on theme change */
:root {
  --surface-action: var(--color-primary-default);
  --surface-action-hover: var(--color-primary-hover);
  --text-body: var(--color-neutral-text);
  --text-on-action: #FFFFFF;
  --border-focus: var(--color-primary-default);
}

/* Dark mode — remap Tier 2, Tier 3 auto-resolves */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary-default: var(--color-purple-400);
    --color-neutral-text: var(--color-gray-200);
  }
}
```

### Mapped Tier into Tailwind v4

```css
@import "tailwindcss";
@import "./design-tokens.css";

@theme {
  --color-primary: var(--surface-action);
  --color-primary-hover: var(--surface-action-hover);
  --color-text-body: var(--text-body);
  --color-text-on-action: var(--text-on-action);
  --radius-md: var(--radius-md);
}
```

Then in templates: `<button class="bg-primary hover:bg-primary-hover text-text-on-action rounded-md px-4">`. The sections below cover each platform in detail.

## CSS Custom Properties

### Naming Transform

| DTCG path | CSS custom property |
|-|-|
| `color.blue.500` | `--color-blue-500` |
| `color.background.surface` | `--color-background-surface` |
| `space.4` | `--space-4` |
| `font.size.300` | `--font-size-300` |

Dots become hyphens. The full token path maps 1:1 to the variable name.

### Organization

Use `:root` for light/default values. Override with `[data-theme="dark"]` for alternate themes.

```css
/* Primitives — raw palette */
:root {
  --color-blue-500: #2563eb;
  --color-blue-700: #1d4ed8;
  --color-neutral-50: #fafafa;
  --color-neutral-900: #171717;
  --space-4: 1rem;
  --space-8: 2rem;
}

/* Semantics — reference primitives */
:root {
  --color-interactive-default: var(--color-blue-500);
  --color-interactive-hover: var(--color-blue-700);
  --color-background-surface: var(--color-neutral-50);
  --color-text-primary: var(--color-neutral-900);
}

[data-theme="dark"] {
  --color-neutral-50: #171717;
  --color-neutral-900: #fafafa;
}
```

Key principle: semantic CSS vars always reference primitive CSS vars, never raw hex values.

### Dark Mode

Override **semantic** custom properties within a dark scope. Primitive vars stay unchanged — they're just the raw palette. Semantic vars remap which primitives they reference, and mapped vars auto-resolve through the alias chain.

```css
/* Primitives — always available, never change per theme */
:root {
  --color-purple-400: #a78bfa;
  --color-purple-500: #6c5ce7;
  --color-purple-600: #5a4bd6;
  --color-gray-200: #e5e5e5;
  --color-gray-700: #404040;
  --color-gray-900: #171717;
}

/* Semantics — light mode (default) */
:root {
  --color-primary-default: var(--color-purple-500);
  --color-primary-hover: var(--color-purple-600);
  --color-neutral-text: var(--color-gray-700);
  --color-neutral-bg: #ffffff;
}

/* Semantics — dark mode: remap which primitives are referenced */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary-default: var(--color-purple-400);
    --color-primary-hover: var(--color-purple-500);
    --color-neutral-text: var(--color-gray-200);
    --color-neutral-bg: var(--color-gray-900);
  }
}

/* Or class-based for manual toggle: */
.dark {
  --color-primary-default: var(--color-purple-400);
  --color-primary-hover: var(--color-purple-500);
  --color-neutral-text: var(--color-gray-200);
  --color-neutral-bg: var(--color-gray-900);
}
```

Key principle: **semantic CSS vars remap which primitives they reference** in dark mode. Mapped/component tokens (`--surface-action`, `--text-body`, etc.) don't change — they reference semantics which auto-resolve to the correct primitive for each theme. This is more flexible than overriding primitives directly, especially for multi-brand scenarios where different brands may need different dark mode adjustments.

### High Contrast

For `forced-colors` / Windows High Contrast mode:

```css
@media (forced-colors: active) {
  :root {
    --color-background-surface: Canvas;
    --color-text-primary: CanvasText;
    --color-border-default: CanvasText;
    --color-interactive-default: LinkText;
  }
}
```

### Reduced Motion

Gate all duration tokens when user prefers reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-duration-fast: 0ms;
    --motion-duration-normal: 0ms;
    --motion-duration-slow: 0ms;
  }
}
```

## Tailwind CSS v4

Tailwind v4 uses CSS-first configuration. Import the generated token CSS file, then map tokens in `@theme`:

```css
@import "./design-tokens.css";
@import "tailwindcss";

@theme {
  --color-surface: var(--color-background-surface);
  --color-primary: var(--color-interactive-default);
  --color-danger: var(--color-feedback-danger);
  --spacing-inline-md: var(--space-inline-md);
  --spacing-stack-lg: var(--space-stack-lg);
  --radius-interactive: var(--radius-interactive);
}
```

Key principle: the token CSS file provides custom properties; `@theme` maps them to Tailwind's namespace so utility classes like `bg-surface`, `text-primary`, and `rounded-interactive` work.

For Tailwind v3: use `tailwind.config.js` with `var(--token-name)` references in `theme.extend`.

> For full Tailwind v4 configuration, dark mode ThemeProvider, OKLCH color patterns, and shadcn/ui integration, see the `uiux-design-tailwindv4` skill.

## SCSS

Map tokens to `$variables` and use maps for scales:

```scss
$color-interactive-default: var(--color-interactive-default);
$space-md: var(--space-4);

$font-sizes: (
  sm: var(--font-size-200),
  base: var(--font-size-300),
  lg: var(--font-size-500),
);

@mixin typography($token) {
  font-family: map-get($token, fontFamily);
  font-size: map-get($token, fontSize);
  font-weight: map-get($token, fontWeight);
  line-height: map-get($token, lineHeight);
}
```

## Other Platforms

| Platform | Output Format | Pattern |
|-|-|-|
| React Native | JS/TS module | Named exports: `export const colorActionPrimary = '#2563eb'` |
| iOS (Swift) | Enum/struct | `enum DesignTokens { static let actionPrimary = UIColor(hex: "#2563eb") }` |
| Android | XML resources / Compose theme | `<color name="action_primary">#2563eb</color>` or `MaterialTheme` values |

Native platforms receive resolved values (not `var()` references) since CSS custom properties are unavailable.

## Style Dictionary

[Style Dictionary](https://amzn.github.io/style-dictionary/) is the standard pipeline tool for multi-platform token generation. It reads DTCG-compatible JSON and outputs platform-specific code.

```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "dist/css/",
      "files": [{ "destination": "tokens.css", "format": "css/variables" }]
    },
    "js": {
      "transformGroup": "js",
      "buildPath": "dist/js/",
      "files": [{ "destination": "tokens.js", "format": "javascript/es6" }]
    }
  }
}
```

Add additional platform entries (android, ios, scss) to generate all outputs from one token source.

For Tokens Studio projects, add `@tokens-studio/sd-transforms` to handle Tokens Studio–specific formats (math expressions, color modifiers, multi-value composites) before Style Dictionary processes them:

```bash
npm install @tokens-studio/sd-transforms
```

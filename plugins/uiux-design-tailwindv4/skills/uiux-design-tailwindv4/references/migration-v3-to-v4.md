# Migration Guide: Tailwind CSS v3 to v4

## Migration Checklist

- [ ] Replace `tailwind.config.ts` with CSS `@theme` block
- [ ] Change `@tailwind base/components/utilities` to `@import "tailwindcss"`
- [ ] Move color definitions to `@theme { --color-*: value }`
- [ ] Replace `darkMode: "class"` with `@custom-variant dark (&:where(.dark, .dark *))`
- [ ] Move `@keyframes` inside `@theme` blocks
- [ ] Replace `require("tailwindcss-animate")` with native CSS animations
- [ ] Update `h-10 w-10` to `size-10` (new utility)
- [ ] Remove `forwardRef` (React 19 passes ref as prop)
- [ ] Consider OKLCH colors for better color perception
- [ ] Replace custom plugins with `@utility` directives
- [ ] Replace hardcoded colors with semantic tokens
- [ ] Use `@tailwindcss/vite` plugin instead of PostCSS (for Vite projects)
- [ ] Set `components.json` `"config": ""` (if using shadcn)
- [ ] Delete `tailwind.config.ts` and `postcss.config.js` (if using Vite plugin)

## Key Pattern Changes

### Configuration

**v3:**
```typescript
// tailwind.config.ts
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'hsl(var(--primary))',
        secondary: 'hsl(var(--secondary))',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

**v4:**
```css
/* app.css */
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-primary: oklch(14.5% 0.025 264);
  --color-primary-foreground: oklch(98% 0.01 264);
  --color-secondary: oklch(96% 0.01 264);
  --color-secondary-foreground: oklch(14.5% 0.025 264);
}
```

### Imports

**v3:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**v4:**
```css
@import "tailwindcss";
```

### Custom Components

**v3:**
```css
@layer components {
  .btn-custom {
    @apply bg-primary text-white px-4 py-2 rounded;
  }
}
```

**v4:**
```css
@utility btn-custom {
  @apply bg-primary text-primary-foreground px-4 py-2 rounded-md;
}
```

### Build Tool

**v3 (PostCSS):**
```javascript
// postcss.config.js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**v4 (Vite plugin):**
```typescript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

## Migrating Hardcoded Colors to Semantic Tokens

### Semantic Color Mapping

| Hardcoded Color | Semantic Token | Use Case |
|-|-|-|
| `bg-red-*` / `text-red-*` | `bg-destructive` / `text-destructive` | Errors, delete actions |
| `bg-green-*` / `text-green-*` | `bg-success` / `text-success` | Success states |
| `bg-yellow-*` / `text-yellow-*` | `bg-warning` / `text-warning` | Warnings |
| `bg-blue-*` / `text-blue-*` | `bg-info` or `bg-primary` | Info, primary actions |
| `bg-gray-*` / `text-gray-*` | `bg-muted` / `text-muted-foreground` | Backgrounds, secondary text |

### Migration Patterns

**Solid Backgrounds:**
```tsx
// BEFORE
<div className="bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300">

// AFTER
<div className="bg-info/10 text-info">
```

**Borders:**
```tsx
// BEFORE
<div className="border-2 border-green-200 dark:border-green-800">

// AFTER
<div className="border-2 border-success/30">
```

**Text Colors:**
```tsx
// BEFORE
<span className="text-red-600 dark:text-red-400">

// AFTER
<span className="text-destructive">
```

**Icons:**
```tsx
// BEFORE
<AlertCircle className="text-yellow-500" />

// AFTER
<AlertCircle className="text-warning" />
```

**Gradients:**
```tsx
// BEFORE
<div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">

// AFTER
<div className="bg-gradient-to-r from-success/10 to-success/20">
```

### Adding Semantic Colors to CSS

If your theme does not already include status colors, add them:

```css
:root {
  --destructive: hsl(0 84.2% 60.2%);
  --destructive-foreground: hsl(210 40% 98%);
  --success: hsl(142.1 76.2% 36.3%);
  --success-foreground: hsl(210 40% 98%);
  --warning: hsl(38 92% 50%);
  --warning-foreground: hsl(222.2 47.4% 11.2%);
  --info: hsl(221.2 83.2% 53.3%);
  --info-foreground: hsl(210 40% 98%);
}

.dark {
  --destructive: hsl(0 62.8% 30.6%);
  --destructive-foreground: hsl(210 40% 98%);
  --success: hsl(142.1 70.6% 45.3%);
  --success-foreground: hsl(222.2 47.4% 11.2%);
  --warning: hsl(38 92% 55%);
  --warning-foreground: hsl(222.2 47.4% 11.2%);
  --info: hsl(217.2 91.2% 59.8%);
  --info-foreground: hsl(222.2 47.4% 11.2%);
}

@theme inline {
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-success: var(--success);
  --color-success-foreground: var(--success-foreground);
  --color-warning: var(--warning);
  --color-warning-foreground: var(--warning-foreground);
  --color-info: var(--info);
  --color-info-foreground: var(--info-foreground);
}
```

### Step-by-Step Color Migration Process

1. **Add semantic colors** to your CSS (see above)
2. **Find hardcoded colors** in your codebase:
   ```bash
   grep -r "bg-\(red\|yellow\|blue\|green\|purple\|orange\|emerald\)-[0-9]" src/
   grep -r "text-\(red\|yellow\|blue\|green\|purple\|orange\|emerald\)-[0-9]" src/
   grep -r "border-\(red\|yellow\|blue\|green\|purple\|orange\|emerald\)-[0-9]" src/
   ```
3. **Replace component by component**, starting with high-impact components:
   - Buttons, Badges, Alert boxes, Status indicators, Cards
4. **Test both themes** after each component migration

### Example: Badge Component Migration

**Before:**
```tsx
const severityConfig = {
  critical: {
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
  },
  warning: {
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/20',
  },
  info: {
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
  },
}
```

**After:**
```tsx
const severityConfig = {
  critical: {
    color: 'text-destructive',
    bg: 'bg-destructive/10',
    border: 'border-destructive/20',
  },
  warning: {
    color: 'text-warning',
    bg: 'bg-warning/10',
    border: 'border-warning/20',
  },
  info: {
    color: 'text-info',
    bg: 'bg-info/10',
    border: 'border-info/20',
  },
}
```

### Verification Commands

```bash
# Should return 0 results when migration is complete
grep -r "text-red-[0-9]" src/components/
grep -r "bg-blue-[0-9]" src/components/
grep -r "border-green-[0-9]" src/components/

# Verify semantic colors are being used
grep -r "bg-destructive" src/components/
grep -r "text-success" src/components/
grep -r "text-warning" src/components/
```

### Performance Impact

**Before** (with `dark:` variants everywhere):
```tsx
<div className="bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800">
```

**After** (semantic tokens, CSS handles switching):
```tsx
<div className="bg-info/10 text-info border-info/30">
```

Result: ~60% fewer CSS classes in markup, smaller HTML payload, faster rendering.

## Common Migration Pitfalls

### Forgetting to Map in @theme inline

Variables defined in `:root` but not mapped in `@theme inline` means the utilities do not exist.

### Wrong Opacity Syntax

```tsx
// WRONG
<div className="bg-success-10" />

// CORRECT
<div className="bg-success/10" />
```

### Mixing Approaches

Do not mix hardcoded and semantic colors in the same component. Choose one approach and be consistent.

### Not Testing Dark Mode

Always test both themes during migration. Semantic tokens automatically switch, but verify contrast and readability.

## Migration Testing Checklist

- [ ] All severity/status levels visually distinct
- [ ] Text has proper contrast in both light and dark modes
- [ ] No hardcoded color classes remain (verify with grep)
- [ ] Hover states work correctly
- [ ] Gradients render smoothly
- [ ] Icons are visible and colored correctly
- [ ] Borders are visible in both themes
- [ ] No visual regressions
- [ ] `tailwind.config.ts` deleted (or empty)
- [ ] Using `@import "tailwindcss"` not `@tailwind` directives
- [ ] All `@layer components` replaced with `@utility`

## Official Documentation

- Tailwind v4 Upgrade Guide: https://tailwindcss.com/docs/upgrade-guide
- Tailwind v4 Docs: https://tailwindcss.com/docs
- shadcn/ui Tailwind v4 Guide: https://ui.shadcn.com/docs/tailwind-v4

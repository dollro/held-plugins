# Common Gotchas and Fixes

Documented pitfalls for Tailwind CSS v4 projects, with and without shadcn/ui.

## Critical Failures (Will Break Your Build)

### 1. `:root` Inside `@layer base`

```css
/* WRONG */
@layer base {
  :root {
    --background: hsl(0 0% 100%);
  }
}

/* CORRECT */
:root {
  --background: hsl(0 0% 100%);
}

@layer base {
  body {
    background-color: var(--background);
  }
}
```

**Why**: Tailwind v4 strips CSS outside `@theme`/`@layer`, but `:root` must be at root level to persist.

### 2. Nested `@theme` Directive

```css
/* WRONG */
@theme {
  --color-primary: hsl(0 0% 0%);
}
.dark {
  @theme {
    --color-primary: hsl(0 0% 100%);
  }
}

/* CORRECT */
:root {
  --primary: hsl(0 0% 0%);
}
.dark {
  --primary: hsl(0 0% 100%);
}
@theme inline {
  --color-primary: var(--primary);
}
```

**Why**: Tailwind v4 does not support `@theme` inside selectors.

### 3. Double `hsl()` Wrapping

```css
/* WRONG */
@layer base {
  body {
    background-color: hsl(var(--background));  /* Already has hsl() */
  }
}

/* CORRECT */
@layer base {
  body {
    background-color: var(--background);
  }
}
```

**Why**: Variables already contain `hsl()`, double-wrapping creates `hsl(hsl(...))`.

### 4. Colors in `tailwind.config.ts`

```typescript
// WRONG -- v4 ignores theme.extend.colors
export default {
  theme: {
    extend: {
      colors: {
        primary: 'hsl(var(--primary))'
      }
    }
  }
}

// CORRECT -- delete tailwind.config.ts entirely
// Use @theme in CSS instead
```

**Why**: Tailwind v4 completely ignores `theme.extend.colors` in config files.

### 5. Missing `@theme inline` Mapping

```css
/* WRONG -- bg-background class won't exist */
:root {
  --background: hsl(0 0% 100%);
}

/* CORRECT */
:root {
  --background: hsl(0 0% 100%);
}
@theme inline {
  --color-background: var(--background);
}
```

**Why**: `@theme inline` generates the utility classes. Without it, `bg-background` does not exist.

## Configuration Gotchas

### 6. Wrong components.json Config (shadcn)

```json
// WRONG
{
  "tailwind": {
    "config": "tailwind.config.ts"
  }
}

// CORRECT
{
  "tailwind": {
    "config": ""
  }
}
```

### 7. Using PostCSS Instead of Vite Plugin

```typescript
// WRONG (v3 way)
export default defineConfig({
  css: {
    postcss: './postcss.config.js'
  }
})

// CORRECT (v4 way)
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()]
})
```

### 8. Missing Path Aliases

```json
// tsconfig.app.json -- required for @/ imports
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## Color System Gotchas

### 9. Using `dark:` Variants for Semantic Colors

```tsx
// WRONG -- semantic tokens already respond to theme
<div className="bg-primary dark:bg-primary-dark" />

// CORRECT
<div className="bg-primary" />
```

**Why**: With proper CSS variable setup, `bg-primary` automatically responds to the `.dark` class.

### 10. Hardcoded Color Values

```tsx
// WRONG
<div className="bg-blue-600 dark:bg-blue-400" />

// CORRECT
<div className="bg-primary" />
```

**Why**: Semantic tokens enable theme switching and reduce repetition.

## Component Gotchas

### 11. Missing `cn()` Utility

```tsx
// WRONG
<div className={`base ${isActive && 'active'}`} />

// CORRECT
import { cn } from '@/lib/utils'
<div className={cn("base", isActive && "active")} />
```

**Why**: `cn()` properly merges and deduplicates Tailwind classes using `clsx` + `tailwind-merge`.

### 12. Empty String in Radix Select

```tsx
// WRONG
<SelectItem value="">Select an option</SelectItem>

// CORRECT
<SelectItem value="placeholder">Select an option</SelectItem>
```

**Why**: Radix UI Select does not allow empty string values.

### 13. Using `forwardRef` in React 19

```tsx
// WRONG -- unnecessary in React 19
const Button = forwardRef<HTMLButtonElement, ButtonProps>((props, ref) => { ... })

// CORRECT -- ref is a regular prop in React 19
function Button({ ref, ...props }: ButtonProps & { ref?: React.Ref<HTMLButtonElement> }) { ... }
```

### 14. Using Arbitrary Values Instead of @theme

```tsx
// WRONG
<div className="bg-[oklch(45%_0.2_260)]" />

// CORRECT -- extend @theme instead
// In CSS: @theme { --color-brand: oklch(45% 0.2 260); }
<div className="bg-brand" />
```

## Installation Gotchas

### 15. Wrong Tailwind Package

```bash
# WRONG
npm install tailwindcss@^3.4.0

# CORRECT
npm install tailwindcss@^4.1.0
npm install @tailwindcss/vite
```

### 16. Missing Dependencies

```json
{
  "dependencies": {
    "tailwindcss": "^4.1.0",
    "@tailwindcss/vite": "^4.1.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1"
  },
  "devDependencies": {
    "@types/node": "^24.0.0"
  }
}
```

### 17. tw-animate-css Import Error

```bash
# WRONG -- deprecated package
npm install tailwindcss-animate

# CORRECT -- use tw-animate-css or native CSS animations
npm install tw-animate-css
```

- `tailwindcss-animate` is deprecated in Tailwind v4
- Causes import errors during build
- shadcn/ui docs may still reference it (outdated)

### 18. Duplicate `@layer base` After shadcn init

```css
/* WRONG -- shadcn init may add a duplicate */
@layer base {
  body { background-color: var(--background); }
}
@layer base {
  * { border-color: hsl(var(--border)); }
}

/* CORRECT -- merge into single block */
@layer base {
  * { border-color: var(--border); }
  body {
    background-color: var(--background);
    color: var(--foreground);
  }
}
```

Check `src/index.css` immediately after running `shadcn init` and merge any duplicate `@layer base` blocks.

### 19. Using `@tailwind` Directives

```css
/* WRONG */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* CORRECT */
@import "tailwindcss";
```

### 20. Using `@layer components` for Custom Classes

```css
/* WRONG -- @apply inside @layer components can fail in v4 */
@layer components {
  .btn-custom { @apply bg-primary text-primary-foreground; }
}

/* CORRECT */
@utility btn-custom {
  @apply bg-primary text-primary-foreground;
}
```

## Testing Gotchas

### Not Testing Both Themes

Always test in:
- Light mode
- Dark mode
- System mode
- Both initial load and toggle

### Not Checking Contrast

- Use browser DevTools Lighthouse
- Check contrast ratios (4.5:1 minimum for normal text, 3:1 for large text)
- Test with actual users

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
|-|-|-|
| `bg-primary` doesn't work | Missing `@theme inline` mapping | Add `@theme inline` block |
| Colors all black/white | Double `hsl()` wrapping | Use `var(--color)` not `hsl(var(--color))` |
| Dark mode not switching | Missing ThemeProvider | Wrap app in `<ThemeProvider>` |
| Build fails | `tailwind.config.ts` exists with theme config | Delete the file |
| Text invisible | Wrong contrast colors | Pair background with its foreground token; check contrast |
| `@/` imports fail | Missing path aliases in tsconfig | Add paths to `tsconfig.app.json` |
| `@apply` fails on custom class | Using `@layer components` instead of `@utility` (v4 breaking change) | Use `@utility` |
| Animation errors | Using deprecated `tailwindcss-animate` | Use native CSS animations or `tw-animate-css` |

## Prevention Checklist

Before deploying:

- [ ] No `tailwind.config.ts` file (or it's empty)
- [ ] `components.json` has `"config": ""` (if using shadcn)
- [ ] All colors have `hsl()` wrapper in `:root` (HSL approach) or use OKLCH in `@theme`
- [ ] `@theme inline` maps all variables (HSL approach)
- [ ] `@layer base` does not wrap `:root`
- [ ] Theme provider wraps app
- [ ] Tested in both light and dark modes
- [ ] All text has sufficient contrast
- [ ] No duplicate `@layer base` blocks
- [ ] Using `@import "tailwindcss"` not `@tailwind` directives
- [ ] Using `@tailwindcss/vite` plugin (for Vite projects)
- [ ] No `forwardRef` usage (React 19)

# Theme Setup (CSS-First Configuration)

How to wire a design system into Tailwind CSS v4: how the 3-tier token model maps onto `@theme`, the two complete starter stylesheets (Approach A: OKLCH directly in `@theme`; Approach B: `:root` HSL variables plus `@theme inline`, required for shadcn/ui), Vite setup, and shadcn/ui initialisation. Token architecture itself is defined in the `uiux-design-system` skill (`references/token-architecture.md`, `references/mapped-tokens.md`).

## How Tailwind v4 Maps to the 3-Tier Token System

| Token Tier | Tailwind v4 Implementation |
|-|-|
| **Primitive** (raw values) | CSS custom properties in `:root` — hex/OKLCH/HSL values |
| **Semantic** (intent aliases) | CSS custom properties referencing primitives — `var(--color-purple-500)` |
| **Mapped** (component-ready) | `@theme` block — maps semantic tokens to Tailwind utilities (`bg-primary`, `text-foreground`) |

Dark mode swaps values at the **semantic tier** (not primitives). The `@theme` block and utility classes stay unchanged — they auto-resolve through the alias chain. See `uiux-design-system/references/platform-mapping.md` for the full strategy.

## Mapped Token Categories in @theme

The design system defines four mapped categories. Here's how they map to Tailwind `@theme`:

```css
@theme {
  /* text/* tokens → text-* utilities */
  --color-text-heading: var(--color-neutral-text);
  --color-text-body: var(--color-neutral-text);
  --color-text-action: var(--color-primary-default);
  --color-text-on-action: var(--text-on-action);

  /* surface/* tokens → bg-* utilities */
  --color-surface-page: var(--surface-page);
  --color-surface-default: var(--surface-default);
  --color-surface-action: var(--color-primary-default);

  /* border/* tokens → border-* utilities */
  --color-border-default: var(--border-default);
  --color-border-focus: var(--border-focus);

  /* icon/* mirrors text/* — use the same color utilities */
}
```

This is complementary to the shadcn/ui naming pattern (Approach B below). Both work — choose based on whether you're using shadcn.

## Core Concepts

### Design Token Hierarchy

```
Brand Tokens (abstract)
    --> Semantic Tokens (purpose)
        --> Component Tokens (specific)

Example:
    oklch(45% 0.2 260) --> --color-primary --> bg-primary
```

### Component Architecture

```
Base styles --> Variants --> Sizes --> States --> Overrides
```

## Approach A: Direct @theme with OKLCH (Recommended)

This is the primary v4 pattern. Colors are defined directly in `@theme` using OKLCH for perceptual uniformity. No intermediate CSS variables needed.

```css
/* app.css */
@import "tailwindcss";

@theme {
  /* Semantic color tokens using OKLCH */
  --color-background: oklch(100% 0 0);
  --color-foreground: oklch(14.5% 0.025 264);

  --color-primary: oklch(14.5% 0.025 264);
  --color-primary-foreground: oklch(98% 0.01 264);

  --color-secondary: oklch(96% 0.01 264);
  --color-secondary-foreground: oklch(14.5% 0.025 264);

  --color-muted: oklch(96% 0.01 264);
  --color-muted-foreground: oklch(46% 0.02 264);

  --color-accent: oklch(96% 0.01 264);
  --color-accent-foreground: oklch(14.5% 0.025 264);

  --color-destructive: oklch(53% 0.22 27);
  --color-destructive-foreground: oklch(98% 0.01 264);

  --color-border: oklch(91% 0.01 264);
  --color-ring: oklch(14.5% 0.025 264);
  --color-ring-offset: oklch(100% 0 0);

  --color-card: oklch(100% 0 0);
  --color-card-foreground: oklch(14.5% 0.025 264);

  /* Radius tokens */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;

  /* Animation tokens */
  --animate-fade-in: fade-in 0.2s ease-out;
  --animate-fade-out: fade-out 0.2s ease-in;
  --animate-slide-in: slide-in 0.3s ease-out;
  --animate-slide-out: slide-out 0.3s ease-in;

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
  }

  @keyframes slide-in {
    from { transform: translateY(-0.5rem); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  @keyframes slide-out {
    from { transform: translateY(0); opacity: 1; }
    to { transform: translateY(-0.5rem); opacity: 0; }
  }
}

/* Dark mode variant */
@custom-variant dark (&:where(.dark, .dark *));

/* Dark mode overrides */
.dark {
  --color-background: oklch(14.5% 0.025 264);
  --color-foreground: oklch(98% 0.01 264);

  --color-primary: oklch(98% 0.01 264);
  --color-primary-foreground: oklch(14.5% 0.025 264);

  --color-secondary: oklch(22% 0.02 264);
  --color-secondary-foreground: oklch(98% 0.01 264);

  --color-muted: oklch(22% 0.02 264);
  --color-muted-foreground: oklch(65% 0.02 264);

  --color-accent: oklch(22% 0.02 264);
  --color-accent-foreground: oklch(98% 0.01 264);

  --color-destructive: oklch(42% 0.15 27);
  --color-destructive-foreground: oklch(98% 0.01 264);

  --color-border: oklch(22% 0.02 264);
  --color-ring: oklch(83% 0.02 264);
  --color-ring-offset: oklch(14.5% 0.025 264);

  --color-card: oklch(14.5% 0.025 264);
  --color-card-foreground: oklch(98% 0.01 264);
}

/* Base styles */
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground antialiased;
  }
}
```

## Approach B: CSS Variables + @theme inline (HSL, shadcn/ui compatible)

Use this pattern when integrating with shadcn/ui, which expects `:root` CSS variables with HSL values. This four-step architecture is mandatory when using shadcn.

```css
/* src/index.css */
@import "tailwindcss";
@import "tw-animate-css";

/* Step 1: Define CSS variables at root (NOT inside @layer base) */
:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(222.2 84% 4.9%);
  --primary: hsl(221.2 83.2% 53.3%);
  --primary-foreground: hsl(210 40% 98%);
  --secondary: hsl(210 40% 96.1%);
  --secondary-foreground: hsl(222.2 47.4% 11.2%);
  --muted: hsl(210 40% 96.1%);
  --muted-foreground: hsl(215.4 16.3% 46.9%);
  --accent: hsl(210 40% 96.1%);
  --accent-foreground: hsl(222.2 47.4% 11.2%);
  --destructive: hsl(0 84.2% 60.2%);
  --destructive-foreground: hsl(210 40% 98%);
  --border: hsl(214.3 31.8% 91.4%);
  --ring: hsl(221.2 83.2% 53.3%);
  --card: hsl(0 0% 100%);
  --card-foreground: hsl(222.2 84% 4.9%);
}

.dark {
  --background: hsl(222.2 84% 4.9%);
  --foreground: hsl(210 40% 98%);
  --primary: hsl(217.2 91.2% 59.8%);
  --primary-foreground: hsl(222.2 47.4% 11.2%);
  --secondary: hsl(217.2 32.6% 17.5%);
  --secondary-foreground: hsl(210 40% 98%);
  --muted: hsl(217.2 32.6% 17.5%);
  --muted-foreground: hsl(215 20.2% 65.1%);
  --accent: hsl(217.2 32.6% 17.5%);
  --accent-foreground: hsl(210 40% 98%);
  --destructive: hsl(0 62.8% 30.6%);
  --destructive-foreground: hsl(210 40% 98%);
  --border: hsl(217.2 32.6% 17.5%);
  --ring: hsl(224.3 76.3% 48%);
  --card: hsl(222.2 84% 4.9%);
  --card-foreground: hsl(210 40% 98%);
}

/* Step 2: Map variables to Tailwind utilities */
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-ring: var(--ring);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
}

/* Step 3: Apply base styles (NO hsl() wrapper -- already has hsl) */
@layer base {
  * {
    border-color: var(--border);
  }

  body {
    background-color: var(--background);
    color: var(--foreground);
  }
}
```

Result: `bg-background`, `text-primary`, etc. work automatically. Dark mode switches via `.dark` class -- no `dark:` variants needed for semantic colors.

## Vite Setup

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
})
```

Install:

```bash
pnpm add tailwindcss @tailwindcss/vite
pnpm add -D @types/node
```

## shadcn/ui Initialisation

When using shadcn/ui with Tailwind v4, use **Approach B** (CSS variables + `@theme inline`) above.

### Setup

```bash
pnpm dlx shadcn@latest init
rm -f tailwind.config.ts  # v4 does not use config file
```

### components.json (critical)

```json
{
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true
  }
}
```

`"config": ""` is required -- v4 does not use `tailwind.config.ts`.

### Component Installation

Install foundation components first, then feature components as needed:

```bash
pnpm dlx shadcn@latest add button input label card
```

For complete component guides and UI recipes, see:
- [shadcn-ui.md](shadcn-ui.md) -- component installation, dependencies, gotchas, customization
- [shadcn-recipes.md](shadcn-recipes.md) -- working patterns (forms, data tables, navigation, modals, settings)

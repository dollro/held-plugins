# Animations and Advanced v4 Patterns

Native CSS animations in Tailwind v4 (`@starting-style`, keyframes declared in `@theme`) and advanced configuration: custom utilities with `@utility`, theme modifiers (`inline`, `static`), namespace overrides, `color-mix()` alpha variants and container query tokens. Use these instead of `tailwindcss-animate` and v3 plugins.

## Native CSS Animations

### @starting-style for Entry Animations

```css
/* Native popover animations */
[popover] {
  transition:
    opacity 0.2s,
    transform 0.2s,
    display 0.2s allow-discrete;
  opacity: 0;
  transform: scale(0.95);
}

[popover]:popover-open {
  opacity: 1;
  transform: scale(1);
}

@starting-style {
  [popover]:popover-open {
    opacity: 0;
    transform: scale(0.95);
  }
}
```

### Dialog Animations in @theme

```css
@theme {
  --animate-dialog-in: dialog-fade-in 0.2s ease-out;
  --animate-dialog-out: dialog-fade-out 0.15s ease-in;
}

@keyframes dialog-fade-in {
  from { opacity: 0; transform: scale(0.95) translateY(-0.5rem); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes dialog-fade-out {
  from { opacity: 1; transform: scale(1) translateY(0); }
  to { opacity: 0; transform: scale(0.95) translateY(-0.5rem); }
}
```

Usage in components:

```tsx
<DialogPrimitive.Overlay
  className="fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out"
/>
<DialogPrimitive.Content
  className="... data-[state=open]:animate-dialog-in data-[state=closed]:animate-dialog-out"
/>
```

## Advanced v4 Patterns

### Custom Utilities with @utility

```css
@utility line-t {
  @apply relative before:absolute before:top-0 before:-left-[100vw] before:h-px before:w-[200vw] before:bg-gray-950/5 dark:before:bg-white/10;
}

@utility text-gradient {
  @apply bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent;
}
```

### Theme Modifiers

```css
/* @theme inline: reference other CSS variables */
@theme inline {
  --font-sans: var(--font-inter), system-ui;
}

/* @theme static: always generate CSS variables, even when unused */
@theme static {
  --color-brand: oklch(65% 0.15 240);
}

/* Import with theme options */
@import "tailwindcss" theme(static);
```

### Namespace Overrides

```css
@theme {
  /* Clear all default colors and define your own */
  --color-*: initial;
  --color-white: #fff;
  --color-black: #000;
  --color-primary: oklch(45% 0.2 260);
  --color-secondary: oklch(65% 0.15 200);
}
```

### Semi-transparent Color Variants

```css
@theme {
  --color-primary-50: color-mix(in oklab, var(--color-primary) 5%, transparent);
  --color-primary-100: color-mix(in oklab, var(--color-primary) 10%, transparent);
  --color-primary-200: color-mix(in oklab, var(--color-primary) 20%, transparent);
}
```

### Container Queries

```css
@theme {
  --container-xs: 20rem;
  --container-sm: 24rem;
  --container-md: 28rem;
  --container-lg: 32rem;
}
```

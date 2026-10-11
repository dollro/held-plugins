---
name: uiux-design-tailwindv4
description: "Implements design systems with Tailwind CSS v4: CSS-first @theme config, semantic tokens in OKLCH or HSL, CVA component variants with React 19, responsive layouts, dark mode, native CSS animations, accessibility, optional shadcn/ui. Use when setting up or theming Tailwind v4, building a Tailwind component library, adding dark mode, migrating v3 to v4, or fixing v4 build or color issues. Not for tool-agnostic token architecture (uiux-design-system) or Vue specifics (uiux-design-vue3)."
---

# Tailwind CSS v4 Design Systems

Build production-ready design systems in code with Tailwind CSS v4: CSS-first configuration, semantic tokens, typed component variants, responsive patterns, dark mode and accessibility.

This skill is the **code side** of a design system. The architecture (token tiers, naming, mapped text/icon/surface/border tokens, component specs, accessibility) comes from the `uiux-design-system` skill; read it there instead of reinventing it. Targets Tailwind v4; for v3 projects start with `references/migration-v3-to-v4.md`.

## Key v4 changes

| v3 Pattern | v4 Pattern |
|-|-|
| `tailwind.config.ts` | `@theme` in CSS |
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `darkMode: "class"` | `@custom-variant dark (&:where(.dark, .dark *))` |
| `theme.extend.colors` | `@theme { --color-*: value }` |
| `require("tailwindcss-animate")` | CSS `@keyframes` in `@theme` + `@starting-style` |
| PostCSS plugin | `@tailwindcss/vite` plugin (for Vite projects) |

## Workflow

1. **Check the project.** Tailwind version, build tool (Vite → `@tailwindcss/vite`), framework, React version, whether shadcn/ui is used, existing tokens (DTCG files, CSS variables). On v3, migrate first.
2. **Pick the theme approach.**
   - **Approach A (default):** semantic tokens in OKLCH directly in `@theme`, dark overrides in `.dark`.
   - **Approach B (required with shadcn/ui):** `:root` HSL variables, mapped with `@theme inline`, base styles without a second `hsl()` wrapper.
3. **Map the token tiers.** Primitives and semantics as CSS custom properties, the mapped tier in `@theme` so utilities like `bg-surface-action` or `bg-primary` exist. Dark mode remaps the semantic tier; `@theme` and classes stay unchanged.
4. **Set up utilities.** `cn()` (clsx + tailwind-merge), shared focus-ring and disabled classes.
5. **Build components** with CVA variants, semantic tokens only, React 19 ref-as-prop, ARIA and visible focus.
6. **Add dark mode** with a ThemeProvider that toggles `.dark` on `<html>`; semantic tokens then switch without `dark:` variants.
7. **Animate natively** with keyframes in `@theme` and `@starting-style`.
8. **Verify** both themes, WCAG contrast (4.5:1 text, 3:1 UI), keyboard focus, a clean build with no `tailwind.config.ts`.

## Rules

**Do**
- Configure in CSS with `@theme`; import with `@import "tailwindcss"`.
- Use semantic tokens (`bg-primary`, not `bg-blue-500`) and pair every background with a foreground token.
- Use OKLCH for perceptual uniformity (or HSL with shadcn/ui).
- Compose variants with CVA; use `size-*` for equal width and height.
- Add ARIA attributes and focus states; test light and dark themes and check contrast.
- Use the `@tailwindcss/vite` plugin for Vite projects.

**Don't**
- Don't keep a `tailwind.config.ts` or use `@tailwind` directives.
- Don't use `forwardRef` (React 19 passes ref as a prop).
- Don't use arbitrary values or hardcoded colors; extend `@theme` instead, and don't mix hardcoded and semantic colors in one component.
- Don't put `:root` inside `@layer base`, and don't nest `@theme` inside selectors (`.dark { @theme {} }`).
- Don't double-wrap colors (`hsl(var(--background))` when the variable already holds `hsl()`).
- Don't use `@layer components` for custom classes; use `@utility`.

## Quick diagnosis

| Symptom | Fix |
|-|-|
| `bg-primary` doesn't work | Add the `@theme inline` mapping |
| Colors all black/white | Use `var(--color)`, not `hsl(var(--color))` |
| Dark mode not switching | Wrap the app in `<ThemeProvider>`, check `@custom-variant dark` |
| Build fails | Delete `tailwind.config.ts` |
| `@apply` fails on custom class | Use `@utility` instead of `@layer components` |

Full list with causes and a prevention checklist: `references/common-gotchas.md`.

## References

| Read | When |
|-|-|
| `references/theme-setup.md` | Setting up or changing the theme: 3-tier mapping to `@theme`, mapped token categories, full Approach A (OKLCH) and B (HSL + `@theme inline`) stylesheets, Vite setup, shadcn/ui init and `components.json` |
| `references/component-patterns.md` | Writing components: `cn()` and shared utilities, CVA button, compound card, form inputs with React Hook Form + Zod, responsive grid and container |
| `references/dark-mode.md` | Implementing dark mode: ThemeProvider (shadcn style and React 19 with `resolvedTheme`), mode toggle, flash-of-wrong-theme fixes, testing checklist |
| `references/animations-advanced.md` | Animations (`@starting-style`, dialog keyframes) and advanced config: `@utility`, theme modifiers, namespace overrides, `color-mix()` variants, container queries |
| `references/shadcn-ui.md` | Installing and customising shadcn/ui components, known gotchas, component catalogue |
| `references/shadcn-recipes.md` | Working shadcn/ui page patterns: contact form, data table, modal CRUD, responsive navigation, settings page |
| `references/migration-v3-to-v4.md` | Migrating a v3 project: checklist, pattern changes, hardcoded colors to semantic tokens, verification |
| `references/common-gotchas.md` | Debugging build, color, config or component errors; pre-deploy prevention checklist |

From the `uiux-design-system` skill: `references/token-architecture.md` (tiers, naming), `references/mapped-tokens.md` (text/icon/surface/border tables), `references/token-categories.md` (color scale generation), `references/typography.md` (type scale), `references/platform-mapping.md` (DTCG → CSS → Tailwind pipeline), `references/theming-multi-brand.md` (multi-brand), `references/component-patterns.md` (component specs), `references/accessibility.md` (WCAG 2.2 + EAA).

# Theming, Dark Mode and Multi-Brand Strategies

How to structure modes (light, dark, high contrast), build a dark theme by remapping the semantic tier, and choose between branded house and house of brands for multiple brands. CSS output for modes is in `platform-mapping.md`; high-contrast and reduced-motion tokens in `accessibility.md`. For Tailwind v4 dark mode (ThemeProvider, `@custom-variant`, OKLCH), see the `uiux-design-tailwindv4` skill.

## Modes

Three modes minimum:

| Mode | Purpose |
|-|-|
| Light | Default — light backgrounds, dark text |
| Dark | Inverted neutral scale, adjusted feedback colors |
| High Contrast | Maximum contrast, bolder borders, no transparency — WCAG AAA + `forced-colors` |

## Dark Mode Strategy

**Same token names, different values.** Every component that references `primary/default` automatically gets the correct color in both modes. This is the entire power of the semantic layer.

**Quick approach:** Rough pass first, then refine for accessibility.

1. **Invert the scale direction:** Where light mode uses `neutral/800` for headings, dark mode uses `neutral/100`
2. **Lighten primary colors:** Primary actions shift from `500` → `400` or `300` to maintain contrast on dark backgrounds
3. **Darken surfaces:** Page background goes from white → `neutral/900` or `neutral/950`
4. **Keep action surfaces recognizable:** Buttons can stay the same primary color if contrast is sufficient
5. **Test with accessibility tools:** Run WCAG contrast checks after the initial pass

**What stays the same in dark mode:**
- `text/on-action` (text on buttons) — typically stays white in both modes
- Semantic intent — `error` is still red, `success` is still green
- Component structure — nothing in the component layer changes

**What changes:**
- Text colors get lighter (higher neutral values)
- Surface colors get darker
- Border colors adjust for visibility against dark backgrounds
- Primary/accent colors may shift to lighter variants
- Shadows need higher opacity
- Feedback backgrounds shift to 900–950 shades

The light/dark values for every mapped token are in `mapped-tokens.md`.

## Multi-Brand Strategies

### Branded House

One house, brands that share the same system with slightly different visual identity. Think one soft-drink brand with regular, zero and diet lines — same components, primary color differs.

**Implementation:** In the semantic/alias collection, add modes per brand. Each mode remaps only the **primary** (and maybe secondary) color scales. Success, error, warning, neutral, fonts, spacing — all stay identical.

```
Semantic Collection Modes:
  Brand A → primary/* maps to purple scale
  Brand B → primary/* maps to blue scale
  Brand C → primary/* maps to teal scale
  (success, error, warning, neutral all identical)
```

### House of Brands

Completely different visual identities, like separate drink brands owned by one company.

**Implementation:** Separate design system files per brand. Each brand has its own primitive collection with entirely different color scales, fonts, and potentially different spacing.

### When to Use Which

| Scenario | Strategy | Token Approach |
|-|-|-|
| Same components, slightly different colors | Branded House | Semantic modes |
| Completely different visual identities | House of Brands | Separate design system files |
| White-label / customer-specific theming | Branded House with Tier 1 overrides | Primitive swap + semantic auto-resolves |
| Design language evolution (v1 → v2) | Branded House | Legacy + new theme as modes |

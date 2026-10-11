# Typography and Type Scale

How to define typography tokens, generate a type scale snapped to the 4px grid, set line heights and paragraph spacing, name text styles, and scale type responsively. A complete example scale (with fonts, weights and usage) is in `design-system-template.md` §3.

## Primitives

`font.family.{sans|serif|mono}`, `font.size.{100–900}` on rem scale, `font.weight.{regular|medium|semibold|bold}`, `font.line-height.{tight|normal|relaxed}`, `font.letter-spacing.{tight|normal|wide}`, `font.paragraph-spacing.{none|md}`.

## Generating a Type Scale

1. Set base size to **16px** (paragraph `<p>` size)
2. Choose a scale ratio:
   - **Minor Third** (1.2) — conservative, good for apps
   - **Major Third** (1.25) — balanced, popular choice
   - **Perfect Fourth** (1.333) — more dramatic, good for marketing
3. **Snap each generated size to the nearest multiple of 4** — keeps everything crisp on 1x, 2x, 3x displays

| Scale Output | 4px Snap | Used For |
|-|-|-|
| 12px | 12px | Extra small / captions |
| 14px | 14px | Small text (use sparingly) |
| 16px | 16px | Base paragraph |
| 20px | 20px | H6 |
| 25px | 24px | H5 |
| 31.25px | 32px | H4 |
| 39px | 40px | H3 |
| 48.8px | 48px | H2 |
| 61px | 60px | H1 |

## Line Height

- **Headings:** `font-size × 1.2`, snapped to nearest multiple of 4
- **Body text:** `font-size × 1.4–1.5`, snapped to nearest multiple of 4

| Font Size | × Multiplier | Snapped | Use |
|-|-|-|-|
| 60px | × 1.2 = 72 | 72px | H1 line height |
| 48px | × 1.2 = 57.6 | 56px | H2 line height |
| 40px | × 1.2 = 48 | 48px | H3 line height |
| 32px | × 1.2 = 38.4 | 40px | H4 line height |
| 24px | × 1.2 = 28.8 | 28px | H5 line height |
| 20px | × 1.2 = 24 | 24px | H6 line height |
| 16px | × 1.5 = 24 | 24px | Body line height |

**Paragraph spacing:** H1: 64–80px, H2: 48–64px, H3: 32–48px, H4: 24–32px, Body: 16–20px.

## Text Style Naming

Hierarchical with `/` separator:

```
Heading/H1, Heading/H2, Heading/H3, Heading/H4, Heading/H5, Heading/H6
Body/Large, Body/Large - Semi Bold, Body/Large - Link
Body/Medium, Body/Medium - Semi Bold, Body/Medium - Link
Body/Small, Body/Small - Semi Bold, Body/Small - Link
Body/Extra Small, Body/Extra Small - Semi Bold, Body/Extra Small - Link
```

Each text style bundles: font family + font size + line height + font weight + paragraph spacing.

## Responsive Typography

**Cardinal rule:** Body text stays the same size on mobile (16px). **Only headings scale down.** Body text at 14px on mobile is too small for comfortable reading.

| Variable | Desktop | Mobile |
|-|-|-|
| H1 font-size | 60px | 40px |
| H2 font-size | 48px | 32px |
| H3 font-size | 40px | 32px |
| H4 font-size | 32px | 24px |
| H5 font-size | 24px | 20px |
| H6 font-size | 20px | 20px |
| Body font-size | 16px | 16px (unchanged) |

**Accessibility floor:** Never go below 12px for any readable text. Body text minimum is 16px. 14px only for supplementary content.

## Semantic Typography Tokens

`font.heading.*`, `font.body.*`, `font.caption.*`, `font.label.*` — each bundles family + size + weight + line-height + letter-spacing using DTCG composite `typography` type.

Use `rem` for font sizes (WCAG 1.4.4 — Resize Text). Pick one scale convention (numeric `100–900` or t-shirt `xs–xl`) and use it everywhere.

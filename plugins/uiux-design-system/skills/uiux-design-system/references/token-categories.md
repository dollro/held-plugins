# Token Categories

Guidance per token category: which primitives and semantic tokens to define, how to generate color scales, and the 4px number scale that spacing, sizing, borders and radii derive from. Typography has its own file (`typography.md`); the mapped tier is in `mapped-tokens.md`.

**Priority for new systems:** Color > Typography > Number Scale (Spacing) > Border Radius > Shadow > Sizing > Border > Motion > Opacity > Z-Index > Breakpoints > Grid. The first three cover ~80% of typical UI token needs.

## 1. Color

**Primitives:** Hue scales `50`–`950` (lightest to darkest). E.g., `color.blue.50` through `color.blue.950`. Include `color.neutral.*` for grays.

**Minimum scales needed:**

| Scale | Purpose | Typical Hue |
|-|-|-|
| **Primary** | Brand identity, CTAs, active states | Your brand color |
| **Neutral** | Text, backgrounds, borders, disabled states | Gray |
| **Error/Danger** | Form errors, destructive actions, alerts | Red |
| **Success** | Confirmations, completed states | Green |
| **Warning** | Caution alerts, attention needed | Orange / Amber |
| **Information** | Informational alerts, help text | Blue |

Start with these six. Add a secondary brand color only when needed.

**Scale generation (opacity method):**
1. Start with your core brand color as a solid hex (e.g., `#6C5CE7` at position 500)
2. For lighter shades (50–400): place the core color on a **white** background, reduce opacity in even intervals (e.g., 10% steps: 50→~10%, 100→~20%, 200→~30%, etc.)
3. For darker shades (600–900): place the core color on a **black** background, reduce opacity
4. **Always convert resulting colors to solid hex codes** — opacity-based tokens cause problems in dark mode and when layering elements

For programmatic palette generation and format conversion, see `color-utilities.md`.

**Semantic patterns:**
- `color.background.*` — surfaces, overlays, elevated containers
- `color.text.*` — foreground content, headings, body, muted
- `color.border.*` — dividers, outlines, input borders
- `color.interactive.*` — buttons, links, focus rings, hover states
- `color.feedback.*` — success, warning, error, info

Use `on-*` for contrast pairs: `color.text.on-primary` pairs with `color.background.primary`. Always define both sides. Name by intent (`danger`) not appearance (`red`).

## 2. Typography

See `typography.md` for primitives, type scale generation, line heights, text style naming and responsive rules.

## 3. Number Scale (4px Grid)

All spacing, sizing, border width, and border radius values derive from **multiples of 4**:

```
scale/0    = 0px
scale/25   = 1px    (exception: borders — the only non-4px value)
scale/50   = 2px    (exception: focus rings)
scale/100  = 4px
scale/200  = 8px
scale/300  = 12px
scale/400  = 16px
scale/500  = 20px
scale/600  = 24px
scale/700  = 28px
scale/800  = 32px
scale/900  = 36px
scale/1000 = 40px
scale/1100 = 48px
scale/1200 = 64px
```

**Why multiples of 4?** Screens render in even pixel counts — 4px aligns perfectly on 1x, 2x, and 3x displays. Consistent visual rhythm, easy mental math.

**Rule:** Never mix odd and even numbers. The only exceptions are 1px (borders) and 2px (focus rings).

Border width and border radius reference this scale directly:

```
border-width/default  → scale/25  (1px)
border-width/focus    → scale/50  (2px)
border-radius/none    → 0
border-radius/sm      → scale/100 (4px)
border-radius/md      → scale/200 (8px)
border-radius/lg      → scale/300 (12px)
border-radius/xl      → scale/400 (16px)
border-radius/full    → 9999      (pill/circle)
```

## 4. Spacing

**Primitives:** 4px base grid — `space.1` (4px) through `space.16` (64px).

**Semantic patterns:** `space.inline.*` (horizontal), `space.stack.*` (vertical), `space.inset.*` (padding). T-shirt sizing: `xs`, `sm`, `md`, `lg`, `xl`.

Don't create component-specific spacing at semantic level (`space.card-padding`) — that belongs in component tier as `card.space.inset`.

## Categories 5–12

| # | Category | Primitive pattern | Semantic pattern | Key convention |
|-|-|-|-|-|
| 5 | Sizing | `size.{1–16}` (4px grid) | `size.icon.{sm\|md\|lg}`, `size.avatar.{sm\|md\|lg}` | Separate from spacing — different purpose |
| 6 | Border | `border.width.{1\|2\|4}`, `border.style.{solid\|dashed}` | DTCG composite `border` type | Colors under `color.border.*`, not here |
| 7 | Border Radius | `radius.{none\|xs\|s\|m\|l\|xl\|full}` | `radius.interactive`, `radius.container` | `full` = 9999px (pill). 5–7 values max |
| 8 | Shadow | `shadow.elevation.{1–5}` (DTCG shadow type) | `shadow.card`, `shadow.dropdown`, `shadow.modal` | Map levels to UI layering |
| 9 | Z-Index | Inherently semantic — no primitives | `z.base`, `z.dropdown`, `z.sticky`, `z.modal`, `z.toast` | 100-increment gaps between values |
| 10 | Breakpoints | Inherently semantic — no primitives | `breakpoint.{sm\|md\|lg\|xl}` | Mobile-first. No device names |
| 11 | Motion | `motion.duration.{instant\|fast\|normal\|slow}`, `motion.easing.*` | `motion.transition.default`, `motion.enter`, `motion.exit` | 3–4 durations. DTCG `transition` type |
| 12 | Opacity | `opacity.{subtle\|medium\|strong\|opaque}` | `opacity.disabled`, `opacity.overlay` | 4–6 values. Consider alpha colors instead |

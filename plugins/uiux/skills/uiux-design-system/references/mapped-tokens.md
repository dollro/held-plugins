# Mapped Token Tables (Tier 3)

The complete mapped/component tier: the four categories of tokens (text, icon, surface, border) that are applied directly to components, each with state variants and light/dark alias values. Use these tables as a checklist when building the mapped tier; `starter-template.md` has them as DTCG JSON. Tool plugins (Penpot, Figma) and `uiux-image2design` read this file for the canonical set.

Only create further component tokens when a component diverges from these categories (see `component-patterns.md` for per-component bindings).

## Text Tokens

| Token | Purpose | Light Mode | Dark Mode |
|-|-|-|-|
| `text/heading` | Headings (h1–h6) | neutral/800 | neutral/100 |
| `text/body` | Body paragraphs | neutral/700 | neutral/200 |
| `text/action` | Links, clickable text | primary/500 | primary/400 |
| `text/action-hover` | Link hover state | primary/600 | primary/300 |
| `text/on-action` | Text on primary surfaces (buttons) | white | white |
| `text/disabled` | Inactive/disabled text | neutral/400 | neutral/600 |
| `text/success` | Success messages | success/default | success/default |
| `text/warning` | Warning messages | warning/default | warning/default |
| `text/error` | Error messages | error/default | error/default |
| `text/information` | Info messages | information/default | information/default |

## Icon Tokens

Icon tokens **mirror text tokens** intentionally. When an icon sits next to text (which is most of the time), they should be the same color. Having different warning text and warning icon colors creates inconsistency.

| Token | Maps to same alias as |
|-|-|
| `icon/default` | Same as `text/body` (neutral/700) |
| `icon/action` | Same as `text/action` |
| `icon/action-hover` | Same as `text/action-hover` |
| `icon/on-action` | Same as `text/on-action` |
| `icon/disabled` | Same as `text/disabled` |
| `icon/success` | Same as `text/success` |
| `icon/error` | Same as `text/error` |
| `icon/warning` | Same as `text/warning` |
| `icon/information` | Same as `text/information` |

## Surface Tokens

Surface = the background fill of elements.

| Token | Purpose | Light Mode | Dark Mode |
|-|-|-|-|
| `surface/page` | Full page background | white | neutral/900 |
| `surface/default` | Card/container backgrounds | neutral/50 or white | neutral/800 |
| `surface/action` | Primary action elements (buttons) | primary/500 | primary/500 |
| `surface/action-hover` | Hovered action elements | primary/600 | primary/400 |
| `surface/action-hover-light` | Subtle hover (input fields, rows) | primary/50 | primary/900 |
| `surface/disabled` | Disabled element backgrounds | neutral/100 | neutral/800 |
| `surface/success` | Success alert background | success/50 | success/900 |
| `surface/warning` | Warning alert background | warning/50 | warning/900 |
| `surface/error` | Error alert background | error/50 | error/900 |
| `surface/information` | Info alert background | information/50 | information/900 |

**Key insight:** Alert/notification surfaces use the lightest shade (50 in light mode, 900 in dark mode) so text remains readable against them.

## Border Tokens

| Token | Purpose | Light Mode | Dark Mode |
|-|-|-|-|
| `border/default` | Standard borders | neutral/200 | neutral/700 |
| `border/action` | Active/interactive element borders | primary/500 | primary/400 |
| `border/action-hover` | Hovered interactive borders | primary/600 | primary/300 |
| `border/focus` | Focus ring color (accessibility critical) | primary/500 | primary/400 |
| `border/disabled` | Disabled element borders | neutral/200 | neutral/700 |
| `border/success` | Success state borders | success/200 | success/700 |
| `border/warning` | Warning state borders | warning/200 | warning/700 |
| `border/error` | Error state borders | error/200 | error/700 |
| `border/information` | Info state borders | information/200 | information/700 |

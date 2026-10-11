# Visual Reference Naming

How to name and organise screenshots or other visual references that inform a design system. The flat naming convention maps directly to the component tiers in `component-architecture.md`, so references stay grep-friendly and easy to match to components.

## Convention

```
{tier}--{component}.{breakpoint}.{variant}.{state}.png
```

| Segment | Values | Purpose |
|-|-|-|
| tier | `atom`, `molecule`, `organism`, `pattern`, `screen` | Maps 1:1 to component architecture |
| component | kebab-case element name | What UI piece |
| breakpoint | `tablet`, `mobile` (omit for desktop — it's the default) | Responsive variant |
| variant | `primary`, `compact`, `dark`, `collapsed`, etc. | Optional variation |
| state | `hover`, `active`, `error`, `loading`, `empty`, etc. | Optional interaction state |

## Examples

```
screen--dashboard.png                    # desktop (implied default)
screen--dashboard.tablet.png
screen--dashboard.mobile.png
organism--header.png
organism--header.mobile.menu-open.png
organism--sidebar.collapsed.png
molecule--card.content.hover.png
molecule--form-field.error.png
atom--button.primary.png
atom--button.primary.hover.png
atom--input.text.focus.png
pattern--section.hero-centered.png
pattern--state.empty.png
```

## Grep-Friendly Patterns

- `screen--*` — all full screens
- `*mobile*` — all mobile breakpoints
- `*.hover.*` — all hover states
- `organism--*` — all organisms
- `atom--button*` — all button references

## Tips

- One concept per screenshot.
- Capture states — hover/focus/disabled drive 80% of token decisions.
- Dark mode gets a variant (`screen--dashboard.dark.png`), not a separate folder.
- Flat directory until 100+ images.

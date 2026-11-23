---
brand: <name>
colors: {hero: "#<hex>", text: "#<hex>", background: "#<hex>", dark_ground: "#<hex>", light_ground: "#<hex>", secondary: "#<hex>"}
fonts: {heading: "<family>", body: "<family>"}
font_files: {heading: ["<path>"], body: ["<path>"]}
logos: ["<path to logo>", "<path to logo on dark>"]
safe_margin: 4%   # of frame width
---

# Brand lock · <name>

Written by export_brand_lock.py from design-guide.json, or by hand from stock-take's brand interview when there is no master. Motion and HTML work use only what is listed here.

## Colours

| Role | Hex | Use |
|---|---|---|
| hero | #<hex> | the one thing per frame: the key word, number, CTA, end-card mark; rationed |
| text | #<hex> | titles and body on light grounds |
| background | #<hex> | default ground |
| dark ground | #<hex> | dark stage |
| secondary | #<hex> | supporting shapes; never competes with the hero |

## Fonts

| Use | Family | Files |
|---|---|---|
| heading | <family> | <path to .ttf/.otf/.woff2, or **missing**> |
| body | <family> | <path, or **missing**> |

## Logo

- `<path>` (on light) · `<path>` (on dark)
- Clear space: at least the logo's own height on every side. Lands once, with weight, usually on the end card.

## Safe zones

- Margin: <n>% of the frame width on every side.
- Protected: <logo position, bands, legal line>

## Never

- no fonts other than the heading and body fonts listed here
- no colours outside this palette; no off-palette gradients
- never stretch, recolour, rotate or crop the logo; keep its clear space
- never cover or move protected zones (logo, bands, footer, legal lines)
- <brand-specific: words never used, imagery never shown>

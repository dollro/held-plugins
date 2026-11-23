---
brand: acme-master
colors: {hero: "#E8590C", text: "#1B1B1F", background: "#FFFFFF", dark_ground: "#2E3440", light_ground: "#F4F1EC", secondary: "#1F6F8B", support_3: "#99A3A4", support_4: "#F2C14E", support_5: "#5B8C5A", support_6: "#B23A48"}
fonts: {heading: "Inter", body: "Liberation Sans"}
font_files: {heading: [], body: []}
logos: ["logos/acme-logo.png"]
safe_margin: 3.8%   # of frame width
---

# Brand lock · acme-master

Exported from design-guide.json (source: acme-master.pptx, built by deck-design-guide's make_acme_master.py). Illustrative example · fictional brand. Motion and HTML work use only what is listed here.

## Colours

| Role | Hex | Use |
|---|---|---|
| hero (`accent`) | #E8590C | the one thing per frame: the key word, number, CTA, end-card mark; rationed |
| text (`ink`) | #1B1B1F | titles and body on light grounds |
| background (`bg`) | #FFFFFF | default ground |
| dark ground (`dark2`) | #2E3440 | dark stage or text on light2 |
| light ground (`light2`) | #F4F1EC | panels, alternative ground |
| secondary (`accent2`) | #1F6F8B | second data series, supporting shapes; never competes with the hero |
| support 3 (`accent3`) | #99A3A4 | charts and diagrams only |
| support 4 (`accent4`) | #F2C14E | charts and diagrams only |
| support 5 (`accent5`) | #5B8C5A | charts and diagrams only |
| support 6 (`accent6`) | #B23A48 | charts and diagrams only |

## Fonts

| Use | Family | Files |
|---|---|---|
| heading | Inter | **missing**: add the font files (licensed) before rendering HTML or video |
| body | Liberation Sans | **missing** in this example: on a real project, the licensed font files from the brand owner |

## Logo

- `logos/acme-logo.png`
- Clear space: at least the logo's own height on every side. Lands once, with weight, usually on the end card.

## Safe zones

- Margin: 0.5 in on a 13.33 × 7.5 in slide; keep the same proportion in video frames.
- Protected (master): Acme logo (picture) at x 11.6, y 6.8, 1.2 × 0.4 in
- Protected (master): Confidentiality (text) at x 0.5, y 6.9, 5.0 × 0.3 in

## Never

- no fonts other than the heading and body fonts listed here
- no colours outside this palette; no off-palette gradients
- the hero colour marks one thing per frame, never a whole background unless the guide allows an accent stage
- never stretch, recolour, rotate or crop the logo; keep its clear space
- never cover or move protected zones (logo, bands, footer, legal lines)

## Open

- Font files missing for: Inter, Liberation Sans (example ships without font files; HTML rendering falls back until they are added)

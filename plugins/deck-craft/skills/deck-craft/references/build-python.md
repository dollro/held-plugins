# Building with deckkit (Python)

Read this before writing `build_deck.py`. Requirements: Python 3.9+, `python-pptx` 1.0.x (`pip install "python-pptx>=1.0,<1.1"`, in a virtual environment where possible; `video_slide()` uses `add_movie`, which python-pptx does not promise to keep stable, so stay on the tested minor version). LibreOffice and poppler (`pdftoppm`) are optional, for rendering; Pillow for the contact sheet.

## Skeleton

```python
import sys
sys.path.insert(0, "<path to this skill>/scripts")   # in the plugin: ${CLAUDE_PLUGIN_ROOT}/skills/deck-craft/scripts
from deckkit import *

prs = new_deck("brand.potx", mode="consult")          # or new_deck(mode="keynote"); no template = deckkit theme
apply_design_guide(prs, "design-guides/acme/design-guide.json")   # if deck-design-guide produced one
set_sections(["Diagnosis", "Options", "Plan"])

title_slide(prs, "Restoring wholesale margin", "Steering committee · 12 Nov 2026")
s = content_slide(prs, "Café chains drive most of the decline: their margin fell 9 points", section="Diagnosis")
bar_chart(s, ["Café chains", "Independents", "Grocery", "Online"], [-9, -4, -3, 1], highlight=0,
          w=8.3, y=body_top(s) + 0.4, unit="Change in gross margin, FY2023-25, pp", number_format="+0.0;-0.0")
callout(s, "So what", ["Chains are 45% of volume", "Contracts reprice once a year"], y=body_top(s))
source(s, "Source: client finance data (FY2023-25), as provided in brief; team analysis")
prs.save("deck.pptx")
```

Then: `python check_deck.py deck.pptx` and `python render.py deck.pptx`.

## Layout grid (16:9, 13.333 x 7.5 in), deckkit theme

| Zone | Position | Style |
|---|---|---|
| Tracker (section label) | x 0.5, y 0.32 | 9 pt bold accent, upper case |
| Section navigator | right of tracker, ends x 11.1 | 9 pt, current section in accent |
| Illustrative label | top right, x 11.33 | 9 pt grey, outlined |
| Action title | x 0.5, y 0.58, w 10.63, h 0.9 | 20 pt bold, ≤ 2 lines |
| Rule under title | y 1.55 | 0.75 pt light grey |
| Body | y 1.7 to 6.5, x 0.5 to 12.83 | 12-16 pt |
| Footnote / source | y 6.54 / 6.82 | 9 pt grey |
| Page number | bottom right | 9 pt grey |

Chart plus takeaway: chart `w=8.3`, `callout()` default sits at x 9.13, w 3.7. Columns gutter 0.3 in.

In a template deck the title box is the master's; call `body_top(s)` and pass `y=` to exhibit helpers so the body starts under it.

## Templates

- `new_deck(template)` opens .pptx or .potx, reads theme colours (accent1 → accent, dk1 → ink) and the body font, and finds layouts named Blank and Title Only (also German names Leer, Nur Titel).
- `list_layouts(prs)` prints layouts and placeholders. `use_layouts(prs, cover="Title Slide", divider="Section Header", statement="Blank dark", title_only="Nur Titel", blank="Leer")` maps roles explicitly, by name or index.
- Roles: `cover` (title_slide fills the master's title and subtitle placeholders), `title_only` (content_slide puts the action title in the master title placeholder; only its size is set so it fits two lines, 18-28 pt), `divider` (master's Section Header placeholders carry the takeaway and the section name), `blank` (exhibit and keynote slides), `statement` (keynote slides, falls back to blank).
- If the master's title sits in the tracker zone, no tracker or navigator is drawn: the master owns that zone.
- Keynote in a template: `new_deck(t, mode="keynote", stage="master" | "dark" | "accent")` or `keynote_stage(...)` per stretch of slides. `master` keeps background, logo, footer and uses the template's dark text; `dark` paints a dark stage on the template's layout (logo and footer stay); `accent` is for one or two STAR moments.
- Non-16:9 templates print a warning: pass explicit `x, y, w, h` or work in placeholders.
- Delete the template's sample slides only after building yours, and re-open the result to check.

## Theme without a template

`set_theme("consult", accent="C8102E", font="Calibri")` after `new_deck()`. Keys: font, ink, grey, light, pale, accent, accent_pale, negative, bg, chart_greys. Keynote default: black stage, white type, accent 2F80ED.

## Chart recipes

- Ranking: `bar_chart(..., horizontal=True)`, sorted largest first, accent on the bar the title names. Category labels sit at the low end so negative bars stay readable.
- Bridge: `waterfall(steps)`, first and last `total`; ≤ 7 steps; group small drivers into "Other". Small deltas get their label below the bar automatically.
- Mix over time: `column_chart(stacked=True)` ≤ 4 series; `percent=True` for 100% composition.
- Trend: `line_chart`, the series the title talks about in accent, ≤ 3 lines.
- Unit line above every chart: measure, scope, period, unit.
- Number formats: one decimal under 10, none above; currency in the unit line, not on every label.

## Video slides (clips from motion-craft)

```python
s = video_slide(prs, "renders/beats/B02.mp4", "renders/beats/B02.jpg", beat="B02")   # full bleed
s = video_slide_from_clips(prs, "renders/clips.json", "B12")                           # resolve from clips.json
notes(s, "...")
```

- The clip is embedded (the .pptx grows by its size) and plays on click; nothing autoplays. The poster is required: PowerPoint shows it before play, LibreOffice and thumbnails show only it.
- H.264 MP4 with AAC or no audio plays in PowerPoint for Windows and Mac and imports into Keynote. motion-qa's beat export writes that format; re-encode other sources with `ffmpeg -i in.mov -c:v libx264 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4`.
- Before a deck with clips goes out, open it in PowerPoint and play each clip once; the checker confirms media and poster are present but cannot play them.
- `clips.json` paths resolve against its folder, then its parent (the motion project root), then the working folder.

## Check and render

`check_deck.py` reads the mode from the deck (or `--mode`). It prints the spine (titles or statements in order) first: read it as the argument. ERRORs: missing or topic-style titles, titles over 95 characters, duplicate titles, data without source (consult), Illustrative labels missing on a sample-data deck, shapes off the slide. WARNINGs: overflow estimate, more than 5 bullets, text under 12 pt (consult) or 18 pt (keynote), more than 20 words or bullets on a keynote slide, number claims without fine print, image placeholders left, missing speaker notes, clips without poster frame or over 60 s / 50 MB (missing clip media is an ERROR), title overlapping the body, more than one font family.

`render.py` converts through LibreOffice. LibreOffice substitutes missing fonts, so judge layout, not exact typography. No LibreOffice: open the file in PowerPoint and look at every slide. Video slides render as their poster frame and are marked `VIDEO <beat>` on the contact sheet.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Title wraps to three lines | two messages in one title | split the slide, or move the clause after "because" into the body |
| Chart labels overlap | too many categories or long names | horizontal bars, shorter names, tail into "Other" |
| Waterfall bars float wrongly | sign error | deltas signed, totals absolute |
| Text box overflows | document prose on a slide | cut words; 12 pt is the floor |
| Body collides with template title | master title lower than 1.55 in | `y=body_top(s)` on the exhibit helpers |
| Logo covered | exhibit in a protected zone | shrink the exhibit; read protected zones in the design guide |
| Fonts differ across slides | mixed defaults | everything through deckkit; template font via `new_deck(template)` |
| Leader line points nowhere | chart internals have no fixed coordinates | render, measure, correct `target=` |
| check: missing source | exhibit without provenance | `source(s, ...)` citing the brief or dataset |

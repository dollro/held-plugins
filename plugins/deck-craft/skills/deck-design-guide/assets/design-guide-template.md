# Design guide: <brand or template name>

Source: <template file, brand book, reference deck> · Owner: <who decides> · Version: <date>

## Canvas
- Slide size: 13.333 x 7.5 in (16:9)
- Safe margin: 0.5 in
- Title zone (Title Only layout): x, y, w, h in
- Body starts at: y in · Body ends at: y in
- Source / footnote line: y in

## Colour roles
| Role | Hex | Theme slot | Use |
|---|---|---|---|
| ink | | dk1 | all text |
| bg | | lt1 | pages |
| accent | | accent1 | the one thing per slide, hero numbers |
| grey | | | context data, secondary text |
| light | | | rules, axis lines |
| pale | | | panels, table header |
| negative | | | only where sign is the message |
| chart order | | accent1, … | multi-series charts |

## Fonts and type scale
- Heading font: · Body font:
- Consult: action title __ pt (master) · body 12-16 pt · labels 9-11 pt
- Keynote: statements 40-96 pt · numbers 120-200 pt · secondary ≥ 18 pt
- Title style: sentence case / title case · numbers as digits

## Layout roles
| Role | Layout name | Notes |
|---|---|---|
| cover | | |
| title_only (consult content) | | |
| divider | | |
| blank (exhibits, keynote) | | |
| statement (keynote) | | |
| picture | | |
| closing | | |

## Protected zones (never cover or move)
- Logo: position
- Bands / lines:
- Footer, confidentiality line, page number:

## Keynote allowance
- Default stage: master / dark
- Accent or dark stage: allowed on __ slides max (STAR moments)
- Images: source, style

## Imagery and icons
- Photo style, allowed sources:
- Icon family, stroke, colour:

## Do / don't
- Do:
- Don't:

## Add-in short form (paste into Claude for PowerPoint → Settings → Instructions)
```
Template-first: use our master layouts and placeholders; never add fonts or colours.
Accent = <hex>, only for the one thing per slide. Titles: full-sentence action titles, 18-28 pt in the title placeholder.
Body 12-16 pt. Keep clear of <logo position> and <bands>. Every data slide has a source line.
Keynote slides: <layout>, template fonts, statements 40-96 pt, one number per slide, talk in the notes.
```

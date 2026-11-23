---
name: deck-design-guide
description: Captures and enforces presentation design standards. Turns a slide master (.pptx/.potx), an existing on-brand deck or a brand book into a reusable design guide (design-guide.md for people and the PowerPoint add-in, design-guide.json for deck-craft) - canvas, theme colours and their roles, fonts and type scale, layout roles, title and body zones, protected master artwork, keynote allowances, do and don't - and audits slides against it with explicit thresholds (grid, alignment, spacing, one accent, 60-30-10 colour, contrast, type sizes, icons, density). Use when someone shares a corporate template or brand guidelines, asks to set up or follow a design standard, CI or Corporate Design, "Masterfolie", "Design-Richtlinie", "make this comply with our template", or asks how a slide should look. Organisation-agnostic: one guide per brand or template.
license: MIT
---

# deck-design-guide

Two jobs: **capture** a design standard once, then **apply and audit** it on every deck. The guide is the single source of truth that deck-craft, deck-keynote and deck-review follow, in Claude Code and in the PowerPoint add-in.

## Job A: capture a design guide

Inputs, in order of authority: the brand book or CI rules the user provides > the slide master > a reference deck the user calls on-brand > the defaults in `references/design-rules.md`.

1. **Profile the master** (Python available):
   `python scripts/template_profile.py <template.pptx|.potx> design-guides/<brand>/ --sampler`
   It writes `design-guide.json`, `design-guide.md` and `layout-sampler.pptx` (one slide per layout, each placeholder labelled). It only reads the template.
   Without Python (add-in): open the slide master view and read layouts, placeholders, theme colours and fonts yourself; fill `assets/design-guide-template.md` by hand.
2. **Look at the sampler** (render it with deck-craft's `render.py`) and confirm the **layout roles**: cover, title_only (consult content), content, two_content, divider, blank, statement, picture, closing. Fix wrong guesses in the JSON `layouts` block.
3. **Fill the colour roles.** Theme slots are not roles. Decide with the brand material: ink (text), bg, accent (the one-thing colour, usually accent1), grey (context data), light (rules), pale (panels), negative (only where sign matters), chart order for multi-series. Check contrast (≥ 4.5:1 for text).
4. **Record protected zones**: logo, bands, footer, confidentiality line, page number. Nothing may cover or move them.
5. **Close the TODOs with the user**: tone and title style, imagery, icon family, legal lines, do and don't. Ask only what the template and brand book cannot answer.
6. **Set the keynote allowance** for this brand: default stage (master or dark), whether accent stages are allowed and how many, statement and number sizes within the brand fonts.
7. **Save** both files under `design-guides/<brand>/` (or where the user keeps them) and name the folder in the report. One guide per brand or template; never mix two brands in one guide.

## Job B: apply and audit

- **deck-craft (Python)**: `apply_design_guide(prs, "design-guides/<brand>/design-guide.json")` right after `new_deck(template)`. It sets colours, font and layout roles.
- **PowerPoint add-in**: upload this skill together with the brand's `design-guide.md` in `assets/`, or paste the short form (section "Add-in short form" of the guide) into the add-in's Instructions.
- **Audit** a slide or deck against the guide and `references/design-rules.md`: list each breach with the slide number, the rule, the measured value and the fix. Template breaches before craft breaches.

## Job C: export the brand lock for motion and HTML

Films (motion-craft) and HTML pages do not read a slide master. They read `brand-lock.md`: colours with roles (accent = hero), heading and body fonts with their font files, logo files, safe zones and the never-do list.

```bash
python scripts/export_brand_lock.py design-guides/<brand>/design-guide.json --template <master.pptx>
```

- Logo files come from `--logo`, `assets.logos` in the JSON, or are extracted from the master's pictures into `logos/`.
- HTML rendering needs the font files, not just the names. The script lists the files it finds and flags missing ones under **Open**; get licensed files from the brand owner rather than substituting.
- Without a master or Python, fill `assets/brand-lock-template.md` by hand (story-craft's stock-take runs a four-question brand interview for this).

## Template-first ladder (the rule every module follows)

1. Use the master's layout and its placeholders as they are.
2. Put exhibits inside the body zone, in theme fonts and colours.
3. Enhance only within the mode's allowance (see the guide's keynote section; consult: tracker, callout panel, one accent).
4. Never introduce fonts or colours, never move or cover master artwork, never re-style what the master styles.

When the brand book and the master disagree, the brand book wins and the conflict goes into the guide's notes.

## Files

- `scripts/template_profile.py`: master → design-guide.json + design-guide.md (+ layout sampler).
- `scripts/export_brand_lock.py`: design-guide.json → brand-lock.md for motion-craft and HTML work.
- `examples/make_acme_master.py`: builds a fictional master to try both scripts on.
- `references/design-rules.md`: the default craft rules with thresholds (grid, Gestalt grouping, alignment, spacing, type scale, colour, contrast, icons, density, imagery). A brand guide overrides any of them.
- `assets/design-guide-template.md`: the guide's structure, for filling by hand.
- `assets/brand-lock-template.md`: the brand lock's structure, for filling by hand.

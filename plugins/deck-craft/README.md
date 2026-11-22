# deck-craft

PowerPoint decks two ways, always inside your slide master when you have one:

- **consult**: steering committee, board, investment or recommendation decks. Pyramid storyline, action titles, one message per slide, native editable charts, sources, illustrative labels.
- **keynote**: product launches, vision talks, pitches on stage. Headline, sparkline arc, villain and hero, rule of three, one number per slide, slide-by-slide reveals, speaker notes as the script.

## Modules

| Skill | Job | Standalone? |
|---|---|---|
| `deck-craft` | Orchestrates and builds: mode, template-first rule, workflow, python-pptx kit, checker, renderer | yes (core rules inline) |
| `deck-storyline` | Governing thought, pyramid, SCQA, action-title chain, executive summary, ghost deck, scaffolds | yes |
| `deck-keynote` | Keynote slide form: maps story-craft beats to slide types when `narrative.md` exists, short inline arc rules otherwise; storyboard with a Beat column | yes (inline arc rules) |
| `deck-exhibits` | Exhibit selection, chart finishing, data-ink, callouts, frameworks, MECE layout | yes |
| `deck-design-guide` | Captures a master or brand book into a design guide (md + json); audits against it | yes |
| `deck-review` | Partner review, keynote review, template audit, flow audit, before/after redesign | yes |

The story itself (headline, villain, beats, evidence, cuts) lives in the separate plugin **story-craft**, which writes `narrative.md`. deck-keynote reads it when present; without it, deck-keynote keeps a short version of the arc rules, so deck-craft works standalone and in the PowerPoint add-in.

In Claude Code they are invoked as `/deck-craft:deck-craft`, `/deck-craft:deck-design-guide`, and so on, or picked up automatically from the request.

## Template-first

With a master, every module climbs the same ladder: use the master's layouts and placeholders as they are → put exhibits in the body zone in theme fonts and colours → enhance only within the mode's allowance → never add fonts or colours or touch master artwork. `deck-design-guide` profiles the master once (`template_profile.py`) into `design-guide.json`, which `deckkit.apply_design_guide()` loads, and `design-guide.md`, which people and the PowerPoint add-in read.

## Install (Claude Code)

```bash
claude plugin install deck-craft@held-plugins
```

Python side: `pip install python-pptx` (pulls in lxml); optionally LibreOffice, poppler (`pdftoppm`) and Pillow for rendering.

## Use in Claude for PowerPoint (add-in)

Skills enabled in your Claude account are available in the add-in. Upload each skill folder you want as a skill (zip the folder, e.g. `deck-craft/`, `deck-design-guide/`) in Claude settings. The add-in runs no Python: the skills switch to their add-in path (`deck-craft/references/powerpoint-addin.md`). Paste a brand's "Add-in short form" from its design guide into the add-in's Instructions for persistent brand rules.

## Quick test

```bash
cd "$(mktemp -d)"
python <plugin>/skills/deck-craft/examples/consult_example.py
python <plugin>/skills/deck-craft/examples/keynote_example.py            # black stage
python <plugin>/skills/deck-craft/examples/keynote_example.py brand.pptx # inside your master
python <plugin>/skills/deck-craft/scripts/check_deck.py consult_example.pptx
python <plugin>/skills/deck-craft/scripts/render.py keynote_example.pptx
python <plugin>/skills/deck-design-guide/scripts/template_profile.py brand.pptx design-guides/brand --sampler
```

## Sources and credits

Merged from two MIT skill packs (a python-pptx consulting-slides agent skill with deckkit and check_deck; a pack of 17 consulting slide-design method skills), extended with:
- Barbara Minto's Pyramid Principle and SCQA; Michael Alley's assertion-evidence research on sentence headlines with visual evidence.
- Carmine Gallo's analysis of Steve Jobs's keynotes (headline, rule of three, villain and hero, picture superiority, one number per slide); Apple keynote slide practice (very few words per slide, very large type).
- Nancy Duarte: Resonate (sparkline of what is / what could be, STAR moment) and Slidedocs (read-ahead documents built in slide software).
- Ideas from open skills: Power Design (numeric slide thresholds, MIT), new-presentation (three-act proportions, billboard test), presentation-writing (presentation-type scaffolds, spoken speaker notes, MIT).
- Claude for PowerPoint documentation (templates, skills in the add-in, persistent instructions).

License: MIT (see `LICENSE`).

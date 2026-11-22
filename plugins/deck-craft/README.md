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
| `deck-design-guide` | Captures a master or brand book into a design guide (md + json); audits against it; exports `brand-lock.md` for films and HTML | yes |
| `deck-review` | Partner review, keynote review, template audit, flow audit, before/after redesign | yes |

The story itself (headline, villain, beats, evidence, cuts) lives in the separate plugin **story-craft**, which writes `narrative.md`. deck-keynote reads it when present; without it, deck-keynote keeps a short version of the arc rules, so deck-craft works standalone and in the PowerPoint add-in.

In Claude Code they are invoked as `/deck-craft:deck-craft`, `/deck-craft:deck-design-guide`, and so on, or picked up automatically from the request.

## Template-first

With a master, every module climbs the same ladder: use the master's layouts and placeholders as they are → put exhibits in the body zone in theme fonts and colours → enhance only within the mode's allowance → never add fonts or colours or touch master artwork. `deck-design-guide` profiles the master once (`template_profile.py`) into `design-guide.json`, which `deckkit.apply_design_guide()` loads, and `design-guide.md`, which people and the PowerPoint add-in read.

## How the three fit together

story-craft decides **what the story is**; deck-craft and motion-craft decide **what it becomes**. They share one contract, `narrative.md`, with numbered beats (`B01..Bn`) and named cuts, and one brand source, the design guide.

```
prfaq-vision-builder (optional: prfaq.md)
            │
            ▼
STORY-CRAFT   stock-take ─► intake.md
              narrative  ─► narrative.md   (beats B01..Bn, cuts keynote / film-60 / teaser-20)
              story-review ─► verdict PASS / REVISE in narrative.md
            │
            │   brand: design-guide.json ─► brand-lock.md  (deck-craft:deck-design-guide)
   ┌────────┴──────────────────────────┐
   ▼                                   ▼
DECK-CRAFT                          MOTION-CRAFT
deck-keynote: beat → slide type     motion-director: direction → look → STORYBOARD.md per cut
deck-craft: build / check / render    → motion spec → animated test → build (HyperFrames)
  video_slide(beat) ◄──────────────  motion-qa: render checks, fresh read,
                     clips.json        export renders/beats/Bxx.mp4 + clips.json
                                    shot-forge: character sheets, prompts, generation via
                                      a connected MCP, critic, take log, budget
```

| Step | Skill | Reads | Writes |
|-|-|-|-|
| 1 | story-craft:stock-take | prfaq.md, source docs | `intake.md` |
| 2 | story-craft:narrative | `intake.md` | `narrative.md` |
| 3 | story-craft:story-review | `narrative.md`, `intake.md` | `## Review` (PASS / REVISE) |
| 4 | deck-craft:deck-design-guide | slide master | `design-guide.json`, `brand-lock.md` |
| 5a | deck-craft:deck-keynote → deck-craft | `narrative.md` (cut keynote), `clips.json` | `storyboard.md`, `.pptx` |
| 5b | motion-craft:motion-director | `narrative.md` (film cuts), `brand-lock.md` | `<cut>/STORYBOARD.md`, motion spec, build |
| 5c | motion-craft:shot-forge | frames with `medium: generated` | `shots/shots.json`, takes, clips |
| 6 | motion-craft:motion-qa | renders, `narrative.md` | `renders/beats/*`, `clips.json` |
| 7 | deck-craft (again) | `clips.json` | video slides on the matching beats |

Each plugin works alone: deck-craft keeps short inline story rules (and runs in the PowerPoint add-in), motion-craft needs a reviewed `narrative.md` but nothing else from deck-craft except an optional brand lock.

The worked example for the dummy product `atlas` (fictional company Acme) runs the whole chain: `story-craft/examples/atlas/` (intake, narrative, keynote storyboard), `motion-craft/examples/atlas/` (brand lock, film-60 storyboard, motion spec, shots), `deck-craft/skills/deck-craft/examples/atlas_keynote.py` (the deck, with the B02 and B12 clips).

## Install (Claude Code)

```bash
claude plugin install deck-craft@held-plugins
```

Python side: `pip install python-pptx` (pulls in lxml); optionally LibreOffice, poppler (`pdftoppm`) and Pillow for rendering.

## Use in Claude for PowerPoint (add-in)

Skills enabled in your Claude account are available in the add-in. Upload each skill folder you want as a skill (zip the folder, e.g. `deck-craft/`, `deck-design-guide/`) in Claude settings. The add-in runs no Python: the skills switch to their add-in path (`deck-craft/references/powerpoint-addin.md`). Paste a brand's "Add-in short form" from its design guide into the add-in's Instructions for persistent brand rules.

## Quick test

`<plugin>` stands for the plugin's folder (in this repository `plugins/<name>`, or the installed plugin's path). The atlas walkthrough in `plugins/story-craft/examples/atlas/README.md` spells out every path.

```bash
cd "$(mktemp -d)"
python <plugin>/skills/deck-craft/examples/consult_example.py
python <plugin>/skills/deck-craft/examples/keynote_example.py            # black stage
python <plugin>/skills/deck-craft/examples/keynote_example.py brand.pptx # inside your master
python <plugin>/skills/deck-craft/examples/atlas_keynote.py <motion-project>/renders/clips.json  # video slides
python <plugin>/skills/deck-craft/scripts/check_deck.py consult_example.pptx
python <plugin>/skills/deck-craft/scripts/render.py keynote_example.pptx
python <plugin>/skills/deck-design-guide/scripts/template_profile.py brand.pptx design-guides/brand --sampler
python <plugin>/skills/deck-design-guide/scripts/export_brand_lock.py design-guides/brand/design-guide.json --template brand.pptx  # brand-lock.md for motion-craft
```

## Sources and credits

Merged from two MIT skill packs (a python-pptx consulting-slides agent skill with deckkit and check_deck; a pack of 17 consulting slide-design method skills), extended with:
- Barbara Minto's Pyramid Principle and SCQA; Michael Alley's assertion-evidence research on sentence headlines with visual evidence.
- Carmine Gallo's analysis of Steve Jobs's keynotes (headline, rule of three, villain and hero, picture superiority, one number per slide); Apple keynote slide practice (very few words per slide, very large type).
- Nancy Duarte: Resonate (sparkline of what is / what could be, STAR moment) and Slidedocs (read-ahead documents built in slide software).
- Ideas from open skills: Power Design (numeric slide thresholds, MIT), new-presentation (three-act proportions, billboard test), presentation-writing (presentation-type scaffolds, spoken speaker notes, MIT).
- Claude for PowerPoint documentation (templates, skills in the add-in, persistent instructions).

License: MIT (see `LICENSE`).

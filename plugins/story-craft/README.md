# story-craft

The story before any slide or frame. story-craft settles what a launch, keynote or product film must achieve and what it can stand on, before any medium is chosen. Its files are read by deck-craft (keynote decks) and motion-craft (films).

## Modules

| Skill | Job | Output |
|---|---|---|
| `stock-take` | Interview + inventory: purpose (belief before → after), ask, audience, outputs with channel and runtime, evidence tagged solid / likely / missing, assets, constraints | `intake.md` |
| `narrative` | Medium-neutral dramaturgy: headline, villain, cost, promise, three storylines then one, sparkline, reveal, rule of three, proof per claim, STAR moment, close; numbered beats `B01..Bn` with roles and evidence IDs; cuts per output | `narrative.md` |
| `story-review` | Gate before any medium: validator, one-sentence test, so-what per beat, credibility against the evidence, four-seat expert panel with scorecard; PASS / REVISE appended to `narrative.md` | review in `narrative.md` |

### Validator

`<plugin>` stands for the plugin's folder (in this repository `plugins/<name>`, or the installed plugin's path). The atlas walkthrough in `plugins/story-craft/examples/atlas/README.md` spells out every path.

```bash
pip install pyyaml        # the full atlas chain also needs python-pptx and pillow (deck-craft)
python <plugin>/scripts/validate_narrative.py examples/atlas/narrative.md   # intake.md next to it
python <plugin>/scripts/test_validate_narrative.py                         # example passes, mutations fail
```

Each finding prints as `beat · problem → fix`; exit 1 on any error.

In Claude Code the skills are invoked as `/story-craft:stock-take`, `/story-craft:narrative` and `/story-craft:story-review`, or picked up from the request.

An end-to-end example for the dummy product `atlas` is in `examples/atlas/`; its `README.md` runs the whole chain across the three plugins.

## Decisions

- **Separate plugin.** story-craft, deck-craft and motion-craft are three plugins. deck-craft keeps working without story-craft installed and in the PowerPoint add-in.
- **One language per narrative.** A story is written in one language; another language is a separate cut or a translated file.
- **Evidence is tagged, never upgraded.** `missing` evidence cannot carry a claim downstream.

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
claude plugin install story-craft@held-plugins
```

## Sources and credits

- Interview pattern (one question at a time, sources before questions, import of a PR/FAQ) adapted from prfaq-vision-builder in this marketplace and Amazon's Working Backwards method.
- Nancy Duarte, Resonate (audience belief before and after, the sparkline of what is and what could be, the STAR moment).
- Carmine Gallo's analyses of product-launch keynotes (headline, villain and hero, rule of three, meaningful numbers); the launch dramaturgy was moved here from deck-craft:deck-keynote.
- "Three storylines, then one", hook rules and the tells of a generic film adapted from the story reference of HyperFrames (heygen-com/hyperframes, Apache-2.0).
- Panel review with role lenses and a scorecard: idea from remotion-video-director (bayramannakov/remotion-video-director), rewritten; no text taken.
- One-sentence and so-what tests reused from deck-craft:deck-storyline.
- Cutdown rules ("drop beats from the middle, never the hook or the payoff") adapted from video-director (SallyRS/video-director, MIT).

License: MIT (see `LICENSE`).

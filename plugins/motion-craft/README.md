# motion-craft

Launch films from the same story as the keynote. motion-craft reads story-craft's reviewed `narrative.md` and a `brand-lock.md`, directs each film cut (film-60, teaser-20) beat by beat, builds it in HyperFrames, and exports one clip per beat so deck-craft can play the film's moments on the matching slides.

## Modules

| Skill | Job | Output |
|-|-|-|
| `motion-director` | Gate on a PASS narrative; pick the cut and a style; 2-3 direction options as stills; look decisions; `STORYBOARD.md` with one frame per beat and a medium per role; motion spec; animated test; full build via HyperFrames; polish | `<cut>/STORYBOARD.md`, `motion-spec.md`, `direction.md`, renders |
| `shot-forge` | Generated footage for frames with `medium: generated`: character and continuity sheets, budget estimate and approval, one prompt per shot (no UI, text or logos in generated shots), generation via whichever video MCP is connected, critic loop with a take cap, take log | `shots/shots.json`, `shots/takes.md`, clips |
| `motion-qa` | Review by a fresh reviewer, not the builder: render checks (codec, size, fps, black and frozen frames, loudness, true peak), text reading time, continuity, end card, delivery per cut; fresh read of every beat against `narrative.md`; then the beat export for the deck | findings per beat, `renders/beats/Bxx.mp4` + `.jpg`, `renders/clips.json` |

In Claude Code the skills are invoked as `/motion-craft:motion-director` and so on, or picked up from the request.

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

## Dependencies

- **story-craft** (this marketplace): `narrative.md` with `Verdict: PASS` in its Review. motion-craft does not shape stories.
- **HyperFrames** plugin (build backend, Apache-2.0): install it as its own plugin and keep it current with `npx hyperframes skills update`. motion-director hands it `STORYBOARD.md` (format-compatible) and the assets; it is never vendored here. Needs Node 22+ and Chrome.
- **ffmpeg** and ffprobe for checks and the beat export.
- Python 3.9+ with PyYAML for the checkers.
- For generated footage: a connected video-generation MCP (any provider). Without one, shot-forge stops after the shot specs and budget; it never fakes clips.
- Brand: `brand-lock.md` from deck-craft:deck-design-guide (`export_brand_lock.py`), or filled by hand from its template. HTML rendering needs the font files.

Without HyperFrames, motion-director stops after the storyboard and motion spec (a dry run) and says what is missing.

## Project layout

```
motion/                       next to narrative.md and intake.md
  brand-lock.md
  <cut>/                      one HyperFrames project per cut: STORYBOARD.md, SCRIPT.md, motion-spec.md, direction.md, build
  shots/                      shots.json, takes.md, characters/
  renders/<cut>.mp4           full film per cut
  renders/beats/<beat>.mp4    one clip per beat (+ .jpg poster)
  renders/clips.json          clip manifest for deck-craft:video_slide_from_clips
```

## Quick test

`<plugin>` stands for the plugin's folder (in this repository `plugins/<name>`, or the installed plugin's path). The atlas walkthrough in `plugins/story-craft/examples/atlas/README.md` spells out every path.

Run from the plugin folder (`examples/...` paths are relative to it); `<deck-craft>` is the deck-craft plugin folder.

```bash
pip install pyyaml
python <plugin>/skills/motion-director/scripts/check_storyboard.py examples/atlas/film-60/STORYBOARD.md
python <plugin>/scripts/validate_shots.py examples/atlas/shots/shots.json --storyboard examples/atlas/film-60/STORYBOARD.md
# no HyperFrames render at hand: a labelled test-fixture film stands in for it
python <plugin>/skills/motion-qa/scripts/make_test_film.py examples/atlas --cut film-60 --size 1920x1080
python <plugin>/skills/motion-qa/scripts/render_checks.py examples/atlas/renders/film-60.mp4 --storyboard examples/atlas/film-60/STORYBOARD.md
python <plugin>/skills/motion-qa/scripts/export_beats.py examples/atlas --cut film-60     # renders/beats/*, renders/clips.json
python <deck-craft>/skills/deck-craft/examples/atlas_keynote.py examples/atlas/renders/clips.json   # deck plays B02 and B12
```

## Install (Claude Code)

```bash
claude plugin install motion-craft@held-plugins
```

## Sources and credits

- motion-director adapts the staged workflow, options rounds, motion spec and text-treatment ideas of video-director by Sally Slater (github.com/SallyRS/video-director, MIT), rewritten and condensed.
- shot-forge adapts ideas from Shotkit by WhyStrohm (github.com/whystrohm/shotkit, Apache-2.0; notice in `NOTICE`): the critique schema (reworked for video takes with per-criterion scores and a change-approach verdict), the critique rubric and the shot validator (rewritten as `validate_shots.py` with a no-UI word list and a storyboard cross-check). It also draws on video-director's guide to generated clips (MIT) and on Claude-AI-Video-Producer-Plugin by Daniel Rosehill (github.com/danielrosehill/Claude-AI-Video-Producer-Plugin, MIT): character definition, take log, budget estimate, model recommendation. All text rewritten.
- motion-qa adapts ideas from video-director (MIT): render check, fresh read, continuity sheets, sound balance, retiming, cutdowns. Its delivery and review checks follow the review role of HyperFrames (Apache-2.0); no HyperFrames files are copied. All text rewritten.
- `STORYBOARD.md` is format-compatible with HyperFrames (github.com/heygen-com/hyperframes, Apache-2.0), the build backend, used as a separate plugin and never vendored. Launch-film craft (real UI, the end card, tells of a generated film) is informed by its public guidance, restated in our own words.

License: MIT (see `LICENSE`); third-party notices in `NOTICE`.

# motion-craft

Launch films from the same story as the keynote. motion-craft reads story-craft's reviewed `narrative.md` and a `brand-lock.md`, directs each film cut (film-60, teaser-20) beat by beat, builds it in HyperFrames, and exports one clip per beat so deck-craft can play the film's moments on the matching slides.

## Modules

| Skill | Job | Output |
|-|-|-|
| `motion-director` | Gate on a PASS narrative; pick the cut and a style; 2-3 direction options as stills; look decisions; `STORYBOARD.md` with one frame per beat and a medium per role; motion spec; animated test; full build via HyperFrames; polish | `<cut>/STORYBOARD.md`, `motion-spec.md`, `direction.md`, renders |
| `shot-forge` | Generated footage for frames with `medium: generated`: character and continuity sheets, budget estimate and approval, one prompt per shot (no UI, text or logos in generated shots), generation via whichever video MCP is connected, critic loop with a take cap, take log | `shots/shots.json`, `shots/takes.md`, clips |

In Claude Code the skills are invoked as `/motion-craft:motion-director` and so on, or picked up from the request.

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

```bash
pip install pyyaml
python <plugin>/skills/motion-director/scripts/check_storyboard.py examples/atlas/film-60/STORYBOARD.md
python <plugin>/scripts/validate_shots.py examples/atlas/shots/shots.json --storyboard examples/atlas/film-60/STORYBOARD.md
```

## Install (Claude Code)

```bash
claude plugin install motion-craft@held-plugins
```

## Sources and credits

- motion-director adapts the staged workflow, options rounds, motion spec and text-treatment ideas of video-director by Sally Slater (github.com/SallyRS/video-director, MIT), rewritten and condensed.
- shot-forge adapts ideas from Shotkit by WhyStrohm (github.com/whystrohm/shotkit, Apache-2.0; notice in `NOTICE`): the critique schema (reworked for video takes with per-criterion scores and a change-approach verdict), the critique rubric and the shot validator (rewritten as `validate_shots.py` with a no-UI word list and a storyboard cross-check). It also draws on video-director's guide to generated clips (MIT) and on Claude-AI-Video-Producer-Plugin by Daniel Rosehill (github.com/danielrosehill/Claude-AI-Video-Producer-Plugin, MIT): character definition, take log, budget estimate, model recommendation. All text rewritten.
- `STORYBOARD.md` is format-compatible with HyperFrames (github.com/heygen-com/hyperframes, Apache-2.0), the build backend, used as a separate plugin and never vendored. Launch-film craft (real UI, the end card, tells of a generated film) is informed by its public guidance, restated in our own words.

License: MIT (see `LICENSE`); third-party notices in `NOTICE`.

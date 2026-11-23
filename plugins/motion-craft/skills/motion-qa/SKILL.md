---
name: motion-qa
description: Checks a rendered launch film before anyone sees it and exports one clip per beat for the deck. A reviewer who did not build the film (a fresh subagent if needed) runs the required checks - cut frames, motion smoothness, text size and reading time, sound levels, continuity across generated shots, end card, delivery specs per cut - then watches the render cold against narrative.md and reports findings per beat ID. Then export_beats.py cuts renders/<cut>.mp4 into renders/beats/<beat>.mp4 with posters and writes renders/clips.json for deck-craft. Use for "check the render", "QA the video", "is the film ready", "review the cut", "export clips for the deck", "Clips für die Präsentation", "Video prüfen". Not for direction, storyboard or motion spec (motion-craft:motion-director), not for generating footage or takes (motion-craft:shot-forge), not for reviewing the slides that play the clips (deck-craft:deck-review).
license: MIT
---

# motion-qa

The builder knows what each moment was meant to show, so the builder forgives the render. The viewer sees it once, at full speed, often on a phone, often muted. This skill is the viewer's side: measured checks, a cold watch against the story, findings per beat, then clips for the deck.

Inputs: `motion/renders/<cut>.mp4`, `motion/<cut>/STORYBOARD.md`, `narrative.md` (story-craft), `brand-lock.md`; for generated shots also `motion/shots/shots.json` and `shots/characters/`.
Outputs: findings per beat (in the reply, and in `<cut>/direction.md` under `## QA <date>`), `renders/beats/<beat>.mp4` + `.jpg`, `renders/clips.json`.

## 0. Who checks

- **Not the builder.** The agent or person who built the cut does not sign it off. In Claude Code, start a fresh subagent with only: the render, `STORYBOARD.md`, `narrative.md`, `brand-lock.md`, this skill and `references/checks.md`. No build log, no motion spec, no chat history.
- The builder fixes; the reviewer re-checks only what changed. Repeat until no P0 is open.
- Say what was measured, what was only looked at, and what nobody checked (sound is measured, not heard).

## 1. Measure

```bash
python3 <skill>/scripts/render_checks.py motion/renders/film-60.mp4 --storyboard motion/film-60/STORYBOARD.md --loudness web
```

Reports codec, size, fps, pixel format, faststart, duration against the storyboard (±10 %), black stretches, frozen stretches over 2 s (the end-card hold is allowed), integrated loudness and true peak against the target, and scene cuts against frame boundaries. Exit 0 = clean, 1 = error, 2 = needs a human look. A clean run is never proof: it does not see text, continuity or meaning.

Pull frames to look at: one per second for a contact sheet, and 8-10 fps strips ±0.2 s around every cut.

```bash
ffmpeg -v error -i film-60.mp4 -vf fps=1,scale=480:-2,tile=6x10 qa/contact.png
ffmpeg -v error -ss <t-0.3> -t 0.6 -i film-60.mp4 -vf fps=10,scale=480:-2,tile=6x1 qa/cut-<t>.png
```

## 2. Required checks

All seven, on every render that goes to an owner. Thresholds and how to measure: `references/checks.md`.

| Check | Pass when |
|---|---|
| Cut frames | No jump, pop, doubled element, flash or half-built frame in the strip around any cut; frame 0 is finished |
| Motion smoothness | Moves ease in and out; no stepping, no flicker; holds are still; no stretch over ~0.6 s where nothing moves, except a deliberate hold |
| Text size and reading time | Text ≥ 26 px at 1080p (scale for other sizes), readable at phone width; on screen ≥ 0.3 s per word + 0.5 s; the last line of a beat ≥ 2 s; inside the title-safe area |
| Sound levels | Integrated −14 LUFS for web music-led (−16 LUFS for VO-led), ±1 LU; true peak ≤ −1 dBTP; voice clear above music; effects land on the frame they belong to |
| Continuity (generated shots) | Faces, clothes, props and states (door, screen, weather, light) match across shots of the same person or place; hands and objects behave physically |
| End card | The mark lands once (no second bounce or re-reveal); CTA held 1.5-3 s, still and readable; sound resolves under it |
| Delivery specs per cut | Codec, size, fps, aspect, safe zones, loudness as in the cut's row; teasers work muted (autoplay without sound still tells the story) |

## 3. Fresh read

The reviewer watches the render once, start to end, at full speed, without pausing, before reading any frame. Then, with `narrative.md` open:

1. For each beat of the cut, write the statement the film actually made, in one line, as a stranger would say it.
2. Compare with the beat's `statement`. **Lands** (same meaning), **soft** (right idea, weak or late), **missing** (not on screen or not understood).
3. Watch once muted. Can a first-time viewer say what this is and what to do next?
4. Name the three worst moments with timestamps, whatever the checks said.

## 4. Findings

One line per problem, grouped by beat ID in film order, `–` for the whole film:

`B03 · t=9.4 s · "6.5 hours" on screen 1.1 s, needs 1.7 s → hold the number 0.6 s longer, trim B02's tail · keep the count-up`

- **P0** breaks the read or the delivery: unreadable, wrong, beat missing, true peak over, wrong size or codec.
- **P1** weakens it: soft beat, dead stretch, jump at a cut, loudness off target.
- **P2** polish.

Fix every P0 and the P1s worth the time; text first, then timing, then detail. Retime through the storyboard (`start`, `duration`), never by nudging single moves, and run the checks again. A fix that changes a beat statement goes back to `narrative.md`, keeping beat IDs. No scores out of 10.

## 5. Export beats for the deck

When the deck cut has no open P0:

```bash
python3 <skill>/scripts/export_beats.py motion --cut film-60 [--beats B02,B12]
```

- Reads frames from `film-60/STORYBOARD.md` (beat, `start`, `duration`; missing `start` = sum of earlier durations) and cuts each frame's window from `renders/film-60.mp4`, frame-accurate, re-encoded (H.264 veryfast, yuv420p, AAC if the film has sound, +faststart).
- Writes `renders/beats/<beat>.mp4` and a poster `<beat>.jpg`: the first stable, non-black frame from ~0.3 s in (fallback: middle frame). Open every poster: it is what the slide shows before play.
- Merges `renders/clips.json` (same beat + cut replaced, others kept, sorted by cut then beat; paths relative to `motion/`). `audio` = `none` when the film has no sound, else frontmatter `audio:` of the storyboard (`music` by default). `loopable` is false.
- Errors (exit 1): a beat not in the storyboard, a film shorter than the storyboard's last frame, missing film or ffmpeg.
- One clip folder per motion project: export the deck cut only, or pass `--out renders/beats-<cut>` for a second cut.

deck-craft plays the clips with `video_slide_from_clips()`; deck-craft:deck-keynote offers a `video` slide for every beat in `clips.json`.

No real render yet? `scripts/make_test_film.py motion --cut film-60` builds a labelled **test fixture** (coloured segment per frame, beat and statement as text, sine tone) so export and checks can be tried end to end. Never ship it or put it in a deck.

## Scripts

| Script | Does |
|---|---|
| `scripts/render_checks.py` | measures a render: format, duration, black, freeze, loudness, cuts vs frames |
| `scripts/export_beats.py` | cuts beat clips + posters, merges `renders/clips.json` |
| `scripts/make_test_film.py` | synthetic test fixture film from a STORYBOARD.md |
| `scripts/test_export_beats.py` | unit tests (`python3 test_export_beats.py`) |

Stdlib Python; ffmpeg and ffprobe on PATH (or `--ffmpeg`).

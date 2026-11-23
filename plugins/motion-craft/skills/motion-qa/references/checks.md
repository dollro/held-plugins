# Checks: thresholds and how to measure

Read with `SKILL.md` §2. Each check says what to pull, what passes, and the usual fix. Numbers are starting points; a brief or brand-lock that sets its own wins.

## Contents

- Cut frames
- Motion smoothness
- Text size and reading time
- Sound levels
- Continuity across generated shots
- End card
- Delivery specs per cut
- Fresh-read prompt
- render_checks.py findings

## Cut frames

Pull a strip around every cut: `render_checks.py` lists detected cuts; the storyboard's frame starts are the planned ones.

```bash
ffmpeg -v error -ss <t-0.2> -t 0.4 -i film.mp4 -vf fps=15,scale=640:-2,tile=6x1 qa/cut-<t>.png
```

| Look for | Usual fix |
|---|---|
| Subject jumps position or size across the cut | match the frame: end and start on the same position, or cut on the action |
| Element pops on or off in one frame | fade or move it, or hide it behind a cover first |
| Two layers half-faded over each other (white flash, text over text) | let one finish before the other starts, or move instead of fade |
| Brightness jump (dark footage to white UI) | shared ground, or dip through the brand background |
| Cut lands frames off the storyboard boundary | retime the frame `start` / `duration`, not the single move |
| Frame 0 blank or half-built | first frame is a finished composition |

## Motion smoothness

Pull 8-10 fps strips over the hero move and the payoff of each beat.

- Moves ease in and out; no linear moves on text or UI; no bounce on text.
- No stepping: a slow drift that moves a pixel every few frames reads as judder. Move faster or hold still.
- No flicker: a region that changes and changes back on the next frame.
- Holds are still. Nothing floats during a hold.
- No stretch over ~0.6 s where nothing moves, except a deliberate hold (≥ 1 s, on purpose) or the end card. `render_checks.py` flags frozen stretches over 2 s.
- Not everything moves at once on the same curve: one lead move, the rest follow.

## Text size and reading time

| Rule | Number |
|---|---|
| Minimum text height at 1080p | 26 px (scale: 720p → 18 px, 2160p → 52 px; vertical 1080×1920 → same 26 px) |
| Time on screen, fully visible | ≥ 0.3 s per word + 0.5 s |
| Last line of a beat | ≥ 2 s |
| Typing or word-by-word reveal | finishes in ≤ 2 s; reading time counts from the last word |
| Position | inside title-safe (90 % of the frame); for social cuts also clear of platform UI |

Worked example: "47 photos. 3 voice memos. Zero report." = 7 words → 0.3 × 7 + 0.5 = 2.6 s fully visible. A number like "6.5 hours a week" counts its digits as one word.

Check at phone width: scale the contact sheet to 360 px wide; every line meant to be read must still be readable. One capitalization rule for every on-screen line.

## Sound levels

```bash
ffmpeg -i film.mp4 -vn -af ebur128=peak=true -f null -      # integrated LUFS, true peak
ffmpeg -i film.mp4 -af silencedetect=n=-40dB:d=0.4 -f null -  # where the silences fall
```

| Mix | Integrated | True peak |
|---|---|---|
| Web, music-led | −14 LUFS ±1 | ≤ −1 dBTP |
| VO-led (explainer, keynote clip with voice) | −16 LUFS ±1 | ≤ −1 dBTP |
| Deck clips | as exported from the film; the deck sets playback volume | ≤ −1 dBTP |

- Voice sits clearly above the music: duck the music 6-10 dB under the voice.
- Effects land on the frame of the thing they belong to; no effect on text appearing.
- Measure stems (music, voice, effects) when a sound must be heard (a click, a ding): compare its momentary loudness with the music around it. Short clicks measure lower than they sound; report the number and ask.
- Nobody here hears the mix. Write "measured, not heard" in the findings; the owner's ears decide.
- Fix loudness on the final mix: `loudnorm=I=-14:TP=-1.5:LRA=11` (two-pass for accuracy).

## Continuity across generated shots

Required when the film has generated shots of a recurring person, place or prop (`shots/shots.json`, `shots/characters/`). Not needed for a film made only of motion graphics and UI; say so.

1. From the character and continuity sheets and each shot's `continuity` list, name every recurring item: face, hair, clothes, props, and the state of doors, screens, weather and light.
2. Pull one frame per shot where the item is visible; put them side by side (`ffmpeg -ss <t> -i film.mp4 -frames:v 1 qa/cont-<item>-<shot>.png`, then tile).
3. One line per item: `same:` (what was compared), `changed:` (which shot; remake or cut it before the owner sees it) or `accepted:` (owner's words and date).
4. Inside each shot: faces keep identity, hands do not warp, framing does not drift, nothing moves by itself (a door opening with no hand on it).

Generated shots carry no UI, screens, text or logos; if one shows, that is a P0 (screens are composited later).

## End card

- The mark lands once: one move in, then still. No second bounce, no re-reveal, no loop.
- CTA (the narrative's `ask`) held still and fully readable for 1.5-3 s, then the film ends; no black tail over 1 s.
- Logo and colours from `brand-lock.md`; logo inside the safe margin; nothing else competes on the card.
- Sound resolves under the card (music ending or a held tone), not cut mid-phrase.

## Delivery specs per cut

| Cut | Size, aspect | fps | Codec | Audio | Notes |
|---|---|---|---|---|---|
| film-60 (web, events) | 1920×1080, 16:9 | 25 or 30 | H.264 High, yuv420p, +faststart, ~10-16 Mbit/s | AAC 48 kHz stereo, −14 LUFS (−16 VO-led) | title-safe 90 %; captions as `.srt` beside the file when VO-led |
| teaser-20 (social feed) | 1080×1920 (9:16) or 1080×1350 (4:5) | 25 or 30 | H.264 High, yuv420p, +faststart | AAC, −14 LUFS | must work muted: autoplay without sound still tells the story; burned-in captions; keep top 14 % and bottom 20 % clear of platform UI |
| deck clips (renders/beats) | the film's size | the film's | H.264, yuv420p, +faststart, re-encoded veryfast | AAC or none | ≤ 60 s each, poster frame, never autoplays with sound in the deck |
| phone review copy | 1280×720 or 720×1280 | same | H.264, CRF 26 | AAC 128k | under 30 MB for sending round |

A different aspect ratio is a rebuild of each frame in the new format, not a crop or letterbox. A shorter cut drops beats (from `narrative.md` cuts), never the hook or the close.

## Fresh-read prompt

For the fresh subagent, after it has watched the render once:

> You have not seen how this film was built. Here are the render (or its contact sheet and cut strips), `STORYBOARD.md` and `narrative.md`. For each beat ID in the cut, write in one line what the film says at that moment, as a stranger would put it, then mark it lands / soft / missing against the beat's statement. Then list the three worst moments with timestamps, one line each: `beat · t=… · problem → exact change`. Do not suggest new ideas; report what is on screen.

## render_checks.py findings

| Finding | Meaning | Usual fix |
|---|---|---|
| pixel format not yuv420p | will not play in browsers, slides or phones | re-encode `-pix_fmt yuv420p` |
| size differs from storyboard `format` | wrong render preset | render at the storyboard format |
| no faststart | file must load fully before playing | re-mux `-movflags +faststart` |
| duration off by more than 10 % | film drifted from the plan | retime or update the storyboard |
| frame 0 black / black stretch | blank opening, or a dip that is too long | open on a finished frame; shorten the dip |
| nothing moves for over 2 s | dead stretch | slow move, or cut sooner; the end-card hold is allowed |
| cut frames off a frame boundary | edit and storyboard disagree | retime one of them; beat clips cut on the storyboard |
| loudness off target / true peak over | mix level | loudnorm on the final mix; true-peak limiter |

Scene detection misses cuts between frames of similar brightness and finds cuts inside generated shots; treat cut findings as places to look, not verdicts.

---
format: 1920x1080
duration: "<runtime of the cut, e.g. 60s>"
message: "<narrative headline, verbatim>"
arc: "<beats in one line: pile → cost → what if → name → demo → close>"
audience: "<who watches, where, muted or not>"
cut: <cut name from narrative.md, e.g. film-60>
narrative: <relative path to narrative.md>
brand_lock: <relative path to brand-lock.md, usually ../brand-lock.md>
style: "<style(s) from styles.md>"
voiceover: <none | optional | VO-led>
---

# <cut> · <product> · storyboard

Direction: **"<picked direction>"** (direction.md). One frame per beat of the cut, in cut order. `status: outline` until the frame's still is posed.

<!-- Copy this block once per beat of the cut. Keys: HyperFrames (status, duration,
transition_in, scene, voiceover, poster, reads, sound, src) + motion-craft (beat, medium,
start, statement). medium: motion | generated | ui | mixed, chosen by the role rule in
references/launch-rules.md. Check: python scripts/check_storyboard.py STORYBOARD.md -->

## Frame 1 — <title>

- beat: <B02>
- medium: <motion | generated | ui | mixed>
- start: 0.0s
- duration: <6s>
- status: outline
- statement: "<beat statement, verbatim or shortened>"
- scene: <one line: what is on screen>
- transition_in: <cut | carry | colour flood | zoom through | …>
- voiceover: "<beat line, shortened>" or none
- reads: <what the viewer reads, in order, each with its window: "…" (0.4-1.6s); "…" (1.6-3.0s)>
- sound: <bed, effects on visible actions, or silence>
- poster: <seconds into the frame for the still, past the intro move>

<What is on screen, what is real (recording, file) and what is a placeholder, the fine print
from the proof ledger, what carries over to the next frame, shot-forge shot IDs.>

## Frame 2 — <title>

- beat: <B03>
- medium: <motion>
- start: <previous start + previous duration>
- duration: <6s>
- status: outline
- statement: "<…>"
- scene: <…>
- transition_in: <…>
- voiceover: <…>
- reads: <…>
- sound: <…>
- poster: <…>

<…>

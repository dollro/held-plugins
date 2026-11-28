---
name: motion-director
description: Directs launch films and product films from a reviewed story-craft narrative.md - picks the cut (film-60, teaser-20), a premium style, 2-3 direction options as stills of the same beat, look decisions, a STORYBOARD.md with one frame per beat and a medium per beat role, a motion spec that names each move with its timing and easing, a 20-30 s animated test, then the full build through the hyperframes plugin and polish rounds, with a gate at every step. Brand comes from brand-lock.md. Use for "make the launch video", "motion graphics for the launch", "product film", "film-60", "teaser", "storyboard the film", "Launch-Video", "Erklärfilm", "Produktfilm", or after story-review passes. Not for generated shots and their prompts (shot-forge), not for checking renders or exporting clips per beat (motion-qa), not for the story itself (story-craft:narrative), not for slides (deck-craft).
license: MIT
---

# motion-director

The story is decided; this skill decides how it moves. It reads `narrative.md`, takes one cut, and turns each beat of that cut into one frame of a film. The user directs: every visual decision is a pick between 2-3 real options, and nothing animates before the stills are approved.

The failure this skill prevents is a film that feels like slides: one layout after another, everything fading up at once, the same blur at every seam, a logo in the corner.

## 0. Gate: what must exist

Check before anything else and stop if one fails.

| Needs | Check | If missing |
|---|---|---|
| `narrative.md` | file exists; its `## Review` has `Verdict: PASS` | hand off to story-craft: stock-take → narrative → story-review. A REVISE or missing verdict: say so once and stop; build anyway only if the user says so, and record that in `direction.md` |
| the cut | `cuts:` has the cut the user wants (film-60, teaser-20, …) | ask which cut; a new cut goes into `narrative.md` first (story-craft:narrative) |
| `brand-lock.md` | in the motion project root (`motion/brand-lock.md`) | export it with deck-craft:deck-design-guide; without a master, run stock-take's brand interview or fill deck-design-guide's `assets/brand-lock-template.md` by hand |
| font files | `font_files` in brand-lock lists real files | the build holds at the animated test; ask for the files, never substitute a system font |
| build tools | `node --version` ≥ 22, `npx hyperframes --version`, Chrome or Chromium, `ffmpeg -version` | **dry run**: stop after the motion spec (stage 7) and say exactly what is missing |

Dependencies: the **hyperframes plugin** is the build backend (its storyboard and build steps, the `npx hyperframes` CLI: `init`, `preview`, `snapshot`, `check`, `render`). Install it as a plugin; never copy its files into this one. ffmpeg cuts and checks renders.

Do not redo the story. Headline, beats, order, statements and evidence are fixed; a needed change goes back to `narrative.md` with the same beat IDs.

## Project layout

One motion project per product, next to `narrative.md`:

```
motion/
  brand-lock.md
  <cut>/            STORYBOARD.md, motion-spec.md, direction.md, SCRIPT.md (VO only), index.html, compositions/
  shots/            shots.json, takes.md, characters/   (shot-forge)
  renders/          <cut>.mp4, beats/<beat>.mp4, clips.json   (motion-qa)
```

## The stages

Pause at each gate until the user says go. A decision already given in this conversation counts; do not ask it twice. Details, response shapes and what to load per stage: `references/stages.md`.

| # | Stage | You make | Gate |
|---|---|---|---|
| 1 | Cut | the cut, its beats and runtime, format (16:9 / 9:16 / 1:1), VO or muted, real inputs available (UI recording, logo, fonts, footage) | Cut and inputs right? |
| 2 | Style | 3-4 of the styles in `references/styles.md` suggested for this film | Which style(s)? |
| 3 | Reference films (optional) | notes on films the user names: mechanisms only (seams, text position, shot lengths, close) | – |
| 4 | Direction options | 2-3 directions drawn as stills of the **same beat** (the cut's first beat) | Which direction? |
| 5 | Look decisions | a single choice per round, two or three candidates, logged in `direction.md` | Each pick |
| 6 | Storyboard | `STORYBOARD.md`: one frame per beat, in cut order, with `beat`, `medium`, `start`, `duration`; stills of every frame | Stills approved |
| 7 | Motion spec | `motion-spec.md`: lengths first, then a named move, timing and easing per change and per seam | Spec approved |
| 8 | Animated test | the first 20-30 s built and rendered through the hyperframes plugin | Does the movement work? |
| 9 | Full build | the whole cut, every frame `status: animated`, rendered | Final, or notes |
| 10 | Polish rounds | one numbered render per round of notes | Each round signed off |

Then hand off to **motion-qa** (render checks, one clip per beat for deck-craft).

**Generated footage**: after the storyboard is approved (stage 6) and the user has agreed a budget (shot count × takes), send every `generated` or `mixed` frame to **shot-forge**. It writes `shots/shots.json` and the take log; this skill places the takes. No generated shot holds UI, text or logos; screens are composited here.

## Stage notes

- **Cut (1)**: run `scripts/check_storyboard.py` from stage 6 on; the cut's beats and order are the frame list. Per-beat budget from story-craft's `cuts.md` (film-60: 5-7 s, teaser-20: 3-5 s; the star about twice the median).
- **Direction options (4)**: `references/direction-options.md`. Options differ in their central idea, not in colour. Each states its idea, lead medium, recurring element, way of moving between ideas and end line. Recommend one in one sentence.
- **Look decisions (5)**: in this order: product presentation → colour treatment inside brand-lock → footage grade → the signature (star) frame's layout → line placement → type. One decision per round. Write the pick, the date, the reason and exact values to `direction.md` the moment it is made.
- **Storyboard (6)**: start from `assets/STORYBOARD-template.md`. HyperFrames-compatible: frontmatter `format, duration, message, arc, audience` plus `cut, narrative, brand_lock`; per frame `status, duration, transition_in, scene, voiceover, poster, reads, sound` plus `beat, medium, start, statement`. Choose each frame's medium with the rule below. Pose stills with the hyperframes plugin's storyboard step. Run `python scripts/check_storyboard.py <cut>/STORYBOARD.md`; 0 errors before showing it.
- **Motion spec (7)**: `references/motion-spec.md`. Fix lengths before moves and tell the user the new total.
- **Animated test (8)**: build the first 20-30 s (hook, cost, turn, reveal in a film-60), because the hook decides whether anyone watches the rest. Use the hyperframes plugin's build step; `npx hyperframes check` clean, then `render`. Say which frames are covered and what is still a placeholder. Render slow, GPU unused or the file oddly large: `references/render-performance.md`.
- **Full build (9)** and **polish (10)**: every render the user sees names its placeholders. Find each note in the frames (± 1 s) and say back what you will change before changing it. One new numbered render per round; never overwrite a render.

## Medium rule per beat role

The medium is the frame's lead picture (`motion`, `generated`, `ui`, `mixed` = two picture sources sharing the frame). Type on top of footage does not change the medium.

| Role | Medium | Why |
|---|---|---|
| villain, moment, outcome | generated footage or motion | the viewer must recognise their own week |
| reveal, pillar | motion graphics | the name and the idea, clean; a pillar never fakes a product screen |
| proof, star (demo) | real UI recording, never a mockup | one invented button loses everyone who uses the product |
| cost, versus | motion: one number | a number made physical, same unit on both sides |
| voice | motion type over a still or footage | a quote, attributed by role; never a generated face speaking it |
| turn, objection | motion | a question or an answer in type |
| close | motion end card with the brand mark | the ask held, the logo landing once |

`references/launch-rules.md` has the full rules: no-speaker cuts, brand-lock use, credibility and the tells of a generic film.

## Rules that always apply

- **Hook in 2 s**: the first frame doubles as the thumbnail, so it shows the need, not black or a bare logo.
- **Text carries the claim**: the beat statement is on screen; VO is optional and never read word for word on screen.
- **Brand-lock only**: hero colour on one thing per frame; fonts from the listed font files; logo from the logo file, landing once on the end card.
- **Claims only from the proof ledger**: every number on screen has its fine print from `narrative.md`; nothing the narrative does not say.
- **Before generating anything** (stills, clips), say what it is, where it goes and what it costs.
- **Version everything**: `STORYBOARD.md` and `motion-spec.md` change in place with a dated line in `direction.md`; renders are numbered.

## Output

Per cut in `motion/<cut>/`: `direction.md`, `STORYBOARD.md`, `motion-spec.md`, optional `SCRIPT.md`, the HyperFrames build; round renders `renders/<cut>-vN.mp4`, the signed-off one copied to `renders/<cut>.mp4` for motion-qa. Example: `examples/atlas/film-60/`.

Next: "motion-qa checks the render and exports one clip per beat for deck-craft."

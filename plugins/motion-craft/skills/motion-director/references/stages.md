# Stages in detail

What to load, what to make and how to ask at each gate. Load a stage's files when its gate opens, not before. Explicit approval in this conversation counts; never repeat an answered gate. Every reply states real limits (missing tool, placeholder, unchecked item) before its question.

## 1. Cut

Load: `narrative.md` (frontmatter, proof ledger, Review), story-craft `cuts.md`, `brand-lock.md`.

Make: nothing on disk yet. Read the cut's beats and runtime, and settle in one message:
- **cut** and **format** (16:9 for a landing page, 9:16 or 1:1 for a feed; a second format is a second cut folder);
- **sound**: muted-first with optional VO (the beat `line`, shortened), music bed, or VO-led;
- **real inputs**: a screen recording or a test account for every `proof` and `star` beat, the logo file, the font files, any real footage or photos;
- **media tools**: a clip tool for generated footage (via shot-forge) or none. Without one, `generated` frames become motion or stills (`Layered stills` in `styles.md`).

Ask: "Cut [name]: [n] beats, [runtime]. Format [x]. Sound [x]. Real inputs: [have / missing]. Clip tool: [x]. Right?"

## 2. Style

Load: `styles.md`.

Suggest 3-4 styles that fit the product, the viewer and the brand-lock, clearly different from each other, all buildable with the tools from stage 1. Include Product close-up whenever the cut has a `star` or `proof` beat. One plain line each.

Ask: "For a [film] made of [media], I suggest: [style]: [line]; [style]: [line]; [style]: [line]. Pick one or more, describe the look in your own words, or say 'you choose'." Record the pick in `direction.md`.

## 3. Reference films (optional)

Only when the user names films or wants references. Study what you can actually open: pull stills with ffmpeg (`ffmpeg -ss <t> -i ref.mp4 -frames:v 1 ref-<t>.jpg`) and write down how it works: what bridges each seam, text height as % of the frame, shot durations, the shape of the ending. Take the techniques only; leave its look, logo and footage alone. Record what was inspected in `direction.md`. Built from scratch: say so in one line and move on.

## 4. Direction options

Load: `direction-options.md`, `styles.md`, `launch-rules.md`.

Make 2-3 directions as stills of the cut's first beat (start, end, and the first frame of the next beat). Write them into `direction.md` with a recommendation.

Ask: "[stills]. A: [idea]. B: [idea]. C: [idea]. I recommend [x] because [reason]. Which direction?"

## 5. Look decisions

Load: `direction-options.md` (look decisions), `launch-rules.md` (brand-lock use).

One decision per round, same frames each time: product shown → colour treatment → footage grade → star layout → line placement → type. When the decision changes something already drawn, show the current frame beside the options, labelled "Now".

Reading answers:
- An unclear answer ("the second one"): name the option you understood.
- Two liked options with one shared complaint: keep both, correct that one thing in each, and show the pair again.
- Change only what the user pointed at.
- Every option rejected: name what all of them shared before drawing new ones.

Ask: "[options on the same frames]. Decision: [x]. I recommend [y]. Which?"

## 6. Storyboard

Load: `assets/STORYBOARD-template.md`, `launch-rules.md` (medium rule), the hyperframes plugin's storyboard step.

1. Copy the template to `motion/<cut>/STORYBOARD.md`. One frame per beat of the cut, in cut order.
2. Per frame: `beat`, `medium` by the role rule, `start` and `duration` (per-beat budget from `cuts.md`; the star about twice the median), `statement` (verbatim or shortened, never a new claim), `scene`, `reads` with windows, `sound`, `voiceover` (or none), `transition_in`, `poster`, `status: outline`.
3. Free text under the bullets: what is on screen, what is real, fine print, what carries over.
4. Run `python scripts/check_storyboard.py motion/<cut>/STORYBOARD.md`. Fix every error; justify or fix every warning.
5. Pose the stills with the hyperframes plugin's storyboard step (one still per frame, at its poster time). Without the build tools: describe each still in the frame text (dry run).
6. List generated shots with a count and a rough cost; they go to shot-forge only after this gate and a budget OK.

Ask: "[storyboard + stills]. [n] frames, [total] s. Media: [x motion, y generated, z ui]. Generated shots: [n, cost]. Placeholders: [list]. Approve, or notes per frame?"

## 7. Motion spec

Load: `motion-spec.md`.

Lengths first (read times), then every change inside each frame and every seam, then conflicts with the storyboard. Report the revised total to the user first, then retime.

Ask: "[motion-spec.md]. Total [x] s. Seams: [kinds]. Conflicts: [resolved / open]. Approve?"

**Dry run ends here** when the build tools are missing: "Storyboard and motion spec are ready. To build I need: [node ≥ 22 / hyperframes plugin / Chrome / ffmpeg / font files / UI recording]."

## 8. Animated test

Load: the hyperframes plugin's build step.

Build the first 20-30 s of the cut. Mark every element holding words with its text role so checks can size it. `npx hyperframes check` clean, then `npx hyperframes render`. Pull a still at every seam (`ffmpeg -ss <t>`) and look at both sides.

Ask: "[render]. Covers frames [1-n], [0-x s]. Placeholders: [list or none]. Seams checked: [n]. Watch for pacing and anything that still feels like slides. Does it move right?"

## 9. Full build

Build the rest, update every frame to `status: animated`, render `renders/<cut>-v1.mp4`. Before the user sees it: `check` clean, a still at every seam, a muted watch at phone size, the close against the end-card rule.

Ask: "[render]. Placeholders: [list or none]. Checks: [results]. Final, or notes with timestamps?"

## 10. Polish rounds

Per round:
1. Find each note in the frames: pull stills at its time and 1 s either side; describe the moment you found and the planned edit. When a note's word might refer to on-screen text or to a thing in the picture, state your reading.
2. Change only what the notes ask. A note that changes the story goes back to `narrative.md`.
3. New numbered render (`-v2`, `-v3`); answer each note in a numbered list.

When signed off: copy the render to `renders/<cut>.mp4` and hand off to motion-qa.

# Direction options and look decisions

Every visual decision is a pick between 2-3 real options, drawn on the same frames. People choose well between A and B; they choose badly from a description.

## 1. Directions (stage 4)

Draw 2-3 directions for **the same beat**: the cut's first beat (the hook). Same statement, same timing, different central idea. Three colourways of one layout are one direction.

Ways directions differ (pick ones that suit the story's device in `narrative.md`):

| Kind of idea | On screen |
|---|---|
| One ordinary evening or morning | someone at a place and an hour; the need shows up right then |
| One object travels | one thing (a photo, a file, a defect) moves through every frame |
| Type carries the argument | numbers and statements are the picture; colour fields change per act |
| The result first | the finished output, then the pull back to where it came from |
| One surface | the camera glides across one product surface; each beat is a stop |
| Before and after side by side | the old way churns on one side while the new side moves calmly |

Each direction needs:
- a **short label** the user can repeat ("The pile", "Counter");
- the **idea** as a single sentence that names the product;
- **start still** and **end still** of the beat, plus the first still of the next beat (the hand-off);
- **lead medium** (motion, generated, ui) and the inserts, each with one job;
- **style** from `styles.md`;
- **recurring element** (or none, on purpose);
- **way of moving between ideas** (one seam family that leads; see `motion-spec.md`);
- **end line** (the close statement);
- **cost**: generated shots, recordings needed, risk.

Run these checks on each before drawing:
1. Does it show the beat's statement, not just decorate it?
2. Does the product appear by the reveal, as itself?
3. Would a stranger know what is happening with the sound off?
4. Can the tools from stage 1 build it?
5. Does it avoid the tells in `launch-rules.md`?

Recommend one, with the reason in one clause.

## 2. Drawing the stills

- **With the build tools**: pose the beat in a HyperFrames composition with real words, real fonts and brand colours, and snapshot it with the hyperframes plugin's snapshot step. Stills go to `motion/<cut>/boards/options-direction-v1/`.
- **With generated stills** (a still tool, or shot-forge in still mode): one still per option, same framing, no text or UI in the generated image; type and UI are composited.
- **Dry run**: describe each still precisely (what is where, sizes as % of the frame, colours by brand-lock role and hex) in `direction.md`. The user picks from the descriptions; stills follow when the tools are there.

## 3. Look decisions (stage 5)

After the direction, one decision per round, on the chosen direction's frames:

| # | Decision | Usual options |
|---|---|---|
| 1 | How the product is shown | real screen recording · the real UI rebuilt from recordings (same labels, same states) · hands and device with little UI. Never an invented screen |
| 2 | Colour treatment | built only from brand-lock: light ground with the hero rationed · dark ground · ground changes per act. Flat grounds; a gradient only if the brand already uses one |
| 3 | Footage grade | for generated or supplied footage: one grade for the whole film (time of day, warmth, grain %) |
| 4 | Star frame layout | the signature frame (the `star` beat) in 2-3 layouts |
| 5 | Line placement | four to six frames, lines tried in each spot (upper band, centred, lower third); give the numbers |
| 6 | Type | heading and body faces from brand-lock; sizes as % of frame height |

Smaller choices (how a person appears, a tile style) come up as they arise, two options each.

## 4. direction.md

One file per cut. Sections:

```markdown
# Direction · <product> · <cut>

Narrative: <path> (Review: PASS) · Brand: <path> · Style picked: <styles>

## Options shown · beat <Bxx>
### A · "<name>" (recommended)
- Idea / Start still / End still / Lead medium / Recurring element / Moving between ideas / End line / Cost
### B · ...

## Pick
<date> · <who> picked <option>. Reason: <their words>. Kept from other options: <if any>.

## Look decisions
| # | Decision | Options shown | Pick | Values |

## Open
- <inputs still missing, placeholders, budget decisions>
```

Write the pick and its exact values (hex, %, sizes) the moment it is made. Later sessions read `direction.md`, not the chat.

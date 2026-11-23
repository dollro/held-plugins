# Generated clips: shots that survive the model

When to read: sections 1-3 while writing shots.json (splitting a shot doubles its cost, so decide before pricing); section 4 once a take fails. Treat every figure here as a starting guess and record the real outcome in takes.md.

## 1. Plan around weak spots

Prompt wording seldom fixes the moves below. Redesign the shot first.

| Risky move | Safer plan |
|---|---|
| Fingers on a phone, laptop or keyboard (typing, swiping) | Keep the device out of use: pocket, seat, or held under the frame edge. The face tells the moment; the product appears later as a real screen recording |
| Anything with lettering: screens, signs, labels, paper, plates | Point it away, blur it, or leave it out. All words come from the build |
| Hands operating something (pen, handle, pour, keys) | End the shot just before contact; or keep contact under ~1.5 s, hand already placed; or show only what it achieved |
| Passing an object between people | Shot one: arm extends. Shot two: the other person already holds it. The edit performs the exchange |
| Physical contact between two people | Film each person separately; the edit joins them at the instant they meet |
| Getting into or out of a chair | Begin seated. To rise, palms push on the knees, not the armrest |
| Quick movement, chase cameras, stairs | Lock the camera wide and let the person pass through; or two locked shots |
| Exiting and re-entering the frame | Allow the exit; any return is its own shot |
| Spinning round | Limit the body turn to about a quarter |
| Mirrors or glass showing a face | Frame the reflection alone, or disturb it (rain, steam, darkness) |
| Groups | Backs, silhouettes, soft focus; two sharp faces at most |
| Precise quantities ("47 photos") | Keep counts out of the picture; motion-director sets the figure as type |

Reliable moves: visible breathing, a head turn below ~45°, a glance down or up, a slow exhale, two or three unhurried steps toward the lens, light shifting over a still subject, weather, steam, dust, a gentle push in. Every shot with a person should ask for breathing, or the clip reads as a frozen photo.

**Two hard things → two shots.** If a shot combines contact with anything else that strains the model (length over ~5 s, a moving camera, a second person, a prop that must stay exact), split it now. The first part stops once the result is clear but before motion ends; the second picks up mid-movement from a fresh angle.

## 2. Joining generated shots

Each generation is blind to its neighbours, so the prompt must carry the join.

- **Screen geography.** Decide per scene which third each person occupies and their gaze and travel direction. Repeat it in every prompt of that scene. Change it only in a shot that shows the move.
- **Big enough jump.** Two consecutive shots of one subject need ≥ ~30° of camera rotation or a size change of two steps (medium close-up → insert). Describe the new view by its visible content. Small jumps read as errors.
- **A single light source per scene.** Write one scene light line and paste it unchanged into each prompt of that scene; then add where that light lands in this framing. When the source sits outside a close-up, name it plus one visible consequence.
- **Edit during motion.** Cutting at peak movement masks mismatches; cutting between two still poses exposes them.
- **Spare second.** Takes wobble at the start and wander at the end. Request about one extra second beyond `duration_s` (and price it), cut both ends, then judge. Exception: clips driven by an approved first and last frame.
- **Footage beside motion graphics.** Link the two by colour or shape (the van lamp's orange becoming the brand hero colour), not by content. Agree the link with motion-director in the storyboard.

## 3. Lock continuity up front

- **Character sheet** (`assets/character-sheet.md`) before any take: age, build, two or three facial facts, one distinctive mark, hair, wardrobe per scene. Its anchor paragraph is copied unchanged into each prompt. The mark gives the quickest face check.
- **Reference stills.** Approve one neutral front still per person; derive each scene still by editing that image rather than prompting anew. Supply them as references if the provider allows (`providers.md`).
- **Continuity rows.** Per shot: wardrobe, props, frame side, light, and the cut from the previous shot. Each shot inherits the end state of the one before.
- **Last frames come from first frames.** With first/last-frame control, produce the last frame as an edit of the first that alters one thing only. Several alterations mean several shots.
- **Plain surfaces.** Unprinted vests, unbranded helmets, no stickers or plates: any blank surface invites invented lettering.

## 4. When takes fail

Translate vague notes into observable faults:

| Reviewer says | Look for |
|---|---|
| fake | weightless bodies, drifting pace, wandering light, a face moving on a frozen body |
| AI-ish | shapes dissolving, limbs fusing; next hands, eyes, teeth; then elastic timing |
| cheap | wrong pace first, then flat or unstable lighting |
| dull | a planning issue, not a generation one: redesign or remove the shot |

Repair in order of cost:

1. Trim the fault out in the edit.
2. Adjust one thing (prompt wording or reference still) and name it in the critique (`revise_prompt`).
3. Re-run unchanged once at most; luck is not a method.

Stop generating a shot after `max_takes` failures (default 3) or a second "fake" verdict, and set `change_approach`. Skip straight there, without spending the remaining takes, if the shot relies on a risky move from section 1.

| Approach | Use when |
|---|---|
| `split` | contact or length broke it: two shorter shots and a cut |
| `still_push` | the beat is a face or a place: best frame as a still, slow push and light shift in the build |
| `motion` | the beat works as brand motion graphics: return it to motion-director |
| `drop` | the film stands without it: neighbouring frames absorb its time |

Each option costs less than more takes. If one would exceed the approved cap, show the new total and ask before acting.

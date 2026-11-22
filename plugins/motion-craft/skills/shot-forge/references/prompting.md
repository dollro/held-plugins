# Prompting a shot

One shot in shots.json → one prompt. The prompt is built from the shot's fields, in a fixed order, so two prompts of the same scene differ only where the shots differ.

## Order

| # | Part | From | Example (atlas S01) |
|---|---|---|---|
| 1 | Character anchor, verbatim | character sheet, `## Anchor` | "A man about 45, medium build …, light stubble." |
| 2 | Wardrobe for this scene | character sheet, wardrobe row | "He wears a plain orange high-vis vest over a charcoal fleece." |
| 3 | Place and state | `subject`, continuity row | "He sits in the driver's seat of a parked white van at dusk, holding a phone low in his lap below the frame edge." |
| 4 | One action | `action` | "He breathes out slowly and his head sinks slightly." |
| 5 | Camera | `camera` | "Medium close-up from the passenger side, eye level, 50 mm lens, locked-off camera; left third, facing right." |
| 6 | Light | scene light line verbatim + `light` | "Dusk, deep blue sky; the only warm source is … camera right; a cool glow … from below." |
| 7 | Look | brand-lock mood, one line for the whole film | "Muted, slightly desaturated colour, fine film grain, shallow depth of field." |

Duration, aspect, resolution, seed and references are parameters, not prompt text (`providers.md`). Keep the prompt under the provider's limit; cut from part 7 first, never from 1 or 6.

## Rules

- **One action per shot.** Two verbs of movement means two shots.
- **Describe what is there.** Models often draw what a prompt negates: "no text" invites text. The prompt never names screens, text, logos or UI, not even to forbid them. Put them in `negative` if the provider takes a negative prompt; otherwise leave them out and let the critic catch them. `validate_shots.py` fails a shot whose subject, action, light or prompt names them.
- **Phones and laptops.** Show the person, not the device: in a pocket, face down on a seat, held low below the frame, its glow on the face. A screen the story needs is a real UI recording, cut to or composited in the build (frame medium `ui` or `mixed`), never a generated screen.
- **Numbers and words stay in the motion layer.** The beat statement ("47 photos. 3 voice memos. Zero report.") is set in type by motion-director over or after the shot. The picture shows the feeling, not the count.
- **Same words for the same thing.** "white van", not "van" in one prompt and "work truck" in the next. Copy, do not paraphrase.
- **Camera in film words.** Shot size (wide, medium, medium close-up, close-up, insert), lens in mm, height, move (locked off, slow push in, slow pan left). One move per shot, slow.
- **Reference images beat words for faces.** Pass the approved still when the provider takes one, and keep the anchor in the prompt anyway.

## Revising after a critique

Change one thing per take and name it in the take log's prompt column or the critique's `fix`:

| Critique issue | Prompt change |
|---|---|
| face drifted | add or restore the anchor verbatim; pass the reference still; shorten the shot |
| light from the wrong side | restore the scene light line verbatim; add one visible effect ("shadow falls to the left") |
| floaty or rubbery motion | slower, smaller action; locked-off camera; shorter duration |
| text or a logo appeared | move the object out of frame or out of focus in the prompt; add it to `negative`; plain wardrobe |
| wrong framing | the shot size and lens first in part 5, in film words |
| hands or contact broke | not a prompt problem: change approach (`generated-clips.md`, section 4) |

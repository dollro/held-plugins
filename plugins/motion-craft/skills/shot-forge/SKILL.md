---
name: shot-forge
description: Generates the footage frames of a launch film with whichever video-generation MCP is connected - after motion-director's storyboard is approved, it writes shot specs (shots.json), a character and continuity sheet and a budget estimate against the intake budget, waits for approval, prompts each shot without any visible UI, text or logos, judges every take against its spec with a critic loop (accept, revise the prompt, or change approach after 3 failures) and logs every take in takes.md. Use for "generate the shots", "B-roll", "AI footage", "generated video clips", "KI-Video", "make the clips for frame 1", or when a STORYBOARD.md frame has medium generated. Not for the film plan, storyboard or motion graphics (motion-director), not for checking finished renders or exporting clips (motion-qa), not for real UI recordings (record the product).
license: MIT
---

# shot-forge

Generated footage carries the human moments a film needs and motion graphics cannot draw: a tired face in a van at dusk, someone home on time. It never carries the product. Screens, numbers and words come from the build (real UI recordings, type set by motion-director). This skill turns the approved storyboard's `generated` frames into accepted clips, within a budget the user approved, and stops wherever it would otherwise guess.

Files (in the motion project, see the layout in motion-director):

```
motion/shots/shots.json                 shot specs, one file per cut
motion/shots/characters/<handle>.md     character + continuity sheet
motion/shots/characters/refs/           approved reference stills
motion/shots/prompts/<shot>-t<n>.txt    prompt sent per take
motion/shots/clips/<shot>-t<n>.mp4      every take, accepted or not
motion/shots/critiques/<shot>-t<n>.json one critique per take
motion/shots/takes.md                   take log, budget, spend
```

## 0. Gate

Start only when all of these hold; otherwise say which is missing and stop.

| Needed | From | If missing |
|---|---|---|
| `STORYBOARD.md` of the cut, approved | motion-director | run motion-director first |
| At least one frame with `medium: generated` (or `mixed` with a generated plate) | STORYBOARD.md | nothing to generate; say so |
| `intake.md` with a budget for generated footage | story-craft stock-take | ask the user for a ceiling before pricing |
| `brand-lock.md` (mood, colours) | deck-design-guide | use a neutral look line and flag it |

## 1. Shot specs

For each `generated` or `mixed` frame, write one or more shots into `shots.json` (`schemas/shots.schema.json`):

- `id` S01, S02, … in film order; `beat` and `frame` from the storyboard; `subject`, `action`, `camera`, `light`, `duration_s` (2-10, the length used in the edit), `references`, `prompt`, `continuity`, `max_takes` (default 3), `fallback`.
- Before writing a shot, read `references/generated-clips.md` sections 1-3. Replace actions models get wrong (hands on devices, typing, readable text, fast motion, physical contact) before they cost a take; split hard shots now, not after a failure.
- **No visible UI, screens, readable text or logos** inside a shot. Phones stay in a pocket, face down or below the frame; the glow on a face says "phone" without a screen. A frame that needs the product shows a real UI recording (medium `ui` or `mixed`, composited in the build).
- Build each prompt as in `references/prompting.md`: anchor verbatim, wardrobe, place, one action, camera, the scene light line verbatim, one look line. Describe what is there; negatives go only in `negative`.

Check:

```bash
python <plugin>/scripts/validate_shots.py motion/shots/shots.json --storyboard motion/<cut>/STORYBOARD.md
```

Fix every `S03 · problem → fix` line before going on.

## 2. Character and continuity sheet

One sheet per recurring person from `assets/character-sheet.md`: appearance in a fixed order (age and build, two or three face facts, exactly one check mark, hair), wardrobe per scene (plain, no prints or lettering), setting and the scene light line per scene, reference stills, the anchor paragraph, and the continuity table (one row per shot: wardrobe and props state, frame side and eyeline, light, how it cuts from the shot before).

If the provider takes reference images, the first generations are the reference stills (front, neutral light), approved with the sheet before any clip.

## 3. Budget and approval (stop point)

Price the plan before the first take (`references/providers.md`, section 3):

- seconds per take = `duration_s` + 1 (trim margin); × the connected provider's price per second, or clips × price per clip;
- three figures: one take per shot, typical (two), cap (`max_takes`, default 3), plus reference stills;
- the cap against the intake budget, with the date and source of the price.

Write it into the header of `takes.md` (`assets/takes-template.md`). Show the user, in one message: the shots (id, beat, one line each), the character sheet, the budget table. **Wait for approval.** No take before it. A later take that would pass the approved cap needs a new approval.

Example (atlas, film-60, prices illustrative): 4 shots for B02 (2), B15 and B16, 22 generated seconds per pass at 0.40 EUR/s → 9.80 EUR for one take each, 18.60 EUR typical, 27.40 EUR at the cap of 3 takes, against an intake budget of 600 EUR. See `examples/atlas/shots/`.

## 4. Provider (stop point)

Use whichever video-generation MCP is connected; check its capabilities (reference image, first/last frame, max duration, aspect, audio, seed, negative prompt, price) with `references/providers.md` and note them in takes.md.

**No generation MCP connected:** stop after steps 1-3 (specs, sheets, budget with a labelled placeholder price). Tell the user what to connect, or that motion-director can replace the generated frames with motion or a still. Never fake a clip, never present a placeholder as a take.

No API keys in any file; keys stay in the MCP server's configuration.

## 5. Generate

Per shot, in film order:

1. Save the prompt to `prompts/<shot>-t<n>.txt`; send it with the parameters (aspect from shots.json, duration_s + 1, references, seed if offered, audio off).
2. Download the clip to `clips/<shot>-t<n>.mp4`. Append the take to takes.md the moment it returns.
3. Judge it (step 6) before the next take of that shot.

At most `max_takes` per shot (default 3). One change per take; one unchanged repeat at most.

## 6. Critic loop

Judge each take against its shot spec, the character sheet and the continuity row, after trimming the ends. Write `critiques/<shot>-t<n>.json` (`schemas/critique.schema.json`):

- `scores` 1-5 for spec_match, character, continuity, motion, anatomy, clean_frame, light;
- `issues`: criterion, severity (minor: trim or fix in the edit; major: a prompt change or a new take fixes it; blocking: no prompt fixes it), what is visible and at which second, the exact fix;
- `verdict`:

| Verdict | When |
|---|---|
| `accept` | only minor issues; no score at 1; clean_frame 5 (no screen content, letters or logos anywhere) |
| `revise_prompt` | one or two major issues with a named prompt change, and takes left |
| `change_approach` | a blocking issue, the shot needs something models get wrong, "looks fake" twice, or the third failed take; set `approach`: `split`, `still_push`, `motion` or `drop` (`references/generated-clips.md`, section 4) |

Judge what is visible, not a mood ("left hand has six fingers at 2.1 s", not "feels off"). Do not critique what the spec did not ask for. A change of approach that touches the storyboard (motion instead, a dropped shot) goes back to motion-director and the user; a new approach that would pass the cap needs approval.

## 7. Take log

Every take gets a row in `takes.md`, accepted or not: shot, take, provider, model, prompt (text or `sha256:` of the prompt file), params, seed, cost, verdict, file. Rows are never edited; keep a running spend against the approved cap.

## 8. Hand on

Report per shot: accepted take and file, or the approach that replaced it; spend against the cap. Accepted clips go to the build (`index.html`, compositions) through motion-director; screens and type are composited there. Then: "Next: motion-director builds the cut; motion-qa checks the render."

## Files

- `references/generated-clips.md`: actions to avoid, cuts, continuity, what to do when takes fail
- `references/prompting.md`: prompt order, no-UI rules, revising after a critique
- `references/providers.md`: finding the connected MCP, capabilities, pricing, keys
- `assets/character-sheet.md`, `assets/takes-template.md`
- `schemas/shots.schema.json`, `schemas/critique.schema.json`
- `<plugin>/scripts/validate_shots.py` (tests: `test_validate_shots.py`)

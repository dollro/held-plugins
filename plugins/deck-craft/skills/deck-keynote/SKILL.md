---
name: deck-keynote
description: Designs bold, stage-ready presentations in the tradition of the great product launches (Jobs-era Apple keynotes, Duarte's Resonate) - a one-line headline, a sparkline that alternates what is and what could be, villain and hero, rule of three, one number per slide made meaningful, slide-by-slide reveals, a STAR moment, a close with availability - while staying inside the company's slide master. Reads narrative.md from story-craft when it exists and maps its beats to slide types; otherwise applies short inline arc rules. Produces a storyboard with a Beat column and speaker notes that deck-craft builds. Use for product introductions and launches, vision or strategy talks, all-hands, conference keynotes, demo days, pitch on stage, or requests like "Steve-Jobs-style", "Apple-style", "make it bold", "Produktvorstellung", "Keynote", "Launch-Präsentation". Not for analyst or committee decks (deck-storyline) and not for writing a press release (prfaq skills).
license: MIT
---

# deck-keynote

A keynote is a performance with slides as stage lighting. The slides carry a few words, one number or one image; the speaker carries the argument; the notes carry the script. The output of this skill is a storyboard (`storyboard.md`) that deck-craft builds in `keynote` mode.

## 0. If narrative.md exists, build from it

The story may already be decided by story-craft (`narrative.md`, beats `B01..Bn`, cuts per output). Then:

1. Read `narrative.md` and its `## Review`. If the verdict is REVISE or missing, say so once and suggest story-craft:story-review; build anyway only if the owner says so.
2. **Do not redo the dramaturgy.** Headline, villain, promise, beats, evidence and order are fixed. Your job is the slide form.
3. Take the beats of cut `keynote` (`beats: all` = every beat, in order). One beat = one row in the storyboard, usually one slide.
4. Map each beat's role to a slide type:

| Role | Slide type | Notes |
|---|---|---|
| moment, villain, turn, outcome | `statement` | the beat statement, one accent word |
| cost, proof | `big_number` | the number from the statement; fine print from the proof ledger |
| pillar | `reveal` | consecutive pillars become one `reveal()` run, one slide each; `three` if the master forbids reveals |
| objection | `three` | each answer in one word plus one line |
| versus | `versus` | both sides in the same unit |
| voice | `quote` | verbatim, attribution as in the intake |
| reveal | `image_slide` | product image or labelled placeholder, the name only |
| star | `video` if `clips.json` has a clip for the beat, else `statement` or `image_slide` | live demo: a statement slide that hands over to the demo |
| close | `closing` | availability, price, the ask |

5. If `clips.json` (from motion-craft:motion-qa) exists, offer type `video` for every beat that has a clip; the owner picks which ones play. deck-craft builds them with `video_slide_from_clips()`.
6. Spoken notes come from the beat's `line`, extended for the stage; fine print from the proof ledger. Add nothing the narrative does not say; a needed change goes back to the narrative, keeping beat IDs.
7. In Claude Code, `scripts/storyboard_from_narrative.py narrative.md [--clips clips.json]` drafts `storyboard.md` with this mapping, and `--check storyboard.md narrative.md` confirms the Beat column matches cut `keynote`. Edit the draft by hand; do not reorder beats.

## 1. Without a narrative: the arc in short

When no `narrative.md` exists (story-craft not installed, the PowerPoint add-in, a quick talk), these rules are enough. Full rules: story-craft:narrative; suggest it once for a launch that matters.

- **Headline** of the whole talk in one line a journalist could print (≤ 140 characters). **Promise** in the audience's words: benefits, features only as proof. **Villain**: the concrete pain from their own week, never a named competitor.
- **Sparkline**: alternate what is and what could be. Act 1 (~25%): the moment everyone knows, the villain, its cost in one number, "What if…?". Act 2 (~50%): the reveal (name once, then silence), three things it does, proof per thing, objections answered. Act 3 (~25%): before vs after, a real voice, the STAR moment, availability, price, call to action.
- **One STAR moment** (Something They'll Always Remember), tied to the headline: a demo, a before/after, a startling number.
- **Credibility**: every claim slide has proof or fine print; quotes real and attributable; dates and prices stated or left out, never fudged; benchmarks name the conditions.
- Mark each slide's side (is / could be) and give it Beat `–` in the storyboard.

`references/patterns.md` has a launch sequence, wording patterns and the visual vocabulary.

## 2. Rules for keynote slides

- **One idea per slide.** One statement, one number, one image, one comparison or one clip.
- **Word budget:** aim for 1-8 words on a statement slide, ≤ 20 visible words on any slide; everything else goes into the notes. Average around three words per text slide is a good target.
- **No bullets.** A list becomes a reveal: one slide per item, earlier items dimmed (`reveal()`), or three pillars (`three()`).
- **Big type.** Statements 40-96 pt, hero numbers 120-200 pt, secondary lines ≥ 18 pt. The bigger the type, the fewer the words.
- **One number per slide, made meaningful:** the number, one line saying what it means, and a familiar comparison. Fine print with source or test conditions under every performance claim.
- **Versus slides** for the turn: old way vs new way, or us vs the benchmark the audience already respects. The hero side in the accent.
- **Space:** ≥ 40% of the slide empty. Symmetry and centred composition are fine here.
- **One accent colour,** used on the word or number that matters (`[[word]]` in deck-craft).
- **Images** only from the user or owned; product shots full-bleed or on the master's picture layout. Placeholders are labelled and listed until replaced.
- **Video** only from clips the user made or owns (motion-craft renders); always with a poster frame, never autoplaying with sound, ≤ 60 s. One clip per slide.
- **Charts on stage:** one series, one highlight, three to five bars or points, no axis; the headline says what to see.
- **Notes are the script,** written to be spoken: short sentences, the pause marked, the transition to the next slide in the last line.

## 3. Inside the slide master

Bold does not mean off-brand. Apply deck-craft's template-first ladder:

1. Statement, number, versus, video and closing slides go on the master's **Blank** (or a dedicated statement layout if the master has one), so background, logo and footer stay.
2. Type in the **template's fonts**, colours from the **theme** (accent1 for the hero word or number).
3. Allowed enhancements: larger type; full-bleed image or clip on picture layouts; a **dark or accent stage** painted on a master layout for at most one or two STAR moments (`stage="dark"` or `"accent"`), never for the whole deck unless the master itself is dark.
4. Never: new fonts, off-palette gradients, covering the logo, removing legal footers.

## 4. Leave-behind

A keynote deck read without the speaker fails. If the deck will be sent, produce a **slidedoc** version: the same story, consult density (action titles, short paragraphs, ≤ 250 words per page), or the keynote slides with the notes printed beneath. Video slides show their poster and a link to the clip.

## Output: storyboard.md

```markdown
# <Talk title> · headline: "<one line>"
Audience: ... | Duration: ... min | Template: <file or none> | Stage: master / dark
Narrative: narrative.md (cut keynote, review PASS) or none
Villain: ... | Promise: ... | STAR moment: ...

| # | Beat | Act | Side | On screen (≤ 8 words, [[accent]]) | Type | Notes (spoken) | Proof / fine print |
|---|---|---|---|---|---|---|---|
| 1 | – | – | – | Site reports, finally | title | ... | Illustrative example |
| 2 | B01 | 1 | is | Every site visit ends the same way. | statement | ... | - |
| 3 | B02 | 1 | is | 47 photos. 3 voice memos. [[Zero]] report. | statement | ... | interviews |
...
```

`Beat` is the narrative's beat ID, or `–` for slides that carry no beat (cover, section breaks) and for decks without a narrative. Types map to deck-craft helpers: title, statement, big_number, three, reveal, versus, image_slide, quote, video, keynote_chart_slide, closing.

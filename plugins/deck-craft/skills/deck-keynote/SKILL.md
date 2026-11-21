---
name: deck-keynote
description: Designs bold, stage-ready presentations in the tradition of the great product launches (Jobs-era Apple keynotes, Duarte's Resonate) - a one-line headline, a sparkline that alternates what is and what could be, villain and hero, rule of three, one number per slide made meaningful, slide-by-slide reveals, a STAR moment, a close with availability - while staying inside the company's slide master. Produces a storyboard with speaker notes that deck-craft builds. Use for product introductions and launches, vision or strategy talks, all-hands, conference keynotes, demo days, pitch on stage, or requests like "Steve-Jobs-style", "Apple-style", "make it bold", "Produktvorstellung", "Keynote", "Launch-Präsentation". Not for analyst or committee decks (deck-storyline) and not for writing a press release (prfaq skills).
license: MIT
---

# deck-keynote

A keynote is a performance with slides as stage lighting. The slides carry a few words, one number or one image; the speaker carries the argument; the notes carry the script. The output of this skill is a storyboard (`storyboard.md`) that deck-craft builds in `keynote` mode.

## 1. The headline and the promise

- Write the **headline of the whole talk** in one line a journalist could print and that fits a social post (≤ 140 characters). "Today, X reinvents Y" is the archetype; make it specific to this product.
- Write the **promise to the audience**: what changes for them, in their words. Benefits, not features. Features appear only as proof of a benefit.
- Name the **villain**: the concrete pain, waste or status quo the product defeats. A villain the audience recognises in their own week works better than an industry abstraction.

## 2. Shape the arc (sparkline)

Great talks alternate between **what is** (the frustrating present) and **what could be** (the better future), several times, then end on the new bliss and a call to action. Plan the beats:

| Act | Share of slides | Beats |
|---|---|---|
| 1 Setup | ~25% | the moment everyone knows · the villain · the cost in one number · the question "what if…" |
| 2 Solution | ~50% | the reveal (name once, then silence) · three things it does · proof per thing (number, demo, versus) · objections answered before they are raised |
| 3 Resolution | ~25% | before vs after · real customer voice · the STAR moment · availability, price, call to action |

Each beat is one slide. Mark on the storyboard which side of the sparkline each slide plays (is / could be).

## 3. Rules for keynote slides

- **One idea per slide.** One statement, one number, one image, or one comparison.
- **Word budget:** aim for 1-8 words on a statement slide, ≤ 20 visible words on any slide; everything else goes into the notes. Average around three words per text slide is a good target.
- **No bullets.** A list becomes a reveal: one slide per item, earlier items dimmed (`reveal()`), or three pillars (`three()`).
- **Big type.** Statements 40-96 pt, hero numbers 120-200 pt, secondary lines ≥ 18 pt. The bigger the type, the fewer the words.
- **One number per slide, made meaningful:** the number, one line saying what it means, and a familiar comparison ("faster than any X you can buy", "a working day, every week"). Fine print with source or test conditions under every performance claim.
- **Versus slides** for the turn: old way vs new way, or us vs the benchmark the audience already respects. The hero side in the accent.
- **Space:** ≥ 40% of the slide empty. Symmetry and centred composition are fine here.
- **One accent colour,** used on the word or number that matters (`[[word]]` in deck-craft).
- **Images** only from the user or owned; product shots full-bleed or on the master's picture layout. Placeholders are labelled and listed until replaced.
- **Charts on stage:** one series, one highlight, three to five bars or points, no axis; the headline says what to see.
- **Notes are the script,** written to be spoken: short sentences, the pause marked, the transition to the next slide in the last line.

## 4. Inside the slide master

Bold does not mean off-brand. Apply deck-craft's template-first ladder:

1. Statement, number, versus and closing slides go on the master's **Blank** (or a dedicated statement layout if the master has one), so background, logo and footer stay.
2. Type in the **template's fonts**, colours from the **theme** (accent1 for the hero word or number).
3. Allowed enhancements: larger type; full-bleed image on picture layouts; a **dark or accent stage** painted on a master layout for at most one or two STAR moments (`stage="dark"` or `"accent"`), never for the whole deck unless the master itself is dark.
4. Never: new fonts, off-palette gradients, covering the logo, removing legal footers.

## 5. STAR moment and the reveal

- Plan exactly one **STAR moment** (Something They'll Always Remember): a live demo, a physical reveal, a startling number, a before/after, a short customer story. Tie it to the headline, not to spectacle for its own sake.
- **The reveal**: build anticipation in Act 1, then show the product name or image alone. Say the name once, stop talking for two seconds.
- "One more thing" works only if the thing is genuinely bigger than what came before. Otherwise leave it out.

## 6. Credibility

Bold claims without proof cost more than they win; vague promises without dates or numbers have deflated big launch events. So:
- every claim slide has a proof slide or fine print;
- dates and prices are stated or deliberately omitted, never fudged;
- customer quotes are real and attributable; no invented testimonials;
- benchmark comparisons name the benchmark and the test conditions.

## 7. Leave-behind

A keynote deck read without the speaker fails. If the deck will be sent, produce a **slidedoc** version: the same story, consult density (action titles, short paragraphs, ≤ 250 words per page), or the keynote slides with the notes printed beneath.

## Output: storyboard.md

```markdown
# <Talk title> · headline: "<one line>"
Audience: ... | Duration: ... min | Template: <file or none> | Stage: master / dark
Villain: ... | Promise: ... | STAR moment: ...

| # | Act | Beat (is / could be) | On screen (≤ 8 words, [[accent]]) | Type | Notes (spoken) | Proof / fine print |
|---|---|---|---|---|---|---|
| 1 | 1 | is | Every site visit ends the same way. | statement | ... | - |
| 2 | 1 | is | 6.5 h | big_number | ... | survey, n=120 |
...
```

Types map to deck-craft helpers: statement, big_number, three, reveal, versus, image_slide, quote, keynote_chart_slide, closing. `references/patterns.md` has ready-made beat sequences and wording patterns.

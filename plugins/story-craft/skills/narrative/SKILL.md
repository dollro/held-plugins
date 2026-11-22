---
name: narrative
description: Shapes the story of a launch, keynote, pitch or product film before any medium is chosen - the one-line headline, the villain and what it costs, the promise, a sparkline alternating what is and what could be, the turn, the reveal, rule of three, proof for every claim, one STAR moment, the close - as numbered beats (B01..Bn) with roles and evidence IDs, plus named cuts per output (keynote, film-60, teaser-20). Writes narrative.md, the contract that deck-craft and motion-craft both build from. Use for "launch narrative", "pain, villain, reveal", "Steve-Jobs-style story", "the story arc", "Storyline für den Launch", "Dramaturgie", or after stock-take. Not for analyst or board decks (deck-craft:deck-storyline), not for slide design (deck-craft:deck-keynote), not for reviewing a story (story-review).
license: MIT
---

# narrative

The story is decided once, in words, and every medium plays it. This skill turns `intake.md` (from stock-take) into `narrative.md`: a headline, a villain, a promise, a sequence of numbered beats and the cuts that each output uses. It never mentions slides or shots; a beat is "a moment on screen or on stage". deck-craft maps beats to slides, motion-craft maps them to frames.

## 0. Inputs

- Read `intake.md`. Without it, run stock-take first, or ask the four questions that matter most in one message: belief before and after, the ask, the audience, the outputs. Record that the intake is thin.
- Every claim beat must point at an evidence row of `intake.md` (`E1`, `E2`, …). Evidence tagged `missing` cannot carry a claim: weaken the wording, drop the beat or send the owner to find the evidence.
- Use the owner's words and the audience's words from the intake verbatim where they fit.

## 1. The one thing

Write these four lines before any beat:

- **Headline**: the whole story in one line a journalist could print, ≤ 140 characters. Specific to this product; "Today, X reinvents Y" is the archetype, not the template.
- **Promise**: what changes for the audience, in their words. Benefits, not features; features appear only as proof of a benefit.
- **Villain**: the concrete pain, waste or status quo the product defeats, recognisable in the audience's own week. Never a named competitor.
- **Cost**: the villain in one number, with its evidence ID.

## 2. Three storylines, then one

Write three candidate arcs, one paragraph each, that differ in their **device** (what the story is: a moment in someone's day, life before and after, the result first, a number that lands, a question with the input in it) and their **opening** (the first moment, exactly). Make one of them the bold one you would not have picked first.

Pick one for its story, the one a stranger would follow and remember, and give the reason in one clause. Keep the other two in `narrative.md` under "Storylines considered" so a later turn can switch. If the owner is present, show the three and wait for the pick; if they asked for no stops, take your recommendation.

## 3. Shape the arc (sparkline)

Alternate **what is** (the frustrating present) and **what could be** (the better future), several times, then end on the new state and the ask.

| Act | Share | Beats |
|---|---|---|
| 1 Setup | ~25% | the moment everyone knows · the villain · the cost in one number · the turn ("what if…") |
| 2 Solution | ~50% | the reveal · three things it does · proof per thing · objections answered before they are raised |
| 3 Resolution | ~25% | before vs after · a real voice · the STAR moment · the outcome · the close |

`references/arc-patterns.md` has ready sequences (launch, vision, feature, pitch) and wording patterns.

## 4. Beats

One beat = one idea the audience must take in. Each beat gets:

- an **ID** `B01`, `B02`, … IDs are stable: after the first draft never renumber; a new beat between B07 and B08 is appended at the end of the list as the next free number and placed by its position; a removed beat leaves a gap;
- **act** (1-3), **side** (`is` / `could`), **role** (`references/beat-roles.md`);
- a **statement**: what the beat says, ≤ 8 words where possible (on screen or on stage, the medium decides the form);
- **evidence**: the intake row behind it, or `null`;
- a **line**: the spoken sentence (speaker or voice-over), written to be said aloud.

Rules:
- exactly one `reveal`: the product named, then silence. Build anticipation before it;
- exactly one `star` moment (Something They'll Always Remember), tied to the headline: a demo, a before/after, a startling number, a short customer story;
- at least one `villain`, exactly one `close` (availability, price, the ask; never "questions?");
- **rule of three** for what the product does (`pillar` beats), parallel in form;
- every `proof`, `cost` and `versus` beat carries evidence `solid` or `likely`; `likely` evidence gets softened wording or a qualifier in the statement;
- one number per beat, made meaningful: the number, what it measures, a familiar comparison from the audience's world. Check the arithmetic of every analogy;
- quotes are real and attributable; never invent a testimonial, benchmark or date.

## 5. Cuts

The master narrative is the longest output (usually the keynote: all beats). Each other output is a **cut**: a subset of beats in the same order, with its own runtime. Name cuts by the output IDs in the intake. `references/cuts.md` has the compression rules; in short:

- every cut keeps a `villain`, the `reveal` and the `close`;
- drop from the middle (extra proof, objections, second pillar), never the hook, the reveal or the payoff;
- no-speaker cuts (films, teasers): the first beat is a hook that works in 2 s without sound; the statement carries the claim as text; voice-over is optional;
- rough budget: about 5-7 s per beat in a film, 4-5 beats for 20 s, 8-10 beats for 60 s.

## 6. Output: narrative.md

Write `narrative.md` next to `intake.md` from `assets/narrative-template.md`. The YAML frontmatter is the contract (machine-read by story-review's validator, deck-keynote and motion-director); the sections below it are for people. Fill:

- frontmatter: product, headline, purpose, ask, villain, cost, promise, star, beats, cuts;
- **Why this story**: purpose, audience, the one belief it must change;
- **Storylines considered**: the three, the pick and the reason;
- **Arc**: is / could sequence as one line (`is is is could | could could … | could`) and the act shares;
- **Beats**: table of ID, act, side, role, statement, evidence, line;
- **Proof ledger**: every claim beat → evidence ID, strength, and the wording used for `likely`;
- leave **Review** empty; story-review fills it.

Then hand on: "Next: story-review checks this narrative before anything is built." Without story-review installed, run the checks in its absence yourself: one reveal, one star, a close in every cut, evidence on every claim.

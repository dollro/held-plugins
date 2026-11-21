---
name: deck-storyline
description: Structures the argument of a presentation before any slide is designed - governing thought, Pyramid Principle with MECE groups, SCQA opening, action-title chain, executive summary with the ask, ghost deck, and scaffolds for pitch, recommendation, board or steering-committee update, report-out, workshop and investment decision. Outputs storyline.md, the spine every later step builds on. Use when someone wants to structure a deck, write or fix action titles, build an executive summary, says the deck "does not tell a story", asks for a ghost deck or storyboard, or says "Storyline", "roter Faden", "Pyramid Principle", "SCQA", "Executive Summary bauen". For a product-launch or keynote arc use deck-keynote; for building the slides use deck-craft.
license: MIT
---

# deck-storyline

The storyline is the deck. Fix it in text, where changes are cheap, before anyone opens PowerPoint. Output: `storyline.md` (format at the end), or the same content in the chat when no files are in play.

## 1. Find the governing thought

1. Name the audience and the **one question they bring** ("Should we keep the logistics unit?", "Why is margin falling?", "Which option wins?"). If you cannot name it, ask.
2. Write the **answer in one sentence**. This is the apex. If you cannot write it, the analysis is not finished: say so and list what is missing.
3. Name the **ask**: the decision, budget, approval or date wanted from this audience.

## 2. Build the pyramid

- Below the apex, 3-5 supporting arguments that together prove it. Either **inductive** (independent reasons) or **deductive** (situation → problem → therefore). Do not mix the two in one group.
- **MECE test** on every group: check each pair for overlap; check the set for gaps against the audience question, using a known structure (process start to end, all segments, all P&L lines). "Other" only as a small last resort.
- Push each argument down until every leaf is **one slide of evidence** you can actually produce.
- **So-what test** at every node: a claim that could be argued, never a topic. "Churn is concentrated in the first 90 days" not "Customer churn".

## 3. Open with SCQA

- **Situation**: facts the audience already accepts. If they would dispute it, it is a finding, not a situation.
- **Complication**: what changed or is at risk.
- **Question**: the one the complication raises; the deck answers exactly this.
- **Answer**: the apex.
- Order by stance: supportive or senior audience → answer first, SCQA as backup logic. Skeptical audience → walk S, C, Q so they arrive at the question before you give the answer.

## 4. Write the action-title chain

Per slide, one action title:
- one complete sentence with a verb that carries the so-what (drives, erodes, doubles, concentrates, depends on);
- the headline number when the body shows one; never a number the body does not show;
- 8-14 words, ≤ 90 characters; cut hedges ("various", "key", "it is important to note", "we believe" unless the doubt is the point);
- claim strength matches the evidence: correlation is not causation, a pilot is not a rollout.

Then read the titles **as one paragraph** (horizontal logic). They must argue the case: situation, complication, resolution, supporting points, ask. A title that does not advance the argument marks a slide that may not belong. Check vertical logic per slide: the body proves exactly the title, nothing more.

## 5. Executive summary (slide 2)

- Title = the governing thought as an action title (not "Executive summary").
- 3-5 rows: heading + one sentence each, the same MECE arguments that structure the sections, each with its headline number.
- The ask in its own band at the bottom.
- Reconcile: every row has a section that proves it; every section ladders up to a row. A section with no row is a candidate for backup.

## 6. Ghost deck

For anything high-stakes, expensive to redo or ambiguous: one unstyled slide per leaf with the final action title, the intended exhibit in one line ("waterfall from 34% to 28% margin"), the data needed and whether you have it, and a confidence tag (solid / likely / speculative). Review the title chain and page count before building. In Python: `ghost_slide()` in deck-craft.

## 7. Density and backup

- One message per slide. Several messages: split. Fragments of one message over several slides: merge.
- Glance test: the point lands in 5-10 seconds when presented. A read-ahead (slidedoc) may carry more text but still one point per page.
- Methodology, full tables and granular data go to backup, labelled as such.

## 8. Scaffolds by occasion

Read `references/scaffolds.md` for the slide-by-slide pattern of: recommendation or decision deck, steering-committee update, board update, investment or funding decision, investor pitch, report-out, workshop, and the bridge to deck-keynote for launches.

## Output: storyline.md

```markdown
# <Deck title>
Audience: ... | Question: ... | Ask: ... | Mode: consult | Slides: 12 (+ backup)

## Governing thought
<one sentence>

## SCQA
S: ... C: ... Q: ... A: ...

## Pyramid
- <argument 1 as a claim>
  - <evidence leaf> → slide 4
- ...

## Spine (one line per slide)
| # | Section | Action title | Exhibit | Data (have / need) | Confidence |
|---|---|---|---|---|---|
| 1 | - | Cover | - | - | - |
| 2 | - | <governing thought> | exec summary + ask | - | solid |
...
```

Finish by printing the titles alone as a paragraph and naming any title the evidence does not yet support.

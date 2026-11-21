---
name: deck-review
description: Reviews and reworks presentations to a senior standard - partner-grade review top-down (story, title chain, MECE, exhibit fit, craft, density, consistency, evidence, ask) with a prioritised fix list, keynote review (arc, word budget, one number per slide, claims with proof), template-compliance audit against the slide master or design guide, flow and page-tracker audit, density rebalancing, and before/after redesign of single slides that keeps every fact. Runs deck-craft's check_deck.py when available. Use for "review my deck", "partner review", "is this ready for the board", "Folien prüfen", "Deck reviewen", "redesign this slide", "mach die Folie besser", or before any deck goes out. Not for building a deck from scratch (deck-craft).
license: MIT
---

# deck-review

Review top-down: story before slides, message before format. Findings come back prioritised, each tied to a slide number and a concrete fix.

## 0. Get the facts first

- Audience, the decision or reaction wanted, presented live or read, template or design guide that applies.
- If the deck is a file and Python is available, run deck-craft's checker first: `python <plugin>/skills/deck-craft/scripts/check_deck.py deck.pptx` (mode is auto-detected for deck-craft decks; otherwise pass `--mode consult|keynote`) and render it (`render.py`). Read the printed spine before anything else.
- Without Python (e.g. the PowerPoint add-in): extract the titles yourself and look at every slide.

## 1. Partner review (consult and slidedoc decks)

Work in this order; the order is the priority.

1. **Story and answer.** One recommendation, up front? Does it answer the audience's actual question? Could the decision be made from the executive summary alone?
2. **Title chain.** Read titles in sequence as a paragraph. Every title a claim, not a topic? No gaps or jumps? Does each title match what its slide proves?
3. **MECE and logic.** Groupings without overlap and gaps? Each section ladders to a summary point? Orphan slides?
4. **Exhibit fit.** Right form for the relationship? One highlight? Comparison anchor? Any chart that implies a different conclusion than its title?
5. **Craft.** Grid alignment, even spacing, consistent type scale, palette and one accent per slide, one icon family, no chart junk.
6. **Density.** One message per slide; overloaded slides to split, thin ones to merge, detail to backup.
7. **Consistency.** Same category same colour and label everywhere; source and footnote style; number formats and rounding.
8. **Evidence and honesty.** Every number traceable to a source; no claim beyond the data; no invented figure; illustrative data labelled; assumptions stated where they matter.
9. **The ask.** Clear decision, owners, dates at the end.

## 2. Keynote review

1. **Headline**: one line, printable, specific.
2. **Arc**: the slides alternate what is and what could be; the villain is concrete; the reveal is clean; there is one STAR moment.
3. **Per slide**: one idea; ≤ 20 visible words (most statements ≤ 8); no bullets; one number per slide with meaning and fine print; ≥ 40% empty space; one accent.
4. **Proof**: every bold claim has a proof slide or fine print; benchmarks named; quotes real.
5. **Notes**: every slide has spoken notes with the bridge to the next.
6. **Close**: availability, price or the concrete next step.

## 3. Template-compliance audit

Against the slide master (and `design-guide.md` if one exists):
- right layout per slide role; titles in the title placeholder, not in text boxes over it;
- only theme fonts and colours; accent used as the guide defines;
- protected zones clear (logo, bands, footer, page number, legal line);
- no re-styled placeholders the master already styles; no stray empty placeholders;
- keynote enhancements within the allowance (painted stages on ≤ 2 slides unless the master is dark).

## 4. Flow and navigation

- Sections match the pyramid's supporting arguments; each starts with a divider carrying the section takeaway.
- A small tracker on body slides shows the current section (only where the master leaves room).
- Headers, footers, page numbers continuous and identical in position.
- The last slide of each section hands off to the next question.
- Backup separated and labelled. Read dividers and trackers alone: they should narrate the structure.

## 5. Before/after redesign of one slide

1. Read it cold; note what the point seems to be and how long it took to find.
2. Recover the one message; write the action title (or keynote line). Several messages → plan a split.
3. Inventory every fact, number and label on the original.
4. Choose the right exhibit for the relationship (deck-exhibits).
5. Regroup MECE, lay out on the grid, strip junk, add the single highlight and at most one annotation.
6. Bring it into the template: layout, placeholders, theme colours and fonts.
7. Check the inventory: every real fact is still there, on the slide or in backup.
8. Write a before/after note: what changed and why.

## Output

```
Verdict: <ready / not yet ready> because <one sentence>.

Blockers (story or logic broken)
- s<n>: <finding> → <fix>
Majors (title or exhibit wrong, template broken)
- ...
Minors (alignment, colour, wording)
- ...

Do first: <three highest-impact fixes>
```

If asked to fix as well, apply the fixes in that priority, re-run the checker, and report what changed per slide.

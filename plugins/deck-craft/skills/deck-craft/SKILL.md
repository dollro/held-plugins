---
name: deck-craft
description: Builds PowerPoint decks two ways - consulting-grade analyst decks (action titles, pyramid storyline, one message per slide, native editable charts, sources) and bold keynote or product-launch decks (few words, huge type, one number per slide, reveal, story arc) - always inside the user's slide master when one exists. Orchestrates the sibling skills deck-storyline, deck-keynote, deck-exhibits, deck-design-guide and deck-review; builds with python-pptx in Claude Code or works directly in the PowerPoint add-in. Use for any request to create, rebuild or restyle a deck, pitch, board or steering-committee presentation, executive summary, product launch, keynote, "McKinsey-style", "Steve-Jobs-style" or "Apple-style" slides, or "Folien/Präsentation erstellen". Not for reviewing an existing deck only (deck-review) or capturing a brand template (deck-design-guide).
license: MIT
---

# deck-craft

Turn a brief, notes or data into a deck a partner could present without rewriting the titles, or a launch a marketing lead would put on stage. This skill decides the mode, enforces the template-first rule, runs the workflow and builds. The method detail lives in sibling skills; load them when the step needs them.

| Step needs | Load |
|---|---|
| The story before any slide: purpose, villain, promise, beats, cuts (`narrative.md`) | `story-craft:narrative` (separate plugin, optional) |
| The argument: governing thought, pyramid, SCQA, ghost deck, executive summary | `deck-storyline` |
| A launch or keynote arc: sparkline, villain and hero, reveal, rule of three | `deck-keynote` |
| Which chart or framework proves a message, finishing an exhibit | `deck-exhibits` |
| A corporate master or brand book to follow, or a design-standard question | `deck-design-guide` |
| Checking or reworking a deck before it goes out | `deck-review` |

If a sibling skill is not installed, the short rules below are enough to build a sound deck.

## 1. Decide mode and runtime first

**Mode.** Ask once if the brief does not make it clear; it decides everything after.

| Mode | For | Slide unit | Text budget |
|---|---|---|---|
| `consult` (analyst) | steering committee, board, investment committee, recommendation, diagnosis, status | action title + one exhibit | title ≤ 90 characters, body 12-16 pt, ≤ 5 bullets |
| `keynote` (launch) | product introduction, vision, all-hands, conference talk, pitch on stage | one idea, few words, huge type | ≤ 20 visible words, statements 40-96 pt, numbers 120-200 pt |
| `slidedoc` (read-ahead) | pre-read, leave-behind, deck sent instead of presented | consult slide, denser | ≤ 250 words, still one point per page |

Mixed decks are normal: a launch with one consult-style proof section, or a board deck that opens with one keynote statement. Pick the dominant mode for the build and switch per slide where the story asks for it.

**Runtime.**
- *Claude Code or any session with Python:* build with `scripts/deckkit.py`, check with `scripts/check_deck.py`, look with `scripts/render.py`. Read `references/build-python.md` before writing code.
- *Claude in PowerPoint (add-in):* no scripts. Work in the open file with the add-in's own slide tools, follow the same rules, and read `references/powerpoint-addin.md`.

## 2. Template-first rule (applies in every mode and runtime)

When the deck has, or the user supplies, a slide master (.pptx/.potx or a deck to match), the master governs. Climb this ladder and stop at the first rung that carries the message:

1. **Use the master as is.** Pick the right layout, fill its placeholders (title, subtitle, body, picture). Titles go into the title placeholder, never a text box on top of it.
2. **Add exhibits inside the body zone** of that layout: charts, tables, frameworks, drawn in the theme's fonts and colours (accent1 is the accent). Keep clear of protected zones (logo, bands, footer, page number).
3. **Enhance within the mode's allowance:**
   - consult: tracker label and section navigator only where the master leaves room; a callout panel; one accent per exhibit.
   - keynote: larger type in the template fonts, a blank or picture layout for statement and number slides, full-bleed images, one accent word per statement, a dark or accent stage on a master layout for at most one or two STAR moments.
4. **Never:** new fonts, off-palette colours, moving or covering master artwork, re-styling placeholders the master already styles, deleting the master's footer or legal lines.

If `deck-design-guide` produced a `design-guide.json` for this template, load it (`apply_design_guide`) before building. Without a master, deckkit's own clean theme applies (white consult, black keynote stage).

## 3. Workflow

Do not write python-pptx code (or touch the slides in the add-in) before step 4 is done.

1. **Read the brief.** Audience, the decision or reaction wanted, slide budget, duration, data given and its source, template. Invented or sample data makes the deck illustrative (rule H2).
2. **Load the design guide.** Template supplied but no guide yet: run `deck-design-guide` first (in Claude Code its profiler takes a minute). Note layout roles and protected zones.
3. **Write the spine in `storyline.md`.** consult: one action title per slide; read top to bottom, they must tell the whole argument (`deck-storyline`). keynote: one line per slide plus the beat it plays on the sparkline (`deck-keynote`); if story-craft's `narrative.md` exists, the storyboard maps its beats (cut `keynote`) instead of inventing the arc, and every slide carries its beat ID. Fix the story here, not in code. For high-stakes or ambiguous briefs, show the spine (or a ghost deck, `ghost_slide`) before building.
4. **Assign one exhibit or slide type per line** (`deck-exhibits`; keynote slide types in `deck-keynote`).
5. **Build.** Python: write `build_deck.py` importing deckkit; one helper per slide line. Add speaker notes to every keynote slide (`notes()`); the talk lives there.
6. **Check.** `python scripts/check_deck.py deck.pptx`. Fix every ERROR. Read every WARNING and fix it unless you can say why it is wrong.
7. **Look.** `python scripts/render.py deck.pptx` and open the contact sheet and any doubtful slide. Check overflow, overlaps, collisions with master artwork, label clashes, and whether each slide makes its point in five seconds. Fix, rebuild, re-check. Stop when it passes; do not polish forever.
8. **Report.** File name, slide count, the spine, which layouts of the master were used, anything in the brief you could not support with data, and image placeholders still to be filled.

## 4. Hard rules (all modes)

- **H1 One message per slide.** consult: the title states it, the body proves it, nothing else. keynote: one idea, one number, one image.
- **H2 Honesty.** Never present invented numbers as real; label them (`illustrative()`, cover note "Illustrative example · Fictional company and sample data"). Never invent a source, a customer quote, a benchmark or a test result. Every performance claim carries fine print: source or test conditions.
- **H3 Native and editable.** Charts as native PowerPoint charts, tables as tables, text as text. No pictures of charts.
- **H4 Images.** Only images the user supplied or owns. No downloaded photos of real people, no logos of other companies without the user's material, no copyrighted artwork. Otherwise `image_slide()` draws a labelled placeholder and the report lists it.
- **H5 Sources.** Every slide with data has a source line (consult) or fine print (keynote).
- **H6 Language.** Write slide text in the language of the brief. Keep established technical terms in English in German decks.
- **H7 The end asks for something.** consult: decisions, owners, dates. keynote: availability, price, call to action. Never a "Questions?" slide.

## 5. Mode rules in brief

**consult**: action title = full sentence with a verb and, where the body supports it, a number; ≤ 2 lines (~90 characters). Executive summary on slide 2 with the ask. Sections with dividers and a tracker. Exhibits: grey for context, one accent for the point, data labels instead of axes, unit line above every chart, start value axes at zero, no 3D, shadows or gridlines. Body 12-16 pt; if it does not fit at 12 pt, cut words, not size. Detail goes to backup.

**keynote**: headline of the whole talk fits a tweet. Three acts (setup ~25%, solution ~50%, resolution ~25%), alternating "what is" and "what could be". Rule of three. One number per slide, made meaningful by one line and a familiar comparison. No bullets: reveal items slide by slide. ≥ 40% empty space. One accent colour, used for the word or number that matters. Speaker notes written to be spoken. One STAR moment (Something They'll Always Remember).

## 6. Helper menu (deckkit)

| Slide line says | Helper |
|---|---|
| cover | `title_slide(prs, title, subtitle, note)` |
| executive summary + ask | `content_slide` + `exec_summary(s, rows, ask=...)` |
| section start | `divider_slide(prs, section, takeaway, number)` |
| ranking / comparison | `bar_chart(s, cats, vals, highlight=i)` + optional `callout()` |
| trend | `line_chart` or `column_chart` |
| bridge from A to B | `waterfall(s, steps)` |
| mix / composition | `column_chart(..., stacked=True)` or `percent=True` |
| options vs criteria | `table(..., highlight_row=i)` |
| parallel categories (MECE) | `columns(s, items, highlight, band)` |
| two dimensions | `matrix_2x2(s, x_axis, y_axis, quadrants, highlight)` |
| sequence / value chain | `process_flow(s, steps, highlight)` |
| headline numbers (consult) | `kpi_row(s, items)` |
| point at the insight | `annotate(s, text, x, y, target)` |
| decisions and owners | `next_steps(s, rows)` |
| story agreement before building | `ghost_slide(prs, title, exhibit, data_needed, confidence)` |
| keynote statement | `statement(prs, "words with [[accent]]", sub)` |
| keynote number | `big_number(prs, "6.5 h", label, fine_print, context)` |
| keynote three pillars | `three(prs, headline, items)` |
| keynote list, revealed | `reveal(prs, headline, items)` |
| old vs new / us vs benchmark | `versus(prs, headline, left, right, fine_print)` |
| product reveal / hero image | `image_slide(prs, image, caption)` |
| real customer voice | `quote(prs, text, attribution)` |
| keynote close | `closing(prs, headline, details, cta)` |
| one simple chart on stage | `keynote_chart_slide` + `bar_chart(...)` |

Every consult content slide starts with `content_slide(prs, title, section=...)` and ends with `source(s, ...)`. `[[word]]` in any text renders in the accent colour.

## Files

- `references/build-python.md`: deckkit API, layout grid, template handling, check and render, common failures.
- `references/powerpoint-addin.md`: working in Claude for PowerPoint with the same rules.
- `scripts/deckkit.py`, `scripts/check_deck.py`, `scripts/render.py`.
- `examples/consult_example.py` (10-slide steering-committee deck), `examples/keynote_example.py` (14-slide launch; pass a template path to see it inside a master).

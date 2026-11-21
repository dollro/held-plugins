---
name: deck-exhibits
description: Chooses and finishes the exhibit that proves a slide's message - chart family by analytical relationship, framework slides (2x2, process, value chain, pyramid, matrix), MECE layouts, tables - then finishes it with one highlight, direct labels, a comparison anchor, restrained callouts and maximum data-ink. Use when a slide's message is known but not how to show it, when a chart does not communicate, a default Excel chart needs cleaning, a bullet list should become a visual, or someone asks "which chart", "Chart aufräumen", "make this chart tell the story", "2x2", "framework slide", "MECE gliedern". Works for analyst and keynote slides; deck-craft builds the result.
license: MIT
---

# deck-exhibits

An exhibit proves one action title in under five seconds, with no narration. Diagnose the relationship, pick the form, then finish it.

## 1. Select: relationship → form

| The message is about | Use | Avoid |
|---|---|---|
| comparison / ranking across items | sorted bar chart; horizontal when labels are long | unsorted bars, pies |
| change over time, few periods | column chart | line with 3 points |
| change over time, many periods | line chart, ≤ 3 lines | spaghetti of 8 series |
| how A became B (bridge, build-up) | waterfall, ≤ 7 steps | stacked columns side by side |
| composition at one point | 100% stacked bar, or a sorted bar of shares | pie with > 4 slices |
| composition over time | stacked column, ≤ 4 series | multiple pies |
| distribution | histogram, box plot | average alone |
| correlation of two measures | scatter; 2x2 overlay to classify | two bar charts |
| ranking with a Pareto point | sorted bars + cumulative line | |
| two crossing dimensions of ideas | 2x2 matrix | bullet lists |
| sequence, process, value chain | process flow / chevrons | numbered bullets |
| hierarchy or decomposition | tree, issue tree, driver tree | indented bullets |
| parallel categories | columns (MECE), equal width | uneven boxes |
| options against criteria | table with the recommended row highlighted | prose |
| a few headline numbers | KPI row (consult) or one big number per slide (keynote) | a table of 20 numbers |

Then:
- **Chart vs framework vs table.** Numbers with a pattern → chart. Structured ideas → framework. Exact lookup values the reader needs → compact table.
- **One question per exhibit.** Two relationships = two exhibits = two slides.
- **Comparison anchor:** target, benchmark, prior period or competitor. A number without a reference is just a number.
- **Opposite-title test:** if a reader could write the opposite title from this exhibit, the form or the highlight is wrong.

## 2. Finish: chart-to-message

1. The chart's message is the slide's action title; above the chart sits only a **unit line**: measure, scope, period, unit ("Gross margin by channel, FY2025, %").
2. **One highlight**: everything neutral grey, the element the title talks about in the single accent.
3. **Direct labels** on the data; delete the value axis and the legend where labels can sit next to bars or lines.
4. **Sort** bars by value unless order is the point (time, process).
5. **Reference line or anchor** (target, average, prior year) as a thin line or a labelled bar.
6. **One annotation** at the insight point: a short claim, thin leader line, accent colour, placed in white space. Two at most; more means split the exhibit.
7. **Strip chart junk**: gridlines, borders, background fills, 3D, shadows, gradients, redundant axis titles, decimals that do not matter.
8. **Value axes start at zero** for bars and columns.
9. Cover the title: does the chart still imply it? If not, fix the highlight or the data.

## 3. Data-ink

Every mark either shows data or helps read it. Inventory the marks, erase decoration first (shadows, 3D, gradients, heavy borders), then redundancy (gridlines when labels exist, legends when direct labels fit), then lighten what remains (thin axes, faint reference lines). Aim for ≥ 80% data ink. Reduce, do not amputate: keep the anchor, the one annotation and the labels that carry the message.

## 4. Frameworks

1. **Name the relationship** first (crossing dimensions → 2x2; sequence → flow; hierarchy → pyramid or tree; parallel parts → columns; maturity → stairway).
2. **Define axes and stages precisely.** A 2x2 needs both axes with a low-high meaning and all four quadrants named. Flow stages start with a verb and are MECE.
3. **Real content in every box:** one short line of substance, not just a label.
4. **One reading path:** left to right for flows, bottom to top for pyramids, a marked start quadrant for matrices.
5. **Highlight the conclusion:** the quadrant you are in, the broken stage, the layer that matters, in accent.
6. **Balanced geometry:** equal boxes for peers, even gaps, one corner style, everything on the grid.
7. **Arrows only for real flow or causation.**
8. **Say the so-what** in a callout if the framework is generic.

## 5. MECE layout of text content

List the items → pick one organising dimension (stage, function, region, cause, size, time) → test overlap and gaps → choose the shape (list, columns, 2x2, flow, tree) → order by logic (time, size, priority) → lay out top-left to bottom-right → add a spanning summary band if the groups ladder up to one point.

## 6. Numbers and labels

- Precision that matters: one decimal under 10, none above; percentages as "12%" not "12.38%".
- Units in the unit line, not on every label.
- Same category, same colour and name on every slide.
- Negative values in the negative colour only when sign is the message.
- Colour never carries meaning alone: pair it with a label (colour-blind readers).

## Output

Per slide: action title, chosen form and why (one line), highlight, anchor, labels kept and dropped, annotation text, junk removed, and the deck-craft helper call. Flag any exhibit that cannot support its title, and what data would.

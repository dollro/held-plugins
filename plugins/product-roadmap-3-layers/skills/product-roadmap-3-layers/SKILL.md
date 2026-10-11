---
name: "product-roadmap-3-layers"
description: "Builds or rebuilds a product roadmap in the 3-layer format (Business Outcomes, Product & Features, Tech Enabler) across Now/Next/Later as one markdown document; triages any input through an interview, or generates from and builds a Notion roadmap database. Use when building, restructuring, reviewing or presenting a roadmap, or for Now/Next/Later, outcome roadmaps, tech enablers or a roadmap slide. Not for a feature PRD (braindump2prd) or a vision (prfaq-vision-builder)."
---

# Roadmap in the 3-Layer Format

Version r10.10, 2026-10-06. `scripts/` and `references/` belong to this version and are updated
with it.

This skill produces one artifact: a markdown file that describes a roadmap completely and
ends with a fixed rendering instruction from which a downstream model builds the picture
(HTML, slide, image). The file is the source, the picture is derived.

The hard part is triage, not writing. Input is almost never in roadmap shape. Decide what is
an outcome, what is a visible feature, what is a technical prerequisite underneath it, and
what does not belong on a roadmap at all. Derive what is derivable, ask for the rest, invent
nothing.

Use whenever someone wants to build, restructure, review or present a product roadmap,
mentions Now/Next/Later, roadmap layers, tech enablers, outcome roadmap or a roadmap slide,
or hands over material (strategy papers, PRDs, backlogs, notes, braindumps) and asks what to
make of it.

**Language.** Everything is English: this skill, the document, and all content in it
(outcome sentences, card titles, descriptions, tables). Names of systems and artefacts keep
their proper names. Input may be in any language.

## 1 What this roadmap is

An ordered picture of intent: what should become possible for whom, what has to be built for
that, and in what order. **Time appears only as the period of each position and the order
inside it.**

It carries no dates, no capacity quotas, no OKR reconciliation, no commitment states and **no
progress**. When the order comes out longer than the period can carry, the picture has
produced a demand statement. That is a result worth writing down, not a defect.

It is not a PRD, a project definition or an issue list:

1. One sentence per card. A card that needs acceptance criteria is too granular.
2. No screens, endpoints, tickets, sprints, story points or person days.
3. A card names a result, a thing that exists, or a problem, never an activity.
4. The picture is the 3 × 3 grid with its labels and nothing else: one line per card.
5. 12 to 30 cards in total, at most five per cell. A cell is one position of one layer: a half of Now or Next, or Later (r10.3; before, the count ran per column).

Items below this line are routed, not deleted (scope boundaries, section 6 of the document).

**Shipped work leaves the roadmap.** It goes to the product changelog, not into a "done"
table. The document is rebuilt per version: it may carry unchanged content forward, but it
never records delivery. What already exists before the horizon starts is not history, it is
a building block with status `exists`.

**Boundaries.** This skill does not render the picture; that is a second job that follows the
document's rendering instruction. It does not invent evidence or building blocks; what did
not come from the material or the interview goes into the gap list. Depth on one feature
(acceptance criteria, error behaviour, data models, screens) belongs in a PRD via
braindump2prd; a card that needs one says `prd: yes` instead of carrying the detail.

## 2 Layers and columns

| Layer | Default row name | Guiding question | Content |
|---|---|---|---|
| 1 | Business Outcomes | Why are we doing this? | The party the value lands with acts, decides or concludes differently |
| 2 | Product & Features | What does the user get in their hands? | The artifact or property a user receives, named from the user's side |
| 3 | Tech Enabler | Which preconditions do we have to create? | The condition that must hold in the system so a layer 2 feature can exist |

Row names are defaults. A unit may rename a row to match what it actually holds (R11), for
example "Tech & Data Enabler" when most bottom-row cards are data work. The chosen names are
recorded in the context section and kept by later runs.

Column names are fixed:

| Column | Header | Meaning | Period |
|---|---|---|---|
| Now | In Progress | Solution decided, work running or starting next | The running quarter |
| Next | Investigating | Problem validated, solution open | The following half year |
| Later | Considering | Hypothesis, not yet assessed | Beyond that |

Column test, in order: is the solution decided? Now. Is the problem validated, and by what?
Next. Otherwise Later. "Important" answers neither question.

**Positions.** Now and Next are each split into a 1st and a 2nd half; Later is one position.
That gives five positions, each labelled with its absolute period, year first:

| Position | Meaning |
|---|---|
| `Now · 2026 Q4 · 1st` | First half of the running quarter |
| `Now · 2026 Q4 · 2nd` | Second half of the running quarter |
| `Next · 2027 H1 · 1st` | First half of the following half year |
| `Next · 2027 H1 · 2nd` | Second half of the following half year |
| `Later · 2027 H2` | Beyond that |

1st and 2nd are ordinals of the period's halves, an order, not a date. The periods in the
labels are rewritten when the horizon rolls forward. Avoid "earlier / later" as half labels:
"later" collides with the Later column.

**Every outcome belongs to exactly one column** and is cut so it can be reached there. A goal
that spills into the next column is split into two outcomes, each with its own evidence.

**Lead time.** An enabler whose work must start earlier than its outcome's column sits in the
column where the work starts and keeps its outcome's code and colour. The column rule binds
outcomes, not cards. The sequence section names every such card.

## 3 Triage cascade

Step 0: fix **whose roadmap this is** (which product, which users). The same statement is a
feature on the roadmap of the system that provides it and an enabler on the roadmap of
whatever consumes it. An item appears on one roadmap only.

Step 0b: fix **where the value lands**: outside (customer, prospect, partner, investor),
inside (the organisation), or mixed along the business processes. A single answer is recorded
once in the context section; "mixed" is recorded per outcome in the outcome table.

Then per raw item:

1. **Layer 1** if all four tests pass:
   - *Subject:* the party the value lands with, in a concrete situation (in the sales call, at
     the renewal). A colleague as subject is the mechanism: a layer 2 card, and the outcome is one
     question further out, "and what does that get us, with whom?"
   - *Name stripping:* delete every product and system name; the sentence still stands.
   - *No solution:* at least two different solutions could produce it.
   - *Evidence:* a metric with today and target, or one falsifiable observable criterion.
2. **Layer 2** if a user receives it and it can be written as a noun phrase. Internal users
   count; internal capability nobody outside the building team receives does not.
3. **Layer 3** if only engineers would see it. Then the **disappears test**: does the work
   vanish if the feature above it is cut? If not, `standalone: yes`. And: is it a decision a
   person must settle (approval depth, legal basis, policy)? Then `kind: decision`.
4. **None of the above:** constraint (context), assumption (gap list, marked), non-objective
   or too granular (scope boundaries). Do not force it onto the matrix.

**There are no technical outcomes.** Cost, stability and speed goals are layer 3 work under
the outcome whose feature they serve.

Common misfilings and the probe that resolves each:

| Raw phrasing | Usually is | Probe |
|---|---|---|
| "We need an agent framework" | Layer 3 | Which feature stops working without it? |
| "Better onboarding" | Outcome without evidence | Who does what differently, and how would you notice? |
| "The account manager can show X in the meeting" | Layer 2, outcome missing above | And what does that get us, with whom? |
| "Multi-tenancy", "migrate to X", "cut infra cost" | Layer 3, often standalone | Which feature or promise fails without it? |
| "Dashboard for partners" | Several features plus an enabler | Which decision does the partner make with it? One decision, one card |
| "AI-assisted X" | Feature plus an unnamed stack | What must exist before the first version can be shown? |
| A system name on its own | A building block, not a card | What changes for someone once it exists? |

If a probe yields "it just has to be there", it is an assumption, not a card.

## 4 Order

Order is carried by **positions** and by nothing else. Every card and every outcome carries
one of the five positions (section 2).

`precedes` is the one exception: work that must be finished before a specific feature
because it cannot be retrofitted (legal basis, access model, data model reference). Its
position must not be later than its target's.

**Outcomes are placed by hand**, in the half where they are reached. One check keeps outcome
and cards consistent: an outcome never sits in the 1st half when a card under it sits in the
2nd half of the same period. Lead-time cards in an earlier period do not count.

The format cannot order two cards in the same cell by itself. The order is derived from the
`depends_on` edges between building blocks, deepest first. Where two cards hang on the same
blocks, the author sets the order and the sequence section says so.

## 5 Building blocks

Five to nine components several cards depend on, **including those that already exist**.
Each carries `id`, `name`, `purpose`, `status` (`exists`, `partial`, `missing`), `used_by`,
`depends_on`. A block used by one card only is that card's enabler: delete it. More than
nine is an architecture drawing.

The statement which blocks are missing or partial, and what hangs on them, is mandatory.

## 6 Card fields

| Field | Mandatory | Format |
|---|---|---|
| `id` | yes | Stable, never reused, layer letter plus number: `O-1` outcomes, `F-1` layer 2, `E-1` layer 3. In Notion the number comes from the Unique ID for new cards, so numbers are unique but not gapless per layer |
| `title` | yes | Title grammar below. Quoted |
| `layer` | yes | 2 or 3 (outcomes live in the outcome table) |
| `position` | yes | One of the five positions, quoted |
| `outcome` | yes | Outcome code, quoted (`"O-1"`); on layer 3 derived from `serves` |
| `serves` | layer 3 | Feature IDs the enabler serves, all under one outcome |
| `standalone` | layer 3 | `yes` / `no`, disappears test |
| `kind` | layer 3 | `build` / `decision` |
| `desc` | recommended | One to two sentences: what is behind the card, in the vocabulary of the architecture. Shown in the detailed view of the picture, hidden in the compact view (layer 1: always shown). Quoted |
| `precedes` | only hard prerequisites | Target card ID |
| `blocks` | recommended | Building block IDs |
| `prd` | optional | `yes` if the card needs a PRD or project before it can start |
| `source` | recommended | Where it came from, or `interview`. Quoted |
| `linear` | optional | Linear project URL. Quoted |
| `confidence` | internal | `stated`, `inferred`, `open` |

Outcomes carry: `code`, `sentence`, `context` (one to two sentences of background, drawn on
the outcome card in small type), `value` (only when "mixed"), `evidence`, `type`
(`metric` or `criterion`), `today` and `target` (metrics only), `position`, `color`, and
`impact` (one or more impact dimensions). Sentence and context are two fields with two readers:
the sentence is executive language, impact first; the context is what someone needs to
understand what is behind it. The evidence never appears in the picture. A feature may have no
enabler.

**Impact dimensions.** A roadmap may define a small, fixed set of business dimensions (four to
six) that management steers by, for example Customer value, Efficiency, Revenue quality.
Each outcome names the dimensions it supports; the set and its one-line definitions are stated
once in section 1 and are never invented by this skill. An outcome that fits no dimension is a
finding, not a reason to add a dimension. Without a defined set the column is left out.

**YAML rule:** `title`, `desc` and `source` always in double quotes. An unquoted colon breaks
the block.

## 7 Title grammar

| Layer | Now and Next | Later | Max words |
|---|---|---|---|
| 1 | Full sentence, the external party as subject: what they do, decide or conclude. No product names | Same | 16 |
| 2 | Noun phrase: the thing the user gets. Could appear on an invoice | Same | 9 |
| 3 | State sentence in the present: the condition that must hold. Test: append "so that the feature above can exist" | Same form, no vendor names | 9 |

**Uncertainty belongs to the column, never to the sentence.** A Later card names its solution
in the same grammar as a Next card; the column header ("Considering"), the dashed card style and
the column's own definition carry the fact that it is a hypothesis. Up to r10 a Later feature was
written as the present deficiency ("A warm route cannot be found today"); r10.1 dropped that form
because it broke the reading for a management audience. Forbidden on every card:
"unclear whether", "to be checked", "possibly", "presumably", any question mark. Activity
nominalisations ("enrichment of the profile") are forbidden on every layer.

Two tests: a reader who knows the product but not the project understands the card in three
seconds without its description; and the person who gave the item recognises it.

### Register and length, per field

| Field | Layer 1 | Layers 2 and 3 |
|---|---|---|
| Title | Executive language, impact first: who gets what, and what changes. The system name may appear when it is the thing management knows (beacon, atlas), never as the subject | Layer 2: the thing the user gets, with its version where one exists ("atlas v2 (beta): …"). Layer 3: the condition, named in the architecture's own terms (HUB, RELAY, account profile, beacon-db-feed) |
| Description | One to two sentences of context: what is really behind the sentence, for the reader who needs it. Drawn on the card in small type, in both views | One to two sentences: mechanism, scope cut, or the card it mirrors or rests on. Drawn on the card in the detailed view only |
| Evidence | The falsifiable criterion or the metric. Never in the picture | — |
| Source | Where it came from: a person and date, a document and section, a Linear project | Same; architecture section numbers belong here, not in the description |

Rules that follow from it: no sentence in a description repeats the title; a description
over two sentences is cut, not softened; a reference to another card is by code ("the customer-side
counterpart of E-6"); "Hypothesis:" and "Problem:" prefixes are not used, the column carries
that; the person who gave the item is named in Source, never in the text.

## 8 Process

**Phase 0, intake.** A Notion roadmap database, when one exists, is the source of truth: the
document and the picture are generated by script along path A below, never written or drawn by
hand, and invariant violations are reported, not repaired. A finished roadmap markdown that
should become a Notion database goes along path B. Otherwise: documents (read everything
first), braindump (the common case), filled feature templates from braindump2prd (one file
usually yields one outcome candidate and two to four cards; success criteria become evidence,
"what this should not be" becomes non-objectives, edge cases mostly layer 3, references land
nowhere), an existing roadmap version (rebuild from it, gap-check, do not re-interview
settled points), material already in the conversation (gap-check only, mark inferences), or
nothing (go straight into the interview).

**Phase 1, inventory.** Extract candidates with their source, without judging. Record
contradictions side by side, never average them.

**Phase 2, self-classification.** Run the cascade and the column test. Tag each candidate
`stated`, `inferred` or `open`. Only `open` and risky `inferred` items go into the interview.
Never ask about what the material already says.

**Phase 3, interview.** One question per turn for thinking questions (target picture, whose
roadmap, value landing, each outcome and its evidence, goal cuts, contested scope). Bundled
proposals for bookkeeping (assignment, positions, enablers, blocks, titles). **Always
propose**, with the basis named. Aim for about nine exchanges:

1. Target state at the end of the horizon (a state, not features), whose roadmap, where the
   value lands, the horizon (which quarter is Now).
2. Outcomes, one at a time: who does what differently, and how would you notice. Never
   invent a number; a proposed criterion is marked `[SUGGESTED, confirm]`.
3. Goal cut, only where a goal does not fit its period.
4. Assignment of every card to one outcome (bundled). A card serving none: "what is this
   for?"
5. Position placement (bundled). Then **show the interim matrix as a table**.
6. Enablers per Now feature: what must be true, what breaks under load (`standalone`), what
   cannot be retrofitted (`precedes`), which are decisions (`kind: decision`). Then the block
   list: "which of these does not exist yet?"
7. Sequence: positions, lead time, the halves inside Now and Next (default: enablers in the
   1st half, features and outcomes in the 2nd), and "if only half of this happened, which
   half?"
8. Scope cut per contested item: stays, too granular, deliberately not, not this horizon.
   Ask what is already shipped (changelog) and what will honestly never be built.
9. Row names against the actual composition, then the full title list against the
   originals: "does each of these say what you meant?"

Stop when what is open is unimportant or needs someone not in the room. Open items go into
the gap list with an owner. Markers: `[ASSUMPTION, verify]`, `[NEEDS DECISION: <question>]`,
`[SUGGESTED, confirm]`. Never downgrade a decision into an assumption.

**Phase 4, write** the document per section 10 below. Copy
`references/rendering-instruction.md` verbatim as its last section.

**Phase 5, verify** with R1 to R12 and write every result into the check log, passed ones
included.

Save as `YYYY-MM-DD_Roadmap-<shortname>_vNN.md`; the picture uses the same stem
(`.html`, `.png`). The previous set moves to the archive folder; a published version is never
edited in place, a change is a new version.

### Notion path (deterministic)

When the roadmap lives in Notion, the document and the picture are generated by the scripts in
`scripts/`, never written by hand. Same input, same output. Standard library only; the PNG needs
Playwright with Chromium. If no script can run in the environment, say so and stop rather than
render by hand. **Read `references/notion-contract.md` before either path**: it defines the
database schema, invariants I1 to I9, which page sections are required and which optional, and
the Notion connector quirks.

**Path A, Notion → document and picture** (`scripts/render.py`)

1. Export the rows through the Notion connector with exactly the query in the contract and save
   the result list unchanged as `rows.json`. Never patch the export by hand; if something is
   wrong, fix it in Notion and export again.
2. Fetch the main roadmap page and its child page "Roadmap reference" and save each content
   (inside `<content>`) as `main.md` and `reference.md`.
3. Run `python3 scripts/render.py --rows rows.json --page main.md --page reference.md
   --version vNN --date YYYY-MM-DD --prev <previous vNN.md> --out <dir> --png`.
   It checks I1 to I9 and R1 to R12, reports incomplete rows and missing optional sections, and
   writes the md (rendering instruction included), the HTML and the PNG. It stops only when a
   required section is missing, and names it.
4. Report every finding in the chat. R4 grammar, R5 and R11 are logged as "checked by
   reading": read them before the version is released. The change list is a mechanical diff by
   ID against `--prev`; it states what changed, not why.
5. Numbers in the page prose (for example cards per outcome) are not recomputed. Compare them
   with the check log and name any that went stale.

**Path B, roadmap.md → new Notion database** (`scripts/parse_md.py`)

1. Run `python3 scripts/parse_md.py --md <roadmap.md> --out payload.json`. It reads the current
   format only (five positions, O-/F-/E- IDs); an older file is first rebuilt in this format.
   Report `findings`; the file is imported as it is, nothing is repaired.
2. Build database, rows, relations, the two pages and the views from the payload in the order
   the contract gives (section "Building a new database").
3. Generate the first version along path A as the check that the build is complete.

Notion rules for both paths: the cascade is one relation, Serves, on every layer (a feature
serves one outcome, an enabler serves features); no card below layer 1 carries a typed outcome.
New cards get their code from Notion's Unique ID; nobody types a number.
Select options are renamed in place, never deleted and re-added. The hex colour of an outcome
code is fixed once set, and a new outcome gets the next free code and a row in the colour table;
its Notion tag colour is derived by the "Outcome code" formula from the code number (r10.5), so
nothing in the formula is touched. The Notion page of a concrete roadmap names its data source and page
IDs; the skill carries none.

## 9 Check rules

A rule satisfied by a structural change rather than a change in substance (merging cards,
deleting an outcome) is logged as **"formally passed, finding in substance"**, and the finding
goes into the gap list.

| Rule | Check |
|---|---|
| R1 | Every card has an outcome |
| R2 | Every outcome has a metric with today and target, or a falsifiable criterion; the log says which |
| R3 | Every outcome has at least one card in its column or a column to its left |
| R4 | Title grammar per layer and column holds, word ceilings included |
| R4b | No card hedges |
| R5 | Every card passes the altitude test: one sentence, no screen, ticket or estimate |
| R6 | Cards per outcome do not increase left to right, counted before any merges in this run |
| R7 | No cell holds more than five cards; a cell is one position (half) of one layer |
| R8 | No outcome appears in more than one column (lead-time enablers are not a violation) |
| R9 | Every building block is used by at least two cards; every missing or partial block under a Now card is named in the gap list |
| R10 | Every card and outcome has a position; no `precedes` card sits later than its target; no outcome sits in a 1st half above a 2nd-half card of its own in the same period |
| R11 | Each row name matches the dominant kind of work in the row |
| R12 | Every outcome names at least one impact dimension, when the roadmap defines impact dimensions |

A deliberate departure from a rule is booked in the deviation register with reason and
**price**. Without the price it is an excuse list.

## 10 Document structure

Document sections 1 to 9 are case dependent; section 10 is the rendering instruction, copied
verbatim from `references/rendering-instruction.md`.

````markdown
# Roadmap: <product or unit>

As of <YYYY-MM-DD> · 3 layers × 5 positions · <Now period> · <Next period> · <Later period> ·
Audience: <who reads this> · Replaces: <previous file, if any>

## 1 Target picture and context

<Three to five sentences: the state at the end of the horizon, written as a state. Hard
constraints of the running period. Whose roadmap this is and who its users are. Where the
value lands. Row names in use. A short naming table if the unit has a naming convention.>

This roadmap orders intent, it commits to nothing. The periods place the work, 1st and 2nd
order it inside the period; neither is a date.

Basis: <documents, interviews, sessions with dates>.

## 2 Outcomes

| Code | Outcome | Context | Impact | Value | Evidence | Type | Position | Colour |
|---|---|---|---|---|---|---|---|---|
| O-1 | The key-account customer recognises in the sales call that the offer fits their goals | atlas v2 beta UI, opened by the account manager in the call | Customer value | outside | A sales call runs with the matching shown, without anyone building the list by hand | Criterion | Now · 2026 Q4 · 2nd | `#1F5E5B` |

<"Impact" only when the roadmap defines impact dimensions; then a list of outcomes per dimension
follows the table. "Value" only when the setting is "mixed". Add Today and Target columns only if at least one
outcome uses a metric. No two outcomes in one column with neighbouring hues.>

## 3 Cards

```yaml
cards:
  - id: E-1
    title: "Every key account has a profile with a status per product"
    layer: 3
    standalone: no
    kind: build
    position: "Now · 2026 Q4 · 1st"
    outcome: "O-1"
    serves: [F-2, F-5, F-1]
    desc: "One profile per account, with a status per product, lifted from the CRM as a running sync"
    precedes: F-2
    blocks: [B1, B3]
    source: "Architecture 5.27"
    confidence: stated
```

<Then one reading table per picture row: ID, Position, Outcome, Title, Flags. The row 3
table adds Remains (`standalone`) and Kind (`kind`), so a reader sees which enablers survive
a cut and which are decisions.>

## 4 Sequence

| Position | What comes into being | From then on |
|---|---|---|
| Now · 2026 Q4 · 1st | <what is built> | <what becomes possible; for 2nd halves this reads like an outcome sentence> |

**Outcome positions:** <per outcome in Now and Next the half it is placed in, and whether the
outcome check of R10 holds.>

<Then: lead-time cards (one line each, what they unlock and where), `precedes` pairs (one
sentence each on why first, or "none"), and any in-cell order set by the author.>

## 5 System building blocks

| ID | Block | Purpose | Status | Used by | Depends on |
|---|---|---|---|---|---|
| B3 | CRM | System of record for identity and process state | exists | E-1, E-2 | — |
| B2 | Evidence layer | Source, date and product on every statement | missing | E-1, E-3, E-5 | B1 |

<Below the table, two to four sentences: which blocks are missing or partial, what hangs on
them, and which is the heaviest item.>

## 6 Scope boundaries

**Too granular:** | Item | Belongs in | Level |
**Deliberately not:** | Non-objective | Reason (`strategy`, `solved_differently`, `not_viable`) |
**Deliberately postponed:** | Goal | Why not now | When again |

## 7 Demand from the sequence

<Two to four paragraphs derived from positions and blocks, not asked for: which profiles and
skills, where strands need the same people at once, which blocking items are decisions rather
than build work, what lies outside the unit, and where the order is longer than the period.
No headcount unless the user gave one.>

## 8 Open gaps

| Gap | Affects | Who can close it |
|---|---|---|

<Everything not in the material and not settled in the interview. Markers stay visible.>

## 9 Check log, deviations and changes

| Rule | Result | Note |
|---|---|---|

<All twelve rules.>

**Deviations:** | No | Deviation | Reason | Price | — or "none".

**Changes against <previous version>:** <a short list against the immediate predecessor
only, replaced in every version. Older history lives in the older files; the document does
not accumulate it.>

## 10 Rendering instruction

<references/rendering-instruction.md, verbatim.>
````

## 11 Rendering instruction

The instruction a downstream model follows to draw the picture is in
`references/rendering-instruction.md`. It is copied verbatim as section 10 of every document;
`render.py` does this itself. If a run finds that the instruction has to change, the change
belongs in that file, not in one document. Until then an altered instruction is a deviation with
its price. When the roadmap comes from Notion, `render.py` implements the instruction; a model
renders by hand only when no script can run, and says so.

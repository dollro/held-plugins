# Notion contract

Structure and logic of a roadmap kept in Notion, for skill `product-roadmap-3-layers` r10.5 (r10.4 plus the derived "Outcome code" formula). This
file holds no roadmap content and no IDs of a concrete database; those sit on the Notion page of
that roadmap.

Contents: 1 Principles · 2 Database · 3 Invariants · 4 Pages · 5 Views · 6 Workflow ·
7 Building a new database · 8 Connector notes

## 1 Principles

- Notion is the source of truth. Markdown, HTML and PNG per version are generated snapshots,
  never edited by hand and never synced back.
- One database, not three. The cascade is one relation, **Serves**, on every layer: a feature
  serves one outcome, an enabler serves one or more features.
- Nothing below layer 1 carries a typed outcome. A feature's outcome is the card it serves; an
  enabler's outcome is the outcome of the features it serves. The outcome code is the outcome
  row's own code.
- Stored properties are the contract for agents. Formulas are display only: the connector
  returns placeholders for their values.
- Order is one select, **Position**. Outcomes carry their own Position, placed by hand.
- Every card has a **code**: the layer letter plus a number (`O-1`, `F-45`). Notion's Unique ID
  **No** supplies the number on every new card, so nobody types or looks up a number. Cards that
  existed before the Unique ID keep their typed **ID** (for example `O-1` … `E-12`), which takes
  precedence. Codes are stable and never reused; numbers are unique across the database, not
  gapless per layer.

## 2 Database

### Stored properties

| Property | Type | Layer 1 | Layer 2 | Layer 3 | Meaning |
|---|---|---|---|---|---|
| Title | Title | outcome sentence | noun phrase | state sentence | Card text, title grammar per skill |
| No | Unique ID | set by Notion | set by Notion | set by Notion | Never typed; the number of the code |
| ID | Text | legacy only | legacy only | legacy only | Typed code of cards from before the Unique ID; empty on new cards |
| Layer | Select | `1 …` | `2 …` | `3 …` | Only the leading digit counts; the words are free labels for humans |
| Position | Select | yes | yes | yes | One of the five positions below |
| Serves | Relation to itself, two-way | empty | **exactly one outcome** | ≥ 1 feature | Counterpart: **Served by**; the whole cascade |
| Precedes | Relation to itself, one-way | empty | optional | optional | Hard prerequisite, target card |
| Blocks | Multi-select | empty | optional | optional | `B1` …, defined on the reference page |
| Standalone | Select | empty | empty | yes / no | Disappears test |
| Kind | Select | empty | empty | build / decision | |
| Value | Select | inside / outside | empty | empty | Only when the roadmap setting is "mixed" |
| Evidence type | Select | Criterion / Metric | empty | empty | |
| Impact dimension | Multi-select | ≥ 1 | empty | empty | Business dimensions the outcome supports; the options and their definitions are set per roadmap (main page, Context) |
| Description | Text | context, one to two sentences | desc, one to two sentences | desc, one to two sentences | Drawn on the card in small type: layer 1 in both views, layers 2 and 3 in the detailed view only (r10.4). Register per field: skill section 7 |
| Evidence | Text | evidence sentence | empty | empty | Criterion or metric; never in the picture |
| PRD | Checkbox | | optional | optional | |
| Source | Text | | | | Where the item came from |
| Linear | URL | | optional | optional | Linear project |

All content lives in properties; row page bodies stay empty.

**Export query** (path A, step 1):

```sql
SELECT url, Title, "userDefined:ID" AS ID, "No", Layer, Position, Serves, Precedes,
       Blocks, Standalone, Kind, Value, "Evidence type", "Impact dimension", Description, Evidence, PRD,
       Source, Linear
FROM "collection://<data source id>"
```

The code of a row is its ID if typed, otherwise the layer letter, a hyphen and No. A row
without Title, Layer or Position counts as a draft: `render.py` leaves it out and
names it in the check log. Relations to rows that no longer exist are dropped and named.

### Positions

| Option | Column | Half |
|---|---|---|
| `Now · <quarter> · 1st` | Now | 1st |
| `Now · <quarter> · 2nd` | Now | 2nd |
| `Next · <half year> · 1st` | Next | 1st |
| `Next · <half year> · 2nd` | Next | 2nd |
| `Later · <period>` | Later | — |

The label is parsed as `<Column> · <period> · <half>`; column headers and periods come from it.
When the horizon rolls forward, rename the options in place in the UI (the period part only).
Never delete and re-add options: the board's column order is manual, the connector cannot set
it, and re-created options land in the wrong order.

### Display-only formulas "Code", "Outcome code", "Serves (ID)" and "Served by (ID)"

**Code** shows the card's own code:

```
let(l, substring(format(prop("Layer")), 0, 1),
  if(empty(prop("ID")), ifs(l == "1", "O", l == "2", "F", "E") + "-" + format(prop("No")), prop("ID")))
```

"Outcome code" shows the outcome on every card, coloured by code: on an outcome its own code, on
a feature the code of the outcome it serves, on an enabler the outcomes two steps up. The colour
is derived from the code number (r10.5, 2026-09-28): a palette of 8 text and 9 background colours,
index `n mod 17`. Red is not in the palette and is reserved for a card that resolves to no outcome
or to two, which marks an I2 or I3 violation. No branch per outcome, nothing to maintain when an
outcome is added.

```
lets(l, substring(format(prop("Layer")), 0, 1),
  codes, ifs(l == "1", [prop("Code")],
             l == "2", prop("Serves").map(current.prop("Code")).unique(),
             prop("Serves").map(current.prop("Serves")).flat().map(current.prop("Code")).unique()),
  palette, ["gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink",
            "gray_background", "brown_background", "orange_background", "yellow_background",
            "green_background", "blue_background", "purple_background", "pink_background", "red_background"],
  if(codes.length() != 1, style(codes.join(", "), "b", "red"),
     lets(c, codes.first(), n, toNumber(replace(c, "^[A-Z]-", "")),
          style(c, "b", palette.at(mod(n, 17))))))
```

Two outcomes in one column can share a tag colour by chance (17 styles, numbers assigned by
Notion); the tag is a reading aid, the picture uses the hex table. Set through the connector with
`ALTER COLUMN "Outcome code" SET FORMULA('…')`.

**Serves (ID)** and **Served by (ID)** list the codes of the linked cards instead of their
titles: `prop("Serves").map(current.prop("Code")).sort().join(", ")`, likewise for Served by.
They are for reading the board; the generator does not use them.

### Outcome colours

Notion tag colours only approximate the roadmap palette; the exact hex values sit in the
colour table on the reference page and are used only by the renderer. An outcome without a row
there is drawn grey and reported.

**Adding a card:** create it, set Title, Layer and Position, and link it through Serves. Leave ID
empty; Notion sets No, and Code shows the result (for example `F-45`).

**Adding an outcome**, in addition: fill Value, Evidence type, Impact dimension, Description and Evidence; read its code from
Code and add a row with its hex colour to the colour table on the reference page. The Notion tag
colour needs no action.

## 3 Invariants

Checked from stored properties plus at most one Serves hop. Violations are reported, never
repaired silently.

| # | Invariant |
|---|---|
| I1 | A layer 1 row has no Serves |
| I2 | A feature has a Position and serves exactly one layer 1 row |
| I3 | An enabler has a Position and serves at least one feature; all served features serve the same outcome |
| I4 | A card never sits in a later column than its outcome (Now < Next < Later); an earlier column is lead time |
| I5 | A card with Precedes never sits in a later position than its target |
| I6 | Codes are unique; `O-` only on layer 1, `F-` only on layer 2, `E-` only on layer 3 (a typed ID with the wrong letter breaks this) |
| I7 | At most five cards per position and layer (R7): a half of Now or Next, or Later; a breach is a finding, booked in the deviation register |
| I8 | An outcome never sits in the 1st half when a card under it sits in the 2nd half of the same column; lead-time cards do not count |
| I9 | Every outcome has at least one Impact dimension (R12) |

A feature without an enabler is allowed. Position order: Now · 1st < Now · 2nd < Next · 1st <
Next · 2nd < Later.

## 4 Pages

The prose that is not a card sits on two pages, split by reader. The **main page** is read by
humans as it stands. Its child page **"Roadmap reference"** holds what is looked up. Each fact
sits on one page only.

**How the generator reads them.** `render.py` takes the main page first, then the reference
page, and collects `# ` sections by heading. A heading `<name> · details` continues section
`<name>` and is appended to it. Inline database and child-page tags are dropped. The basis line
is taken from after a `---` rule on the last page. Headings not listed below are ignored, so the
main page may carry sections of its own (a reading guide, for example). Layout does not matter:
toggle headings (`{toggle="true"}`), the indentation of toggle bodies, embeds and empty blocks
are stripped, `## ` subheadings on a page become `### ` in the document. Only the heading
**name** is the contract; a renamed section counts as missing and is reported.

| Section | Status | Usually on | Used for |
|---|---|---|---|
| Outcome colours | **required** | reference | Colours in HTML and PNG |
| System building blocks | **required** | reference | R9, missing-block note, document section 5 |
| Deviations | **required** | reference | Deviation register, breach check |
| Target picture and context (alias: Context) | optional | main, details on reference | Document section 1 |
| Sequence | optional | table on main, reasons on reference | Document section 4; reasons per precedes pair (`- **E-1 before F-2.** …`), `**Lead time.**`, `**In-cell order, row 3.**` |
| Scope boundaries | optional | reference | Document section 6 (`### Too granular`, `### Deliberately not`, `### Deliberately postponed`) |
| Demand from the sequence | optional | main | Document section 7 |
| Open gaps | optional | main | Document section 8; R9 checks that missing and partial blocks under Now cards are named here |
| Basis line | optional | after `---` on reference | Document section 1 |

A missing **required** section stops the generator with its name. A missing **optional**
section is marked "Not maintained in Notion for this version" in the document and reported in
the check log; nothing is generated in its place.

**Where new material goes:** a decision someone has to take or a risk to the plan → Open gaps;
a reason, definition, mapping or boundary → the reference page; structure, rules, agent
instructions → this skill; card content → the database, never a page.

The check log, the YAML block and the rendering instruction are never kept on a page; they are
produced per version.

## 5 Views

| View | Setup |
|---|---|
| Grid | Board, group by Position (manual column order, set once in the UI), sub-group by Layer (UI only), sort Layer then No; show Code and Outcome code |
| By outcome | Table sorted by Layer and No, showing Outcome code, Impact dimension, Serves (ID) and Served by (ID). Grouping by the formula is set in the UI if Notion offers it; the connector cannot set it |
| All | Plain table, every property |

Sorting by No follows creation order for new cards; cards with a typed ID got their No in no
particular order. The generator sorts by code number.

## 6 Workflow

1. **Edit** in the Grid: positions, layers, Serves on features and enablers, Position on
   outcomes.
2. **Generate a version** on request: path A of the skill. Write
   `YYYY-MM-DD_Roadmap-<shortname>_vNN.md`, `.html`, `.png` into the roadmap folder and move
   the previous set to the archive folder.
3. **Findings** go into the check log and are reported in the chat. Notion is not changed
   without being asked.
4. **Deviations:** the generator detects a breach (R4, R7); reason and price come from the
   Deviations table. A breach without an entry, or an entry without a breach, is reported.

## 7 Building a new database (path B)

From `payload.json` of `scripts/parse_md.py`, in this order:

1. Create the parent page, then the inline database with `payload.schema`; run
   `payload.ddl_after` with the new data source id for `{DS}`. The two-way relation Serves /
   Served by is created in one statement.
2. Create one row per entry in `payload.rows` (their codes go into ID); keep the map ID → page
   URL. Cards created later get their code from No; if a typed ID number is at or above the
   number of rows, a later No can repeat it, which the generator reports under I6.
3. Second pass: set Serves and Precedes from `payload.relations` with those URLs.
4. Write `payload.page` as the main page content, with the database tag in place of
   `{{DATABASE}}`, and create the child page "Roadmap reference" with `payload.page_reference`.
5. Create the views from `payload.views` and tell the user the steps marked `by_hand`
   (sub-group by Layer, column order on the board).

## 8 Connector notes

| Topic | Behaviour |
|---|---|
| Two-way self-relation | Create in one statement: `ADD COLUMN "Serves" RELATION('<ds>', DUAL 'Served by' 'served_by')`; two statements create duplicate columns |
| Formula values | Not readable: fetch and query return `formulaResult://` placeholders, and the formula text itself cannot be fetched (`formulaCode://` is refused); a view cannot be grouped by a formula through the connector. `ALTER COLUMN … SET FORMULA(…)` works, so a formula is replaced whole, never edited |
| Board grouping | Group by works; sub-group and group order are not in the view DSL |
| Select options | `ALTER COLUMN … SET SELECT(…)` replaces the option list and clears the property description unless `COMMENT '…'` is repeated; options with unchanged names keep their identity; changing an existing option's colour is refused; renaming an option this way re-creates it and clears its values, so rename in the UI |
| Page tables | `<table>` / `<tr>` / `<td>` markup; escape `[ ] < >` in text; fetched tables come without indentation |

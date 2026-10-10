## 10 Rendering instruction

This section addresses a language model that is to produce a picture from this document. It
is identical in all documents of this format. The data is in section 2 (outcomes), section 3
(cards), section 4 (positions) and section 5 (building blocks).

### What the picture is for

Management and the product unit use it to answer two questions: what is coming, and in what
order. It must work for a reader who does not know the architecture and was not in the
planning meeting. Anything that needs prior knowledge to decode is a defect of the picture.

The picture shows the plan, not the method: no entry criteria, reading hints, confidence
definitions, layer theory or deviation register. It carries no dates, no commitment states
and no progress. The only temporal statements are the periods in the column headers and
the order.

### One channel, one meaning

- **Background** belongs to the columns and carries confidence
- **Colour** belongs to the outcomes and carries assignment
- **Position** belongs to the sequence and carries order
- **Form** belongs to the rows and carries which way the work bears

A sign on a card (badge, pill, marker) is justified only where the grid does not already say
it. Putting a second meaning on an occupied channel destroys the first. If something needs
showing and every channel is taken, it stays out of the picture.

### The rows bear on each other

Row 3 carries row 2, row 2 carries row 1, and the picture shows this without a caption:
arrow shapes, interlocking edges, a bearing shadow or an upward narrowing at the row
boundary. Three rows that merely sit above each other show three lists.

### Basic layout

- Three rows, three columns, and a label column on the left of about a tenth of the width
- Rows top to bottom: layer 1, 2, 3, **with the row names and guiding questions given in the
  document**
- Columns left to right: Now, Next, Later
- Nothing below the matrix. The grid with its labels is the whole picture
- `standalone` and `kind` stay in the document and are not marked in the picture

### Column headers

Serif capitals: `NOW · IN PROGRESS`, `NEXT · INVESTIGATING`, `LATER · CONSIDERING`. Below, a
three-segment confidence bar (three, two, one filled), below that the period as written in the
positions (`2026 Q4`). In Now and Next a last line labels the two halves `1st` and `2nd`,
aligned with the halves of the cells. Nothing else.

### Order inside a column

Now and Next are each split into a 1st and a 2nd half by a thin dotted vertical rule, with a
thin unlabeled left-to-right arrow above the column. The halves are labelled once, in the
column header, never in the cells.

Every card sits in the half its position names. **Row 1 follows the same split**: each outcome
sits in the half its position names. An empty half inside one cell is correct (enabler in the
1st half, feature or outcome in the 2nd) and is neither collapsed nor padded.

**In row 3 the vertical axis inside a cell reads bottom to top**: lower cards are what the
cards above rest on. This holds within one outcome colour only, cards of one outcome are kept
contiguous, and it states a constraint, not a neighbour relation. The order comes from the
`depends_on` edges in section 5, deepest at the bottom; where section 4 says the author set
the order, follow it. The rule does not apply to rows 1 and 2.

Later has no positions; its cards stack at full width. A card sitting left of its outcome
(lead time) looks like any other card and carries its outcome's code and colour.

### Cards

Every card carries one line: its own code and the sentence. On layer 1 that is the outcome code
(`O-1`) and the full outcome sentence, on layers 2 and 3 the card's own code (`F-2`, `E-66`) and
the title (r10.10; up to r10.9 every card showed its outcome code instead). No position label.

Below that line, cards of layers 2 and 3 carry one small line in mono type naming what the
card serves, in codes: a feature `serves O-4`, an enabler `serves F-54 · F-56` (r10.6). It
shows in both views. On layer 2 it repeats the outcome code on purpose: the reader learns the
grammar in row 2 and reads row 3 the same way, where the codes are the only way to see which
feature an enabler stands under.

The picture has two views. **Compact**: no card carries its description; layer 1 keeps the
dimensions line. **With descriptions**: every card, layer 1 included, carries its description
in small type below the line (r10.7: one switch toggles all three layers). The HTML holds
both behind a switch in the masthead (compact by default; `#detail` in the URL opens the
detailed view); the image is exported twice, `<stem>.png` compact and `<stem>_detail.png`
detailed.

Layer 1 cards carry two further lines, both small. First, below a thin rule, the impact
dimensions the outcome supports (section 2, column Impact), separated by " · ", in the order
given there. Second, the outcome's context (section 2, column Context): one to two sentences in
a smaller, lighter type than the sentence, read by the person who needs the background and
skipped by the person who does not; like every description it shows only in the detailed view. The evidence never
appears in the picture. Cards of layers 2 and 3 never carry the dimensions line.

`precedes` is drawn as a small "ahead" pill **only when the target sits in a different
column or under a different outcome**. The pill names the target card by its code, "ahead of
F-1" (r10.10; before, it named the target's outcome code when that differed).

**Markers need a threshold.** If more than about a third of the cards would carry the same
marker (for example "missing block"), it goes on no card: it becomes one cell note, or stays
in the document.

### Colour

- Colour comes only from the outcome. Layer 1 cards: full outcome colour, white text, read
  first
- Row 2 and row 3 cards: the whole card filled with the outcome colour, tinted to about a
  fifth to a quarter of full strength. Not an edge, not a stripe
- White is reserved for a card with no outcome, which is a visible rule violation
- If section 2 names no colours, use in this order: `#1F5E5B` teal, `#B4622C` rust,
  `#3B4E8C` indigo, `#5E6B2F` olive, `#7A3F6B` plum, `#6E2B38` wine
- No two outcomes in one column with neighbouring hues
- Every card carries a code: its own on the code label, and on layers 2 and 3 the serves line.
  The outcome is read from the code on layer 1 and layer 2 (serves O-n) and by one hop on layer 3;
  together with the colour this is the fallback for greyscale and colour-blind readers and the
  link for lead-time cards

### Confidence

- Now: white cell background, solid border, cards with a light shadow
- Next: slightly tinted background, dashed border, no shadow
- Later: more strongly tinted background, dashed border, no shadow

### Cell notes

An empty cell carries one short italic line saying why it is empty. A filled cell may carry
one when the content itself is the finding. One sentence, only where the cards cannot say it.

### Styling

Warm off-white ground `#F7F5F0`, text `#1A1A18`, rules `#DDD8CC`. Grotesque for everything
except the grid labels. Column headers and row labels get the same treatment: serif,
capitals, letter-spaced, row labels smaller. A row label has three lines: "Layer n", the row
name, the guiding question in italic. If they do not fit, shorten the text, not the column.
No gradients, no shadows beyond the light one on Now cards. Proportions rather than pixels.

### Target formats

- **Web (default):** one self-contained HTML file, height to content, equal column widths,
  CSS grid per row, Google Fonts with a fallback stack
- **Slide:** one 16:9 slide, the same matrix with the same card fills. An overfull cell shows
  the most important cards and "+ n more". Nothing moves to a second slide
- **Image:** as the web version without interaction, SVG preferred

### What not to do

Do not invent cards, criteria or blocks not in sections 2 to 5. Do not add dates. Do not fill
an empty cell with something plausible. Do not change an assignment in the YAML block; a wrong
one is corrected in the document. Do not carry findings from section 9 into the picture. Do
not add a legend for something the picture should say by itself.

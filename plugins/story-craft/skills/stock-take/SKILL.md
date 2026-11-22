---
name: stock-take
description: Takes stock before any story is told - purpose (what the audience believes before and after), audience, the ask, which outputs are needed (keynote, film, teaser) with channel and runtime, an evidence inventory tagged solid / likely / missing, and an asset inventory (brand, product UI, recordings, voice, constraints) - through a short interview, one question at a time, importing a prfaq.md when one exists. Writes intake.md, the input for the narrative. Use for "stock-take", "what is the story", "before we make the deck / the video", "launch story", "Bestandsaufnahme", "Ziel der Präsentation", "worum geht es eigentlich". Not for building slides (deck-craft), writing a PRD (braindump2prd) or a vision press release (prfaq-vision-builder).
license: MIT
---

# stock-take

Before a story is shaped, know what it must achieve and what it can stand on. This skill interviews the owner and writes `intake.md`: purpose, audience, outputs, evidence, assets. The narrative is built on that file; a deck or film made without it tends to invent its proof.

## When to use

- A launch, keynote, pitch, vision talk or product film is coming and no `intake.md` exists yet.
- Someone asks for "the story" or "the deck" or "the video" and the purpose, audience or evidence is unclear.
- Skip it if `intake.md` already exists and is current: read it, confirm in one line, hand on to the narrative.

## Sources first, questions second

1. Look for source documents in the working folder and ask once which ones count: `prfaq.md` (from prfaq-vision-builder), PRD, interview notes, survey results, analytics exports, an existing deck, `design-guide.json` (from deck-craft:deck-design-guide).
2. If `prfaq.md` exists, import from it: the user and their problem → Audience, plus a villain candidate under Story hints; the most important benefit → a promise candidate under Story hints; "how do you know" and the FAQ's metrics → evidence rows. Only ask what it lacks.
3. Pre-fill every field you can from the sources and mark it `(from <file>)`. Before question 1, show the pre-filled fields in one message; the owner confirms or corrects them in one pass, and the interview then skips what is settled.

## Interview

Run it as a conversation. **One question per message**, in this order, skipping what the sources answer. Reflect each answer back in one line before the next question. `references/interview.md` has the wording, follow-ups and what a good answer looks like.

1. **Purpose**: what does the audience believe now, and what should they believe afterwards? One sentence each. Push past "they should know about X" to a belief.
2. **Ask**: the one action wanted after (sign up, approve budget, start a pilot, buy). One action.
3. **Audience**: who, in a role and situation; their week; the words they use for the pain. Split decision maker and user if they differ.
4. **Outputs**: which pieces are needed, each with channel, runtime and whether a speaker is present. Typical: keynote (live, 10-20 min), film-60 (landing page, no speaker), teaser-20 (social, muted autoplay). Name each output with a short ID; the narrative reuses it as a cut.
5. **Evidence**: for each claim the owner wants to make, what supports it, from where. Tag strength (below). Ask for the number behind every "faster", "cheaper", "more".
6. **Assets**: brand (design guide or master, logo, fonts), product (live UI with a test account, click path, screen recordings, product images), voice (speaker or VO language and voice, music constraints).
7. **Constraints**: legal lines, claims not allowed, deadline, budget for generated footage.

Seven topics, no more: a topic may take a follow-up or two (and the brand lock below adds up to four questions), but do not open new topics. If an answer is missing, write `open: <what is missing>` in the field and move on; do not invent.

## Evidence strength

| Strength | Means | Allowed use later |
|---|---|---|
| `solid` | measured or documented, source named (survey with n, analytics, signed customer quote, benchmark with test conditions) | any claim, as stated |
| `likely` | credible but thin (a few interviews, an internal estimate, a pilot with one customer) | claim with softened wording or qualifier |
| `missing` | wanted but nothing behind it yet | no claim; either find evidence or drop or weaken the claim |

Give each row an ID (`E1`, `E2`, …). IDs are stable: never renumber, only append. The narrative and its validator reference them.

One row per claim. Several pieces of evidence for the same claim (three interview quotes, say) share one row; the strength is that of the whole.

Never upgrade strength because a claim sounds good. A number the owner "is sure about" without a source is `likely` at best. Quotes must be real and attributable; a paraphrase is not a quote. Attribution by role and company type ("site manager, mid-size builder") is fine if the owner knows who said it and the person agreed to be quoted; note that in Source.

## Brand without a design guide

If there is no `design-guide.json` and no master, run a short brand interview after question 6 (four questions, in `references/interview.md` § Brand lock): colours with roles, fonts, logo files, never-do list. Record the answers under Asset inventory. Motion work reads them as its brand lock.

## Output: intake.md

First read back a five-line summary (purpose, ask, audience, outputs, evidence count by strength) and ask "Anything wrong or missing?". Fix, then write `intake.md` in the working folder from `assets/intake-template.md`. The template's rows in `<angle brackets>` or marked `e.g.` are examples: replace or delete them. Rules:

- every section present, even if a field says `open: <what is missing>`;
- one row per claim, with ID, claim it could support, evidence, source, strength;
- outputs listed with ID, channel, runtime, speaker yes/no;
- Story hints only from sources or the owner's own words; leave it empty rather than invent;
- close with **Open points**: each `open:` field and each `missing` evidence row, with who could close it.

Then hand on: "Next: the narrative (story-craft:narrative) reads this file." If the narrative skill is not installed, say that deck-craft:deck-keynote can work from `intake.md` directly.

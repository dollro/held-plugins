# Output scaffolds & FAQ question banks

The exact structures to produce. Adapt wording to the user's language; keep the shape.

---

## Output scaffold — the single vision document

Produce ONE document in this order. Press release on top (prose), lean FAQ below, optional open-questions list at the end.

```
# [Product name] — Vision Document (Working Backwards PR/FAQ)
*Future-state draft for discussion — written as if [Product] has already shipped. Not a real press release. Iterate freely.*

---

## Press Release

**[Headline — what it does, in one line a real user would say]**
*[Sub-headline — who it's for and the single core benefit]*

[CITY / TEAM], [future date] — [Summary paragraph: the whole vision in miniature. A reader should grasp what this is and why it matters from this paragraph alone.]

[Problem paragraph: the painful before-state, concrete and specific. What the user struggles with today.]

[Solution paragraph: how [Product] works, in plain language. The problem it removes, how it removes it, and why the user cares. Jargon-free.]

"[Internal/leadership quote: why this matters to the organization — the strategic 'why now'.]" said [Name, role].

"[User quote: how it changed their day, in their own voice.]" said [Name, role of the user].

[Call to action: how a user gets started today.]

---

## FAQ

[Use the scope-appropriate question set below. Keep answers tight — a few sentences each. Be candid about risk. Capture unknowns as open questions, never as fabricated certainty.]

**[Q1] …**
…

**[Q2] …**
…

(continue — aim for ~2 pages max)

---

## Open questions & assumptions to validate
*(Optional — the things this vision is betting on that aren't yet proven.)*
- …
- …

## Mockup / storyboard
*(Optional — if the product has a UI or a multi-step flow, note here that a visual would clarify it, or describe the key screen/flow in one line.)*
```

---

## FAQ question bank — INTERNAL scope (tool for the team's own use)

Pick the load-bearing ones; don't ask all of them. The starred ones are near-mandatory.

- ★ **What problem does this solve, and what do we do today instead?** (the honest-competition question — name the current manual process / existing tool)
- ★ **Why would a teammate actually switch from the current way?** (behavior change)
- ★ **What does this deliberately NOT do?** (scope discipline — guard against over-building)
- ★ **What has to be true for this to work?** (assumptions & dependencies)
- ★ **Is it feasible given our constraints?** (time, our stack, data access, who builds/maintains it)
- ★ **How will we know it's working?** (one primary success metric)
- Who owns it after launch? Who maintains it?
- What's the smallest first version that's still useful (the thin slice)?
- What breaks or gets risky at scale / with more users?
- If it touches sensitive or internal data: where does the data live, who can see it, what are the security/privacy implications?
- What's the cost (build time, ongoing, tokens/compute if relevant) vs. the time it saves?

Skip for internal scope: pricing, go-to-market, external PR, market sizing.

---

## FAQ question bank — EXTERNAL scope (product for customers/market)

- ★ **What problem does this solve, and how do customers deal with it today?** (real competitors + status-quo behavior)
- ★ **Why will customers switch / change behavior to use this?**
- ★ **What makes it different from the alternatives?** (differentiation / why it wins)
- ★ **What does it deliberately NOT do?** (scope)
- ★ **What has to be true for this to succeed?** (key assumptions, biggest risks)
- ★ **How will we measure success?** (primary metric)
- What's the business model / how does it make money / pricing posture?
- How much does it cost the customer? When and where can they get it?
- How do customers find it and get started? (go-to-market, in brief)
- Is the market big enough to justify building this?
- Is it feasible given our constraints (tech, team, time)?
- Is customer data safe? (privacy/security, where relevant)
- What's the smallest launchable version (MVP) and what comes after?

---

## Worked micro-example (INTERNAL scope) — for calibration only

*Headline:* "Deal triage that's done before the coffee's cold."
*Sub-headline:* For analysts screening inbound decks under time pressure — a first-pass evaluation in two minutes instead of forty.

*Summary:* [TEAM], next quarter — The deal-screening assistant turns a raw pitch deck into a structured first-pass brief in under two minutes. Analysts who used to spend half a morning reading and reformatting now open a finished, consistent brief and spend their time on judgment instead of transcription. …

(This is a calibration example of tone and shape, not content to copy. Always build from the user's actual five-question answers.)

---

## Reminders while filling the scaffold
- PR is **prose, present tense, future-state, jargon-free**. FAQ may be structured.
- Never attribute an invented quote to a real, named person — use representative names/roles.
- Never fabricate a metric or evidence. Unknown → goes in "Open questions & assumptions."
- One document. PR ≤ 1 page. FAQ ≤ ~2 pages. If it won't fit, consider whether there are two distinct users → two linked PRs.
- Mirror the user's request language throughout.

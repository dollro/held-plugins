---
name: story-review
description: Reviews a narrative.md before anything is built from it - runs the contract validator (one reveal, one star, a close in every cut, evidence behind every claim beat), the one-sentence test, a so-what pass per beat, a credibility pass on the proof ledger and a four-person expert panel with a scorecard - and appends a PASS or REVISE verdict with beat-level findings. The gate that deck-craft and motion-craft check before building. Use for "is the story good", "tear the story apart", "review the narrative", "Story prüfen", or after story-craft:narrative. Not for reviewing a finished deck (deck-craft:deck-review) or a rendered film (motion-craft:motion-qa).
license: MIT
---

# story-review

A story fixed in words is cheap to change; a story fixed in slides or rendered frames is not. This skill reviews `narrative.md` and appends a verdict. Downstream skills (deck-keynote, motion-director) read the verdict: motion work starts only on PASS.

Review as a reader who did not write the narrative. If you wrote it in this session, say so in the verdict and be harder on it, or hand the review to a fresh subagent with only `narrative.md` and `intake.md`.

## Gate order

Run the steps in order; a failing step does not stop the later ones, but the verdict is REVISE if any step fails.

### 1. Validator

```bash
python <plugin>/scripts/validate_narrative.py narrative.md      # intake.md next to it
```

Needs PyYAML. Every ERROR is a finding. Read the WARNINGs: a 60-second cut with 12 beats is a pacing problem the panel should weigh. Without Python (PowerPoint add-in, chat), check by hand: unique IDs, one reveal, one star, ≥ 1 villain, one close, a villain + reveal + close in every cut ending on the close, evidence `solid` or `likely` behind every proof, cost and versus beat.

### 2. One-sentence test

Write the whole story in one sentence without looking at the beats: who suffers what, what changes, what to do. Then compare with the headline and promise. If you cannot write it, or it differs from the headline, the narrative has no spine: finding on the headline.

Then read only the beat statements, top to bottom, as one paragraph. They must tell the story without the lines. A statement that does not advance it marks a beat that may not belong.

### 3. So-what per beat

For each beat ask "so what?" from the audience's chair. A beat passes if the answer is in the audience's words and moves them toward the after-belief. Typical failures: a feature with no benefit, a number with no comparison, a pillar that repeats another, a moment the audience does not recognise.

### 4. Credibility

Walk the proof ledger against `intake.md`:
- every claim cites evidence; `likely` evidence has softened wording ("in our pilot", "about");
- no number is derived beyond the source ("6.2 → 1.4 h" is not "4× faster" unless the owner states it);
- quotes are verbatim and attributable; comparisons name the benchmark;
- nothing the intake lists under "Claims not allowed" appears anywhere, including the spoken lines.

### 5. Expert panel

Run the panel in `references/panel.md`: four reviewers, each with a lens and three questions, scoring five dimensions. Each reviewer gives at most three findings, each tied to a beat ID. Keep their voices distinct; the skeptical buyer is the one most often right.

## Verdict

**PASS** when the validator has no errors, the one-sentence test holds, no beat fails so-what or credibility, and the panel average is ≥ 3.5 with no dimension below 3. Otherwise **REVISE**.

Append to `narrative.md` under `## Review` (replace an older review, keep its date in one line):

```markdown
## Review

Verdict: PASS | REVISE · <date> · reviewer: <fresh agent / author>
One sentence: <the story in one sentence>
Validator: <n errors, n warnings>

| Beat | Step | Finding | Fix |
|---|---|---|---|
| B10 | credibility | "9 in 10" from a 14-person pilot reads as general | add "in our pilot" to the statement |

Panel: <scorecard table from references/panel.md>
```

On REVISE, offer to apply the fixes in narrative (keeping beat IDs), then review again. On PASS, hand on: "Next: deck-craft:deck-keynote for the keynote, motion-craft:motion-director for the films."

# Cuts

One narrative, several outputs. The master is the longest output with every beat (usually the keynote). Each shorter output is a cut: a subset of the master's beats, in the same order, with its own runtime. Cuts share beat IDs, so a film clip for B12 can play on the keynote's B12 slide.

## Compressing the master

1. Keep the spine: a hook (`moment` or `villain`), the `reveal`, the payoff (`star` or `outcome`) and the `close`. Every cut has a `villain`, the `reveal` and the `close`.
2. Drop from the middle first: second and third proof, objections, the versus if the star already shows before and after, the voice.
3. Then reduce the pillars: in a film one or two pillars can stand for three if the star demonstrates the rest. Never show two of three numbered pillars.
4. The `cost` stays if the cut has room for one number; it is the most retold beat after the reveal.
5. Never reorder beats inside a cut; never add a beat that is not in the master. If a cut needs a beat the master lacks, add it to the master (new ID) and decide whether the keynote uses it.

## Budgets

| Output | Runtime | Beats | Per beat |
|---|---|---|---|
| keynote (live) | 10-20 min | 12-20 | 30-60 s spoken |
| film-90 | 90 s | 10-14 | 6-8 s |
| film-60 | 60 s | 8-10 | 5-7 s |
| film-30 | 30 s | 5-6 | 4-6 s |
| teaser-20 | 20 s | 4-5 | 3-5 s |
| teaser-6 | 6 s | 1-2 | the hook and the name |

The validator warns when film-60 has more than 10 beats or teaser-20 more than 5.

## No-speaker cuts

Films on a landing page and teasers in a feed are watched without a presenter, often muted:
- **hook in 2 s**: the first beat shows the need (the evening pile, the waiting bar) or the product already working on something recognisable; never a logo or black;
- **text carries the claim**: the beat statement appears on screen, ≤ 6 words a line; the screen never repeats the voice-over word for word;
- **voice-over optional**: if used, it is the beat's `line`, shortened; the story must still work muted;
- **end card**: the close holds 2-3 s with name and the ask.

## One language per narrative

A narrative is written in one language. Another language is a separate translated `narrative.<lang>.md` with the same beat IDs, not a second column; downstream tools pick one file.

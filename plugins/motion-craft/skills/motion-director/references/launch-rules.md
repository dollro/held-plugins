# Launch film rules

Rules for every cut a motion-director film makes from `narrative.md`. They apply from the direction options to the last polish round.

## 1. Medium per beat role

The medium is the frame's lead picture. `mixed` = two picture sources share the frame (generated hands and a composited real screen, footage under a quote). Type on top never changes the medium. `check_storyboard.py` warns when a frame breaks this table.

| Role | Allowed media | How |
|---|---|---|
| villain | generated, motion, mixed | the pain made visible in the audience's own setting; the count or object in type |
| moment | generated, motion, mixed | a person, a place, a time stamp; no product yet |
| outcome | generated, motion, mixed | the new state of their week, the promise come true; the same person as the villain frame |
| reveal | motion | the product name, set in the brand heading font, then silence; not the end-card logo |
| pillar | motion | the idea as motion graphics (tiles folding, a path drawing); never a fake product screen |
| proof | ui, mixed | the real product showing the result; the number in type with its fine print |
| star (demo) | ui, mixed | a real screen recording of the real flow, never a mockup; a placeholder labelled "Screen recording: …" until it exists |
| cost | motion | one number, large, counted in; fine print from the proof ledger |
| versus | motion | old and new in the same unit, side by side or swapped in place; one number each |
| voice | motion, mixed | the quote in type over a still or footage; attributed by role; never a generated face saying it |
| turn | motion | the question in type, built word by word |
| objection | motion | the answer in type, one line per doubt |
| close | motion | end card: the brand mark lands once, the ask and the URL hold |

`mixed` on a proof or star frame means the real UI leads; motion type, crops and punch-ins sit around it.

## 2. No-speaker cuts

Films on a landing page and teasers in a feed play muted, without a presenter.

- **Hook in 2 s**: frame 0 is the thumbnail; the need is already visible (the pile, the waiting bar) or the product is already working on something recognisable. Never black, never a logo alone, never a typing prompt box as the opener.
- **Text carries the claim**: the beat statement is on screen, ≤ 6 words a line. The screen never repeats the VO word for word.
- **VO optional**: if used, it is the beat `line`, shortened, written to `SCRIPT.md`. The film must still work muted.
- **End card**: the close holds 2-3 s at least with the name and the ask; the mark arrives during the final 5-10% of the runtime.

## 3. Brand-lock use

- **Colours** only from brand-lock. The **hero** colour is rationed: one element per frame (the key word, the number, the CTA, the mark). Grounds are flat brand colours.
- **Fonts** from the `font_files` listed. No files: stop before the animated test and ask; never fall back to a system font in a render.
- **Logo** from the logo file, never redrawn, recoloured or stretched, with clear space of its own height. It **lands once**, with weight, on the end card. The reveal sets the product name in type; it is not the logo.
- **Safe margin** from brand-lock on every side; nothing important outside it. Keep the bottom 17% clear of lines in films for social feeds (platform overlays).
- Anything brand-lock lists under "Never" stays out.

## 4. Credibility

- **Claims only from the narrative's proof ledger.** No number, quote or comparison the ledger does not hold. A number that would help but is not there goes back to story-craft.
- **Fine print on screen for every number**: the ledger's wording (sample, period, test, self-reported). On screen long enough to read (≥ 2.5 s), above the safe margin, in the body font.
- **Likely evidence keeps its qualifier** ("Pilot:", "in our tests").
- **Quotes** verbatim, attributed as in the intake (role, not invented names). A generated person never speaks a real person's words.
- **Real UI, never a mockup.** Rearranging real pieces to explain a result is fine; inventing a screen, button or dashboard is not. A feature with nothing visible gets the actual screen where it surfaces, a familiar real-world comparison, or a labelled placeholder.
- **Generated footage** shows situations, never the product's screen, readable text or a logo; screens are composited from real recordings.

## 5. Tells of a generic film

Each one is banned unless the brand's own material does it. After every render, name the ones that slipped in and fix them.

- a dark navy void with small things floating in the middle;
- glow, bloom, lens flares, particles, orbs as decoration;
- purple or blue gradients, glass cards, mesh backgrounds (unless the brand uses them);
- every element fading and sliding up; everything arriving at once;
- titles that keep drifting or scaling after they land; floating "breathing" loops;
- three feature cards side by side; a metrics grid; a headline laid on a darkened screenshot;
- a logo parked in a corner throughout;
- a typing prompt box as the opener;
- an invented dashboard or a mockup phone with fake data;
- the same seam at every cut;
- frame borders, corner brackets, HUD readouts, "01 / 02" labels as decoration.

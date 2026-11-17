# Pre-flight Gate

Run before handing the uplift to coding agents (Step 6). If a box can't be ticked honestly, the uplift is not done: fix, state in one line what changed and why, re-run.

## Measured (uiux-visual-review on design/targets/)

- [ ] `review.mjs run` on the target prototypes at mobile and desktop (and dark, if the product has it) and `review.mjs check` passes with the default thresholds: 0 off-token colours and font sizes, 0 off-grid spacing, 0 axe serious, 0 targets below 24px, no horizontal scroll, 0 missing focus.
- [ ] `filled_actions` ≤ 1 on every default state.
- [ ] Uplift mode: `review.mjs compare` of MVP vs targets shows no regression the PM hasn't accepted.

## Vision (rubric on the targets)

- [ ] Every place scored; no axis below 3. Distinctiveness scored against the locked direction.
- [ ] Pairwise vs. the MVP audit: better on hierarchy, consistency and state quality, or the reason why not is recorded.
- [ ] The places sheet passes the identity lock: all screens read as the same product.

## Identity lock

- [ ] `DESIGN.md` Overview and Art Direction written; tokens updated in DTCG and regenerated; DESIGN.md matches the tokens (`design:check`).
- [ ] One accent, one radius scale, one icon family, one type pairing, one easing curve, one copy voice.
- [ ] The signature appears where planned and nowhere else.
- [ ] No reflex default without a written reason (`reflex-defaults.md`).
- [ ] Inspiration recorded as took/rejected; no single reference cloned.

## Coverage

- [ ] Every breadboard place has a screen spec; every place that carries a must-job has a target prototype.
- [ ] Every state in every breadboard States table is specified with copy.
- [ ] Responsive re-composition specified for every place below 768px.
- [ ] Every affordance (`U#`) maps to a component variant that exists or is listed as new.

## Cognitive load

- [ ] ≤ ~5 top-level navigation items; ≤ ~4 fields per form group; exactly one primary action per view.
- [ ] Each screen spec names exactly one "first" in its hierarchy.

## Sign-off

- [ ] PM reviewed the targets (sheets or artifact) and signed off in `design/UPLIFT.md` with the date.
- [ ] Open taste questions listed as known risks, not silently decided.

# Comparison Rubric

Hierarchical diff procedure. **Process categories in order — do not skip ahead.** A structure mismatch invalidates downstream analysis; fixing a color on an element that shouldn't exist is wasted work.

## Category 1: Structure

**Question:** Are all elements from the target present in the implementation, and vice versa?

Check for:
- Missing elements (target has X, impl does not)
- Extra elements (impl has X, target does not)
- Wrong element type (target uses a `<button>`, impl uses an `<a>` styled as a button — affects accessibility, not just visuals)
- Wrong containment (element exists but nested under the wrong parent)

**How to check with Claude's vision:**
Walk top-to-bottom through the target image. For each visually distinct element, verify it exists in the impl. Then reverse: walk the impl and verify every element traces back to the target.

**Severity mapping:**
- Missing primary CTA, form field, navigation item → `blocker`
- Missing secondary element (helper text, icon) → `major`
- Extra decorative element → `minor`

**Do not confuse structure with layout.** "Button exists but is on the wrong side" is a layout delta, not a structure delta. If the element exists anywhere in the viewport, it passes structure.

## Category 2: Layout

**Question:** Are elements in the right position, and do they flow/wrap/align correctly?

Check for:
- X/Y position shifts beyond 4px
- Width/height mismatches beyond 8px
- Flex/grid ordering (same elements, different order)
- Alignment (left/center/right, top/middle/bottom)
- Spacing (gap, padding, margin)
- Wrapping behavior (single line vs multi-line)
- Overflow (clipped content, unintended scrollbars)

**How to check:**
Use the pixel-diff output to find regions with changes. For each region, zoom in and compare positions. Where possible, read computed styles from DevTools via Playwright's `evaluate()` for ground truth — vision is good at "this shifted" but exact spacing values come from the DOM.

**Severity mapping:**
- Element hidden, off-screen, overlapping another element → `blocker`
- Position off by >16px or alignment wrong → `major`
- Position off by 4–16px → `minor`
- Position off by <4px → `cosmetic` (usually subpixel rendering; often not fixable)

## Category 3: Typography

**Question:** Do text elements match in font, size, weight, and leading?

Check for:
- Font family (and fallback chain)
- Font size (rem/px)
- Font weight (400 / 500 / 600 / 700)
- Line-height
- Letter-spacing
- Text-transform (uppercase, capitalize)
- Text-decoration (underline, strikethrough)
- Text color (also checked in Category 4, but log under typography when it's a heading/body contrast issue)

**How to check:**
Extract computed styles for the key typographic slots — headings, body, captions, buttons, links — and compare. This is more reliable than pure vision for font-weight deltas (400 vs 500 can look identical to vision but breaks hierarchy).

```js
// In Playwright evaluate
const h1 = document.querySelector('h1');
const styles = getComputedStyle(h1);
return {
  fontFamily: styles.fontFamily,
  fontSize: styles.fontSize,
  fontWeight: styles.fontWeight,
  lineHeight: styles.lineHeight,
  letterSpacing: styles.letterSpacing,
};
```

**Severity mapping:**
- Wrong font family (not in fallback chain) → `major`
- Font-size off by >2px or wrong scale step → `major`
- Font-weight delta ≥ 200 (e.g. 400 vs 700) → `major`
- Font-weight delta of 100 (e.g. 400 vs 500) → `minor`
- Line-height delta causing visible line wrap changes → `major`
- Line-height delta below wrap threshold → `minor`

## Category 4: Color

**Question:** Do colors match perceptually?

Check for:
- Background colors
- Text colors
- Border colors
- Shadow colors
- Gradient stops

**Use ΔE, not hex diff.** Two colors with different hex codes can look identical. Two colors with similar hex codes can look different. ΔE (CIE Delta E 2000) measures perceptual distance.

- ΔE < 1 — imperceptible to the human eye, ignore
- ΔE 1–2 — perceptible only on direct comparison, `cosmetic`
- ΔE 2–10 — perceptible at a glance, `minor` or `major` depending on element
- ΔE > 10 — clearly different colors, `major` or `blocker`

**Quick ΔE calculation in Node:**

```js
import chroma from 'chroma-js';
const dE = chroma.deltaE('#1e40af', '#1d3fb0');
// 0.4 — imperceptible
```

**Severity mapping:**
- Primary brand color wrong (ΔE > 5 on logo, primary button) → `blocker`
- Text-on-background contrast failure (WCAG AA violation) → `blocker`
- Secondary color wrong (ΔE > 5) → `major`
- Shadow/border color off (ΔE 2–10) → `minor`

## Category 5: Micro

Everything else that affects perceived polish but isn't in 1–4:

- Border radius
- Shadow depth (x, y, blur, spread)
- Icon style and size
- Hover/focus states (requires interaction — often out of scope for initial parity run)
- Transition timing
- Cursor type on interactive elements

**Severity:** Usually `minor` or `cosmetic`. Upgrade to `major` only if it's a recognizable brand element.

## How to apply the rubric

1. Open all three images side by side: target, impl, diff.
2. Walk through the **categories in order**. For each, populate a list of deltas.
3. For each delta, fill: category, severity, description, region, suggested_fix, files.
4. Sort the final list: severity (blocker → cosmetic), then by category order within severity.
5. Emit `deltas.json`.

## What vision is good at vs. bad at

**Good at:**
- "Is this element present?"
- "Is this element in the right place?"
- "Does the overall composition match?"
- "Is this color clearly different?" (ΔE > 10)

**Bad at:**
- Exact spacing values ("is this 16px or 20px?")
- Small font-weight differences (400 vs 500)
- Small color shifts (ΔE 1–3)
- Border radius differences under 4px

**Rule:** When the question is "exactly how much?", use computed styles from the DOM. When the question is "does this look right?", use vision. Use both in the same delta when you can — the vision observation is the "what" and the computed-style read is the "how much".

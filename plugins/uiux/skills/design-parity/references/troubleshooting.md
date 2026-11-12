# Troubleshooting

Failure patterns in the parity loop, in order of how often they come up.

## "Every pixel is different" — environmental drift

### Symptoms
- `diffPercentage > 30%` on first run
- Diff image is a solid red or nearly uniform sea of noise
- Both target and impl "look fine" to the eye

### Causes and fixes

**Viewport mismatch.** Target rendered at 1920, impl at 1440. Check `.parity/<screen>/target_metadata.json` and impl viewport — they must match exactly.

**DPR mismatch.** Target at DPR=1, impl at DPR=2 (common on retina displays during development). Force `deviceScaleFactor: 1` in `screenshot.mjs`.

**OS font stack.** Target rendered on Linux CI runner, impl screenshotted on macOS. Fonts render differently. Fix: load explicit web fonts in both, or run the impl screenshot in the same Docker container as the target. Playwright Docker images are stable across host OSes.

**Font not loaded in time.** `document.fonts.ready` was not awaited. Fix: the stabilization step in `workflow.md` covers this.

## "Diff flips between states on identical runs" — animations

### Symptoms
- Same screen, same code, different diffs on repeated runs
- Specific regions (often hero sections, charts) shift between runs

### Causes and fixes

**CSS animations still running.** The `animation-duration: 0s` override missed some. Check for animations declared via JS (`element.animate()`) or Web Animations API — those ignore CSS overrides. Fix:

```js
await page.evaluate(() => {
  document.getAnimations().forEach(a => a.finish());
});
```

**Intersection-observer-triggered fades.** Elements fade in when scrolled into view, and scroll timing varies. Fix: the scroll-through step in `workflow.md` handles most cases, but stubborn cases need:

```js
await page.evaluate(() => {
  // Force all fade-in elements to fully visible
  document.querySelectorAll('[class*="fade"]').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'none';
  });
});
```

**Autoplay video/GIF.** Mask the region or replace the source with a static frame.

## "Claude keeps fixing color but breaks layout"

### Symptoms
- Iteration 1 fixes font, iteration 2 fixes color, iteration 3 breaks spacing
- Convergence oscillates instead of improving

### Cause
Rubric category order was not respected. Claude was shown a messy delta list without severity ordering.

### Fix
Enforce the category order in the loop:
1. Apply ALL structure fixes before touching anything else
2. Re-screenshot, re-diff
3. Apply ALL layout fixes
4. Re-screenshot, re-diff
5. Apply ALL typography fixes
6. ...and so on

This is slower per iteration but converges more reliably.

## "Computed styles match perfectly but the diff still flags pixels"

### Symptoms
- Extracted CSS shows `font-size: 24px` on both sides, same font-family, same weight
- Diff still shows red on the text
- Zooming in shows what looks like identical text

### Cause
Subpixel rendering differs between runs due to:
- Different GPU/rasterization path
- ClearType / anti-aliasing settings
- Text hinting mode

### Fix
- Run odiff with `--antialiasing true` (default in `diff.mjs`) — this filters out AA-only pixels
- Set `text-rendering: geometricPrecision` globally during screenshot via the stabilization stylesheet
- Accept a higher threshold for text regions (4% pixel diff on text is often acceptable)

## "Target HTML renders differently than the Claude Design preview"

### Symptoms
- User says "but it looks right in Claude Design!"
- Target PNG rendered from HTML doesn't match the Claude Design canvas

### Cause
Claude Design's canvas runs in a sandboxed iframe with specific CSS defaults. Exported HTML may reference those defaults implicitly.

### Fix
- Check the exported HTML for `<link>` tags to external stylesheets that may not resolve locally
- Check if the export used relative image paths that break outside Claude Design
- Re-export with "Include all assets" option if available
- If still broken, fall back to PNG target and accept the limitation

## "Skill ran once, worked great, now keeps saying 'converged' but looks wrong"

### Symptoms
- First run: good deltas, useful fixes
- Subsequent runs: always reports converged even though visible differences remain

### Cause
Threshold set too loose, or masks are covering legitimate content.

### Fix
- Check `.parity/<screen>/masks.json` — did any mask expand to cover too much?
- Lower convergence threshold from `0.5%` to `0.1%`
- Manually review the most recent `diff.png` — if it shows red and the skill says converged, thresholds are wrong

## "Dev server returns different HTML depending on viewport"

### Symptoms
- Mobile viewport impl screenshot differs from desktop in ways that suggest totally different component trees
- Cannot meaningfully diff mobile target against desktop impl

### Cause
Responsive implementation uses conditional rendering (not just CSS media queries) based on user agent or window width.

### Fix
- This is correct behavior, not a bug. Run separate parity loops per breakpoint.
- Target HTML must also be the mobile export, not the desktop export resized.

## "The suggested fix references files that don't exist"

### Symptoms
- Delta says "Edit src/components/HeaderActions.tsx line 42"
- That file doesn't exist, or line 42 is unrelated

### Cause
Vision-based fix suggestions are hypothetical. The skill doesn't know the codebase structure until it reads it.

### Fix
Add a codebase scan before the first vision pass:

```bash
# Let Claude read the component structure first
find src -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" | head -50
# Then the suggested_fix field can reference real paths
```

A better pattern: after vision produces a delta, do a second pass where Claude searches the codebase for the referenced element (e.g. searches for "Filter" button) and updates the `files` array in the delta with real paths.

## When to bail out of the loop entirely

Hard stop conditions — tell the user and wait for direction:

- Convergence not achieved after 5 iterations AND `diffPercentage` has not decreased in the last 3
- Vision analysis returns contradictory deltas on consecutive runs (instability)
- A "fix" would require modifying shared design tokens that affect untested screens
- Target HTML cannot be rendered locally (external deps broken)
- Implementation has dynamic content that can't reasonably be masked (e.g. entire dashboard is live data)

Bailing out is not failure. The skill is for closing gaps, not forcing convergence on a fundamentally different design.

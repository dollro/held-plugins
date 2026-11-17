# Inspiration Intake

Reference sites inform the direction; they never become it. Take principles, not pixels.

## Procedure per URL (1 to 4 sites)

1. Extract measured DNA (no guessing from memory or the URL):
   ```bash
   node <uiux-visual-review>/scripts/review.mjs dna https://example.com --out design/inspiration/example
   ```
   Writes `dna.md` (families, font sizes, weights, text and surface colours, radii, shadows, spacing rhythm, alignment lines, motion), `dna.json`, `first-screen.png`, `full.png`. Add `--viewport 375x812` for mobile, `--scheme dark` for dark mode.
2. Look at the screenshots with the numbers: what creates the feeling the PM liked? Usually 2 or 3 things (a type scale with large contrast, tinted neutrals, a dense table with fine rules, restrained motion).
3. Write one DNA line: "example.com: tight tracking, near-mono palette, 13/15/20 type scale, hairline rules instead of cards, no shadows."
4. Record took and rejected:
   ```markdown
   - example.com: took hairline rules and the compact type scale; rejected the all-caps labels and the purple accent.
   ```
5. Synthesis line across all references, proving the result is not one site reskinned.

Login-protected references: ask for screenshots instead and read values off them roughly; say that they are estimates. Sites that block automation: same. Never bypass bot protection.

## Rules

- Cross-blend 2 to 4 references; the brief beats all of them.
- Reflex defaults in a reference are not inherited (`reflex-defaults.md`).
- Never copy logos, illustrations, icons, copy or proprietary fonts. A licensed font the reference uses can be proposed if the product can license it too.
- If the PM names a competitor as the reference, extract what users of that product value and differ deliberately in the signature.

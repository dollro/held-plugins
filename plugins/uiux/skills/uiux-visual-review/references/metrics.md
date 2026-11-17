# Measured Layer: What Each Number Means

All metrics are computed from the browser's computed styles after fonts load, animations freeze and lazy content scrolls in. Lower is better for every number in the gate. "Example" columns in `report.md` name the first element found (`tag.class "text"`), enough to grep the codebase.

## Token conformance

| Metric | Measures | Usual cause | Fix |
|-|-|-|-|
| `off_token_colors` | Text, background and border colours that match no colour token (RGB distance > 3) | Hard-coded hex in a component; unstyled browser defaults (`rgb(0 0 0)` text in a bare `<button>`); a missing token such as text-on-action | Use the mapped token; add the missing token to the semantic or mapped tier (`uiux-design-system`); style the bare control through the component library |
| `near_token_colors` | Colours within distance 20 of a token but not equal | Hand-typed approximation (`#2f6fd0` for the primary) | Replace with the token. Near misses are the clearest sign of drift |
| `off_token_font_sizes` | Font sizes that match no length token | `14.5px`, browser default `13.33px` on form controls, one-off headings | Map to the type scale; set `font: inherit` on form controls |
| `off_token_radii`, off-token shadows | Radii and shadows outside the token set | Per-component values | One radius scale and one elevation set |

Token sources: `css` reads custom properties defined in the page's stylesheets; restrict with `prefixes` or every framework variable counts as a token. `dtcg` reads colour and dimension tokens from the files. Colours are compared in sRGB after the browser converts them, so OKLCH tokens work. Alpha is ignored for matching: `bg-primary/10` counts as on-token.

False positives: colours inside third-party widgets (put them under `ignore:`); images and canvas are not measured.

## Rhythm and alignment

| Metric | Measures | Fix |
|-|-|-|
| `off_grid_spacing` | Padding, gap and vertical margins not on the `grid` (default 4px). Margins on fixed/absolute layers, `<dialog>` and values above 160px are skipped (centring, not rhythm) | Spacing tokens only |
| `alignment_near_misses` | Two left alignment lines 1 to 3px apart, each used by 2+ elements: things meant to line up that don't | Same container padding; remove stray margins; align text, not boxes |
| `alignment_lines` (info) | Distinct left edges used by 2+ elements | Fewer lines read calmer; dense data UIs need more |

## Type and colour sprawl

| Metric | Default limit | Note |
|-|-|-|
| `font_sizes` | 8 per capture | Product UIs rarely need more than 6 sizes on one screen |
| `font_weights` | 4 | Two or three weights carry most hierarchy |
| `font_families` | 3 | Display, body, mono at most. The family is the declared first one; check the screenshot that the web font actually loaded |
| `colors_distinct` (info) | none | Compare runs, not absolute |
| `saturatedFillShare` (info) | none | Share of page area in saturated fills. Restrained product UIs sit below ~0.1; a committed direction can be higher by design |

## Focus of the view

`filled_actions` (default limit 1, default state only): primary-looking actions per view. With `primary_action` configured it counts that selector; otherwise saturated filled buttons. Two equal primaries split attention: demote one to secondary. A list with a primary button in every row is a design smell; move the action to the row's hover or a toolbar.

## Accessibility and robustness

| Metric | Measures |
|-|-|
| `axe_serious` | axe-core rules of impact serious or critical (WCAG 2.0/2.1/2.2 A and AA tags). Runs per capture, so dark mode contrast is checked separately |
| `targets_below_24` | Interactive elements smaller than 24px in either direction (WCAG 2.2 AA floor). Inline text links are exempt |
| `targets_below_44` (info) | Below the 44px comfortable size; matters on touch viewports |
| `missing_focus` | Tab stops (first `focus_stops`, default state, widest viewport) where focused and blurred styles are identical: no visible focus indicator |
| `horizontal_scroll` | Page wider than the viewport: almost always a fixed width or a long unbroken string at 375px |
| `tiny_text` | Text below 12px |
| `truncated` (info) | Text cut by overflow or ellipsis. Often intended; check that the full value is reachable (title, tooltip, detail view) |
| `console_errors` (info) | Errors while rendering; mocked 500s produce one by design |

Axe and focus measure the whole page even when `scope:` limits the other metrics to a dialog.

## Motion and perceived speed

Measured live, before animations freeze.

| Metric | Measures | Fix |
|-|-|-|
| `overshoot_easing` | Transitions with a cubic-bezier that leaves 0..1 (bounce, elastic) or a `linear()` spring curve | One named easing curve for UI; overshoot only where the direction calls for it |
| `slow_transitions` (info) | Transitions longer than 500ms | UI feedback 100 to 300ms |
| `infinite_animations` | Animations running forever in a settled, non-loading state. Loading states (`hang` mocks, `capture_after_ms`) are exempt | Stop decorative loops; spinners only while loading |
| reduced motion (info) | Animations still running with `prefers-reduced-motion: reduce` | Wrap motion in the media query |
| `cls` | Cumulative layout shift during load | Reserve space: skeletons with final dimensions, image sizes, no late banners |
| LCP (info) | Largest contentful paint on the dev server | Relative between runs only |

## Thresholds and the ratchet

Defaults live in `scripts/lib/config.mjs` and are overridden in `review.config.yaml → thresholds` (set a key to `null` to switch it off). With `review.baseline.json` present, the limit per capture and metric is `max(threshold, baseline)`. Refresh the baseline after each improvement so the gain is locked in.

Tune limits to the product, not to pass: a dense analyst workspace may need 7 font sizes; it never needs off-token colours.

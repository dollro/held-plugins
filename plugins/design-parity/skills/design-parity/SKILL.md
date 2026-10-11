---
name: design-parity
description: "Compares Claude Design exports (HTML or PNG) against a running frontend, produces a ranked delta report and applies fixes until they match, driven by a committed parity.config.yaml and Playwright MCP, Chrome DevTools MCP or a bundled Node runtime. Use for \"compare to the design\", \"match the spec\", \"design parity\", \"why doesn't my implementation match the mockup\", or when Claude Design exports sit next to a running dev server."
---

# Design Parity

## What this skill does

Close the gap between a Claude Design spec (target) and its implementation (actual) through a repeatable compare-and-fix loop. Produces a ranked delta report — not just pixel diffs — and applies fixes hierarchically (structure before style). The full run is driven by a single committed `parity.config.yaml`, so the same command works on a dev machine, in CI, and inside an MCP-assisted agent session.

## Core loop

```
┌───────────────────────────────────────────────────────────┐
│  1. Prepare target  (HTML → rendered PNG, or PNG as-is)   │
│  2. Screenshot impl (running dev server, same viewport)   │
│  3. Pixel diff      (odiff finds WHERE things differ)     │
│  4. Vision analysis (Claude explains WHAT and WHY)        │
│  5. Rank deltas     (by perceptual impact, not pixel count)│
│  6. Emit fix_plan   (operable edits, not advice)          │
│  7. Apply + re-run  (goto 2 until converged or accepted)  │
└───────────────────────────────────────────────────────────┘
```

Every iteration writes to `.parity/runs/<screen>/iteration_N/`. The loop is resumable and reviewable.

## Prerequisites

1. **Target exports** — HTML (preferred; same rendering stack = fewer false positives) or PNG.
2. **A running dev server** reachable at the URL in `parity.config.yaml → base_url`.
3. **A `parity.config.yaml`** — scaffold with `parity init`. Never guess routes; the config is the contract.
4. **Viewport** — default `1440×900`. For PNG targets, viewport auto-matches the PNG dimensions unless `--strict`.

If anything is missing, ask one clarifying question. Do not guess routes.

## Runtime adapters

The skill dispatches browser ops through one of three adapters. Set in `parity.config.yaml → runtime:` (default `auto`):

|-|-|
| `auto` | detect: MCP playwright → MCP chrome-devtools → node-playwright |
| `node-playwright` | bundled Node runtime (needs local `npm install`) |
| `mcp-playwright` | emit an ordered MCP tool-call plan; the calling agent executes it |
| `mcp-chrome-devtools` | same, targeting Chrome DevTools MCP |

Signal MCP availability to the skill via env:

```bash
export PARITY_MCP_PLAYWRIGHT=1         # or PARITY_MCP_CHROME_DEVTOOLS=1
```

Stabilization steps (fonts, animations, lazy scroll, masks) are identical across adapters — they're expressed as an IIFE that each runtime runs as-is. See `references/runtimes.md`.

## Commands

```bash
parity init                       # scaffold config, rubric, .parity/.gitignore
parity auth                       # headless login per config.auth block
parity run [--screen <id>] [--strict]
parity plan [--screen <id>]       # emit MCP plan (for runtime: mcp-*)
```

All commands read `./parity.config.yaml` by default; override with `--config`.

## Config (excerpt)

```yaml
runtime: auto
base_url: http://localhost:3000
viewport: [1440, 900]
auth:
  mode: form                      # form | cookie | storage-state | none
  login_url: /login/
  fields:
    "#login-username": ${env:SS_EMAIL}
    "#login-password": ${env:SS_PASSWORD}
  success_match: "/\\/app\\//"
  storage_state: .parity/auth.json
screens:
  - id: dashboard
    path: /dashboard
    target: targets/dashboard.html
    requires_auth: true
  - id: settings
    path: /app/settings/
    target:
      html: targets/canvas.html    # multi-screen canvas export
      selector: "#settings-main [data-screen]"
    mask:
      - ".save-status-chip"
      - { region: [1100, 20, 140, 24] }
      - { text: "/\\d{1,2}:\\d{2}|ago|today/i" }
    requires_auth: true
fixtures:
  first-session:
    seed: node scripts/seed.mjs --user testuser --sessions 3
```

Full schema in `references/parity.config.example.yaml`; rubric overrides in `parity.rubric.example.yaml`.

## Why HTML targets beat PNGs

When the target is a PNG, every "difference" is filtered through two different rendering stacks (Claude Design's vs. the user's browser). Font metrics, subpixel rendering, and DPR all diverge → false positives that aren't real bugs.

When the target is HTML, we render it in the **same browser, same viewport, same DPR** as the implementation. The only remaining differences are real. Always prefer HTML when available.

## Masks — three kinds

```yaml
mask:
  - ".save-status-chip"                         # selector shorthand
  - { selector: "[data-fresh-date]" }           # selector explicit
  - { region: [x, y, w, h] }                    # opaque rectangle overlay
  - { text: "/timestamp-regex/i" }              # replace matching text nodes with spaces
```

Regex-text masks are essential for "11:42 AM" / "2 hours ago" strings that change every run but aren't tied to a single selector.

## Fixture seeding

Some screens require populated data. Declare fixtures; they run before screenshots:

```yaml
fixtures:
  first-session:
    seed: node scripts/seed.mjs --user testuser --sessions 3
    path_params:
      session_id: ${env:FIXTURE_SESSION_ID}
    teardown: node scripts/seed.mjs --cleanup
```

Path templates (`/app/transcripts/{session_id}`) substitute `path_params` before navigation.

## Viewport / PNG-dim handling

- HTML target: viewport comes from config (default 1440×900).
- PNG target: viewport auto-matches the PNG dimensions. An explicit override is warned about, not blocked — unless `--strict`.
- Never resize the target or impl — interpolation poisons the diff.

## Vision analysis

Load `target.png`, `impl.png`, and `diff.png` into context. Apply the rubric (`references/rubric.md`, overridable via `parity.rubric.yaml`) in this order:

1. **Structure** — missing, extra, or miscontained elements.
2. **Layout** — positions, alignment, spacing, flex/grid order.
3. **Typography** — family, size, weight, line-height, letter-spacing.
4. **Color** — fill, border, shadow (ΔE threshold).
5. **Micro** — radius, shadow depth, iconography.

Write two files per iteration:

- `deltas.json` — ranked findings with category, severity, region, description.
- `fix_plan.json` — concrete `replace` / `patch` / `delete_lines` / `insert_after` / `note` ops an operator (human or agent) can apply directly. See `references/fix-plan.md`.

## Thresholds (defaults)

|-|-|
| Metric | Threshold |
| Pixel threshold | `0.1` (odiff default) |
| Antialiasing filter | `true` |
| ΔE color threshold | `2.0` |
| Convergence | `< 0.5%` diff AND zero blocker/major |
| Max iterations | `5` before asking user |

All overridable in `parity.rubric.yaml`.

## Apply → re-run

Process deltas in severity order (`blocker` → `major` → `minor` → `cosmetic`), then by category (structure first). Batch related fixes before re-screenshotting — post-per-fix captures are slow and obscure which edits worked.

Stop when **any** of:
- `diffPercentage < 0.5%` AND no blocker/major deltas
- User says "accept"
- Three iterations without meaningful improvement (ask user)

## Common failure modes

Top three — see `references/troubleshooting.md` for the full list:

1. **Every pixel different** — viewport, DPR, or font stack mismatch. Check the three values; web fonts not system fonts.
2. **Diff flips between states** — animations. `disable-animations` is on by default; check intersection-observer fade-ins.
3. **Claude fixes color but breaks layout** — wrong category order. Always process `structure` + `layout` before `color`.

## Constraints

- Never start servers. The dev server URL must already be reachable.
- Never edit target files. Targets are source of truth; only the implementation changes.
- Never resize images to force a viewport match.
- Never delete `.parity/`. It's the audit trail and the dependency cache.

## Output to user

After each iteration, print a concise summary (not the full JSON):

```
Iteration 2 of dashboard:
  Pixel diff:  2.3% → 0.8% (improved)
  Blockers:    1 → 0
  Major:       4 → 2
  Minor:       7 → 5

Remaining major:
  1. Sidebar collapse padding (4px too tight)
  2. Card shadow offset (target y=4, impl y=2)

Next: apply 2 fixes in fix_plan.json, re-run. ETA: 1-2 iterations.
```

Full JSON to `.parity/runs/<screen>/iteration_N/{deltas,fix_plan}.json`.

## Related files

- `references/workflow.md` — detailed config-driven procedure
- `references/runtimes.md` — adapter selection, MCP plan shape, stabilization JS
- `references/rubric.md` — hierarchical comparison rubric with examples
- `references/fix-plan.md` — fix_plan.json schema and guidance
- `references/parity.config.example.yaml` — full config schema with comments
- `references/parity.rubric.example.yaml` — rubric override schema
- `references/troubleshooting.md` — false-positive patterns and fixes
- `scripts/parity.mjs` — unified entry point (run / plan / auth / init)
- `scripts/screenshot.mjs` — stabilized Playwright helper (selector, region, text masks)
- `scripts/diff.mjs` — odiff wrapper emitting structured JSON

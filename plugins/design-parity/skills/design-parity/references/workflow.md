# Workflow Reference

Config-driven procedure. Read this when the main SKILL.md summary isn't enough.

## 0. One-time setup

```bash
# In the project root
node /path/to/skill/scripts/parity.mjs init
#   → parity.config.yaml, parity.rubric.yaml, .parity/.gitignore
```

Edit `parity.config.yaml`: set `base_url`, the auth block, and the `screens` list. Commit the config + rubric. `.parity/` is gitignored — it holds runs, cached auth, and node_modules.

Install tooling once:

```bash
cd .parity && npm init -y && npm install --save-dev \
  /path/to/skill/scripts odiff-bin pngjs playwright yaml
```

(The `scripts/` directory is an npm bin — `npx parity run` works once installed.)

## 1. Authenticate (non-interactive)

```bash
npx parity auth
```

Runs the `auth:` block from config headlessly — fills login fields, clicks submit, waits for `success_match`, persists `storage_state`. Re-run after expiry. For `mode: cookie` or `mode: storage-state`, this is a no-op validation.

Legacy interactive flow (humans only, not usable in agent loops):

```bash
node scripts/screenshot.mjs --auth-setup --url http://localhost:3000/login
```

## 2. Run the loop

```bash
npx parity run                  # all screens, next iteration number
npx parity run --screen settings
npx parity run --strict         # fail on viewport/PNG-dim mismatch instead of auto-matching
```

Artifacts land at `.parity/runs/<screen>/iteration_N/{target,impl,diff}.png + run.json`.

## 3. Non-node runtimes (MCP)

If the calling agent has a Playwright MCP or Chrome DevTools MCP server connected, set one of:

```bash
export PARITY_MCP_PLAYWRIGHT=1
export PARITY_MCP_CHROME_DEVTOOLS=1
```

Then:

```bash
npx parity plan --screen dashboard > plan.json
```

Feed `plan.json` into the agent's tool-use loop — it executes `steps[]` in order via MCP. After the plan emits `impl.png` and `target.png`, run `diff.mjs` locally to finish:

```bash
node scripts/diff.mjs --base .parity/runs/dashboard/iteration_1/target.png \
                       --compare .parity/runs/dashboard/iteration_1/impl.png \
                       --out     .parity/runs/dashboard/iteration_1/diff.png
```

See `runtimes.md` for adapter details.

## 4. Stabilization — the most important section

Flakiness comes from environmental noise mistaken for design drift. Every screenshot — target and impl, node or MCP — passes through identical stabilization:

1. Lock viewport + DPR. DPR=1 is default; use 2 only when targeting retina specifically.
2. Disable animations + transitions via `*{animation-duration:0}` init script.
3. `page.goto(..., { waitUntil: 'networkidle' })`.
4. `await document.fonts.ready`.
5. `document.getAnimations().forEach(a => a.finish())`.
6. Scroll full page height (triggers lazy images + intersection observers), scroll back to top.
7. Settle 400ms.
8. Apply masks.
9. Capture.

Never adapt stabilization per screen — it defeats the purpose.

## 5. Targets

### Full HTML file
```yaml
- id: dashboard
  path: /dashboard
  target: targets/dashboard.html
```

### PNG export
```yaml
- id: landing-hero
  path: /
  target: targets/landing-hero.png     # viewport auto-matches PNG dims
```

With `--strict`, a viewport override that disagrees with the PNG fails the run. Without `--strict`, we auto-match and warn.

### Canvas-with-many-screens HTML
One HTML export, many screens laid out on a canvas. Use the selector form:

```yaml
- id: settings
  path: /app/settings/
  target:
    html: targets/canvas.html
    selector: "#settings-main [data-screen]"
```

`screenshot.mjs --selector` captures only that subtree via `page.locator(sel).screenshot()`.

## 6. Masks

Three kinds, combinable per screen:

```yaml
mask:
  - ".save-status-chip"                              # selector shorthand
  - { selector: "[data-fresh-date]" }                # selector explicit
  - { region: [1100, 20, 140, 24] }                  # x, y, w, h in viewport px
  - { text: "/\\d{1,2}:\\d{2} ?(AM|PM)|ago|today/i" } # regex across text nodes
```

- **Selector**: `visibility: hidden` (preserves layout).
- **Region**: opaque black rectangle overlay at top of z-stack.
- **Text**: walk text nodes, replace matching content with spaces before capture. Use for timestamps, relative times, countdown tickers that live inside larger elements.

## 7. Fixtures

Populated states often need seeding. Declare a fixture; it runs before the matching screens are captured.

```yaml
fixtures:
  first-session:
    seed: node scripts/seed.mjs --user testuser --sessions 3
    path_params:
      session_id: ${env:FIXTURE_SESSION_ID}
    teardown: node scripts/seed.mjs --cleanup

screens:
  - id: transcript-detail
    path: /app/transcripts/{session_id}
    target: targets/transcript-detail.png
    fixtures: [first-session]
```

## 8. Rubric overrides

Reference a `parity.rubric.yaml` from config. See `parity.rubric.example.yaml` for the full schema. Common overrides: ΔE threshold, ignore-below-Npx for typography, border-radius noise floor, ignore-regions for always-live areas.

## 9. Vision analysis + deltas

After the diff, load `target.png`, `impl.png`, `diff.png` into Claude's vision. Apply the rubric in category order:

1. Structure
2. Layout
3. Typography
4. Color
5. Micro

Write two files per iteration:

- `deltas.json` — what's wrong (for humans)
- `fix_plan.json` — what to change (for an operator/agent; see `fix-plan.md`)

Convergence = `diffPercentage < 0.5%` AND zero blocker/major deltas.

## 10. Artifact layout

```text
parity.config.yaml             # committed
parity.rubric.yaml             # committed
parity/fixtures/               # committed — seed helpers
.parity/                       # gitignored
  .gitignore
  auth.json                    # storageState
  node_modules/                # bundled runtime deps
  package.json
  runs/
    <screen>/
      iteration_N/
        target.png
        impl.png
        diff.png
        run.json
        deltas.json
        fix_plan.json
```

Old iterations prune automatically when `artifacts.keep_iterations` is exceeded.

## 11. When to stop and ask the user

Stop and ask before:
- Making structural changes (adding/removing components) beyond what the rubric permits.
- Changing framework-level choices (CSS Modules → Tailwind, etc.).
- Modifying shared design tokens that affect screens outside the current run.
- After 5 iterations without convergence.
- When the fix would require backend/API changes.

The skill's autonomy extends to CSS and layout fixes. It does not extend to architectural decisions.

# Agent Handoff Reference

How to package a design system so that **any** coding agent (Claude Code, Codex, Cursor, Copilot, Gemini CLI, Windsurf, ...) builds on-spec UI with it. Everything here is plain files and standard tooling in the repo; nothing depends on one agent, IDE or vendor.

## Principles

1. **Files in git beat tool integrations.** Every agent reads files. MCP servers, plugins and design-tool links are optional accelerators on top.
2. **Compose, don't style.** Agents stay on-spec far more reliably when they assemble existing components than when they write CSS from tokens. Ship a component library, not just tokens.
3. **Semantic names only.** The agent sees `--surface-action`, `bg-surface-action`, `<Button variant="primary">`; raw values live only in primitives.
4. **Instructions drift; checks don't.** Every rule that matters is also a lint rule or a CI check the agent can run and fix against.
5. **Short context.** Agents load instructions on every task. Point to files; don't paste the system into instruction files.

## Layout of a design-system repo (or package)

```
design-system/
├── AGENTS.md                    # entry point for agents (what to read, what to run)
├── DESIGN.md                    # intent + key tokens for agents (see design-md.md), generated
├── tokens/
│   ├── primitives.tokens.json   # DTCG, tier 1
│   ├── semantic.tokens.json     # DTCG, tier 2 (per mode / brand)
│   └── mapped.tokens.json       # DTCG, tier 3
├── design/DESIGN.prose.md       # hand-written prose spliced into DESIGN.md
├── dist/                        # generated, published as a package
│   ├── css/tokens.css           # CSS custom properties, all modes
│   ├── css/theme.css            # Tailwind v4 @theme mapping
│   └── js/tokens.js             # optional constants
├── packages/ui/                 # components using only tokens; one doc/story per component
├── docs/components/*.md         # usage, variants, do/don't per component (agent-readable)
├── lint/                        # shared stylelint / eslint configs that ban raw values
└── package.json                 # scripts: tokens:build, design:lint, design:check
```

Product repos consume it as a versioned package (npm, internal registry, git submodule) and get `AGENTS.md` rules that point into it. Publish `DESIGN.md` inside the package so its version always matches the tokens; if a tool expects `DESIGN.md` at the repo root, copy it there in a `postinstall` or sync script and mark it generated, never edit the copy.

## Agent entry point: AGENTS.md

`AGENTS.md` is the cross-agent instruction file most coding agents read from the repo root (and from subdirectories, nearest file wins). Keep the design part to ~20 lines:

```markdown
## UI and design system

- Read `DESIGN.md` before any UI work (in product repos: `node_modules/@acme/tokens/DESIGN.md`). It is the corporate design spec; follow its Do's and Don'ts.
- Build from the components in `@acme/ui` (docs: `node_modules/@acme/ui/docs/components/`). Create a new component only if none fits, and only from tokens.
- Styling: only mapped and semantic tokens (`--surface-action`, `--text-body`, `--border-focus` ...), via the CSS custom properties in `@acme/tokens/css/tokens.css` or the Tailwind classes from `@acme/tokens/css/theme.css`. Never hex, rgb, px font sizes or font stacks in product code.
- Spacing and sizes on the 4px grid; body text 1rem; one primary action per view.
- Every interactive element: hover, focus-visible (2px focus ring), disabled; WCAG 2.2 AA contrast in light and dark mode.
- Before finishing UI work run `npm run design:check` and fix every finding.
```

**Agents that read another file name.** Keep the content in `AGENTS.md` once and point to it: e.g. Claude Code reads `CLAUDE.md`, so a `CLAUDE.md` containing the line `@AGENTS.md` imports it; other tools can use a symlink or their own one-line pointer file. Never maintain two copies of the rules.

## Enforcement (agent-agnostic)

All of these run as `npm run design:check` locally and in CI, so every agent and every human hits the same gate.

| Check | Tool | Catches |
|-|-|-|
| Raw values in styles | stylelint: core rules `color-no-hex` and `color-named: never`, plus the plugin `stylelint-declaration-strict-value` (rule `scale-unlimited/declaration-strict-value`) for `/color$/`, `fill`, `font-family`, `font-size`, `z-index` | Hex, rgb, named colors, px font sizes outside tokens |
| Raw values in Tailwind classes | A grep or eslint check for arbitrary values in class strings (`-\[#`, `-\[[0-9.]+(px\|rem)\]`), allowlist for documented exceptions | `bg-[#2563eb]`, `p-[13px]` |
| Unknown tokens in product code | stylelint plugin `stylelint-value-no-unknown-custom-properties` pointed at `tokens.css` | Invented `var(--surface-primary)` that silently resolves to nothing |
| Broken token references | Token build (Style Dictionary v5 fails on unresolved references) | Renamed or deleted tokens still referenced in DTCG |
| DESIGN.md valid and current | `designmd lint DESIGN.md`; regenerate and `git diff --exit-code DESIGN.md` | Broken refs, contrast failures in component tokens, stale spec |
| Accessibility | axe-core in Playwright / Vitest, Lighthouse a11y | Contrast, labels, focus, ARIA |
| Visual match | Screenshot tests (Playwright `toHaveScreenshot`) on component stories; `design-parity` skill against design exports | Layout and spacing drift |

A check an agent can run and read beats any amount of instruction text: give every check machine-readable output (JSON or a clear file:line list).

## Optional accelerators

Use when the setup already exists; never as the only channel.

- **Design-tool MCP servers** (Figma Dev Mode MCP with Code Connect, Penpot MCP): let an agent read variables, components and the code mapping live. Useful for large systems and design-to-code work; the repo files stay authoritative.
- **Agent skills** (`SKILL.md` folders, supported by several agents): package a "build on-spec UI" workflow (read `DESIGN.md`, compose components, run `design:check`). Keep the rules themselves in `AGENTS.md`/`DESIGN.md` so agents without skill support get them too.
- **Component docs as Markdown** generated from Storybook or the component source: an agent reads `docs/components/button.md` far cheaper than rendering a docs site.
- **llms.txt** on the published design-system docs site, for agents that browse.

## Corporate-design handover checklist

- [ ] DTCG tokens, three tiers, all modes and brands, versioned (semver; rename/remove = major)
- [ ] Generated `tokens.css` + Tailwind `@theme` (and native outputs if needed), published as a package
- [ ] `DESIGN.md` generated from tokens + prose, `lint` passes, Overview and Do's and Don'ts written by the brand owner
- [ ] Component library using only tokens, with one Markdown usage doc per component
- [ ] `AGENTS.md` design section in the design-system repo and as a snippet for product repos
- [ ] `design:check` script: stylelint/eslint raw-value bans, DESIGN.md lint, a11y, screenshot tests; wired into CI
- [ ] Logos, icons and fonts as files with usage rules (clear space, minimum size, allowed colors) in `DESIGN.md` extra sections
- [ ] A test task: give one agent a page brief with only the repo, review the result against the spec, fix whatever the agent got wrong in `DESIGN.md` or the checks

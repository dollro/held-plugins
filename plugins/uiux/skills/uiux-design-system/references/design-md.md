# DESIGN.md Reference

`DESIGN.md` is an open format (Apache-2.0, Google Labs, spec status **alpha**) for describing a visual identity to coding agents. One plain-text file in the repo root: machine-readable YAML tokens plus Markdown prose that explains how to apply them. Any agent that can read a file can use it; no MCP server, plugin or vendor tool is required.

Spec: `github.com/google-labs-code/design.md` (`docs/spec.md`). CLI: npm package `@google/design.md` (0.4.0 as of November 2026). The format is expected to change while alpha: add the CLI as a pinned devDependency and re-check this reference against `docs/spec.md` when upgrading.

## Where it sits

| Layer | Artifact | Role |
|-|-|-|
| Source of truth | `tokens/*.tokens.json` (W3C DTCG) | Every token, all three tiers, all modes and brands |
| Code | Generated CSS custom properties, Tailwind `@theme`, native | What the app actually uses |
| Agent intent | `DESIGN.md` | Compact token summary + rationale, rules, do's and don'ts an agent needs to make choices tokens alone don't answer |
| Agent entry point | `AGENTS.md` (see `agent-handoff.md`) | Points the agent to `DESIGN.md`, the token CSS and the component library, and lists the checks |

**Rule: DTCG stays the source of truth.** `DESIGN.md` is a projection for agents, not a second token store. Its token values are either generated from DTCG or checked against it in CI, never edited independently. If a system starts from a `DESIGN.md` (e.g. a Stitch export or a brand handover), convert once with `export --format dtcg`, expand to three tiers, and from then on generate in the DTCG → DESIGN.md direction.

**Rule: keep it short.** The spec describes intent, not the full system. Target a few hundred lines. Put the semantic and mapped tokens an agent should actually use; leave the full primitive ramps in DTCG. A long `DESIGN.md` costs context on every task and buries the rules.

## File structure

Two parts: YAML tokens (front matter between `---` lines, or fenced ` ```yaml ` blocks inside the sections, or both) and `##` sections. Each top-level YAML key may appear only once across all blocks. Tokens are normative; prose explains them.

### Token schema

```yaml
version: alpha            # optional
name: <string>
description: <string>     # optional
omitted:                  # optional, silences "missing section" lint warnings
  - section: rounded
    reason: "Brand uses square corners only"
colors:      { <name>: <Color> }
typography:  { <name>: { fontFamily, fontSize, fontWeight, lineHeight, letterSpacing, fontFeature, fontVariation } }
rounded:     { <level>: <Dimension> }
spacing:     { <level>: <Dimension | number> }
components:  { <component>: { backgroundColor, textColor, typography, rounded, padding, size, height, width } }
```

- **Color:** any CSS color string; hex `#RRGGBB` recommended. Converted to sRGB for contrast checks.
- **Dimension:** number with `px`, `em` or `rem`.
- **Reference:** `{colors.surface-action}` (same curly syntax as DTCG). Inside `components`, references to composites like `{typography.label-md}` are allowed.
- **Component states:** separate keys, e.g. `button-primary`, `button-primary-hover`, `button-primary-disabled`.
- Unknown color, typography and spacing names are accepted; unknown component properties warn; duplicate sections or duplicate top-level keys reject the file.

### Section order

All `##`, optional ones may be dropped, the order is fixed:

1. **Overview** (alias "Brand & Style"): personality, audience, emotional tone, density. The fallback for any decision no rule covers.
2. **Colors**: roles of each color in prose, then tokens.
3. **Typography**: families, roles, scale (9 to 15 levels typical).
4. **Layout** (alias "Layout & Spacing"): grid, max widths, spacing rhythm, breakpoints.
5. **Elevation & Depth** (alias "Elevation"): shadows, or how a flat system shows hierarchy.
6. **Shapes**: radius language.
7. **Components**: per component, variants and states.
8. **Do's and Don'ts**: guardrails.

Extra sections (`## Iconography`, `## Motion`, `## Voice & Tone`, `## Accessibility`) are allowed and preserved; place them after the eight core sections.

## Mapping the 3-tier DTCG system to DESIGN.md

DESIGN.md token groups are flat. Map like this:

| DTCG | DESIGN.md | Notes |
|-|-|-|
| Primitive color ramps (`color.blue.500`) | Usually **omit** | Agents should not pick from ramps. Include only if the brand book names them |
| Semantic color (`color.primary.default`, `color.error.default`) | `colors.primary`, `colors.error`, `colors.success`, ... | Only the role colors; the spec requires at least `primary` |
| Mapped color (`surface.action`, `text.on-action`, `border.focus`) | `colors.surface-action`, `colors.text-on-action`, `colors.border-focus` | Keep the full mapped name, separator becomes `-`, so the YAML key equals the CSS custom property without `--` (`--surface-action`). These are the names the agent should use most. Keep your names rather than renaming to the spec's suggestions (`surface`, `on-surface`); consumers accept any color name |
| Text styles (`typography.body.md`) | `typography.body-md` | Prefer the spec's names: `headline-lg`, `body-md`, `label-sm` ... |
| Spacing scale | `spacing.*` | Semantic steps (`xs`..`xl`, `gutter`, `margin`) rather than the full number scale |
| Radius | `rounded.*` | `none`, `sm`, `md`, `lg`, `xl`, `full` |
| Shadow, motion, z-index, opacity | Prose in Elevation / extra sections | No token group in the spec yet; give the values in prose, as CSS variable names |
| Component tokens | `components.*` | Only for the core atoms (button, input, card, chip, link); reference `{colors.*}`, never raw values |
| Dark mode, brands | One `DESIGN.md` describes the default mode; a short section lists how modes differ | The spec has no modes. Agents use the CSS custom properties, which switch automatically; tell them that |

Name the CSS custom property next to each role in the prose (e.g. "**Action surface** `--surface-action`: primary buttons only"). Then an agent writing code uses the variable, not the hex value from the YAML.

## Template

```markdown
---
version: alpha
name: Acme
description: Acme product UI. Light mode shown; dark mode via the same CSS custom properties.
colors:
  primary: "#2563EB"
  error: "#DC2626"
  success: "#16A34A"
  warning: "#D97706"
  information: "#0284C7"
  surface-page: "#F8FAFC"
  surface-default: "#FFFFFF"
  surface-action: "#2563EB"
  surface-action-hover: "#1D4ED8"
  text-heading: "#1E293B"
  text-body: "#334155"
  text-action: "#2563EB"
  text-on-action: "#FFFFFF"
  border-default: "#E2E8F0"
  border-focus: "#2563EB"
typography:
  headline-lg: { fontFamily: Inter, fontSize: 2rem, fontWeight: 700, lineHeight: 1.2, letterSpacing: -0.02em }
  headline-md: { fontFamily: Inter, fontSize: 1.5rem, fontWeight: 600, lineHeight: 1.3 }
  body-md:     { fontFamily: Inter, fontSize: 1rem, fontWeight: 400, lineHeight: 1.5 }
  label-md:    { fontFamily: Inter, fontSize: 0.875rem, fontWeight: 500, lineHeight: 1.4 }
rounded:
  sm: 4px
  md: 8px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
components:
  button-primary:
    backgroundColor: "{colors.surface-action}"
    textColor: "{colors.text-on-action}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 44px
  button-primary-hover:
    backgroundColor: "{colors.surface-action-hover}"
---

# Acme Design System

Generated from `tokens/*.tokens.json` by `npm run tokens:build`; do not edit the YAML by hand.
In code, use the CSS custom properties from `dist/css/tokens.css` (or the Tailwind theme), never the hex values above. Each YAML color key is the custom property name without `--`.

## Overview
Calm, precise, trustworthy. Dense data views for professionals; generous whitespace on marketing pages. Not playful: no illustrations of people, no gradients. ...

## Colors
- **Action** `--surface-action` / `--text-on-action`: the one main action per view. Never for large areas.
- **Page and cards** `--surface-page`, `--surface-default`; text `--text-heading`, `--text-body`.
- **Status** `--surface-error` with `--text-error` etc. for alerts; never color alone, always an icon or label too.
- ...

## Typography
...

## Layout
4px grid; all spacing is a multiple of 4. Content max width 1200px. Breakpoints 640 / 768 / 1024 / 1280.

## Elevation & Depth
...

## Shapes
...

## Components
Use the components from the component library before writing new markup. ...

## Do's and Don'ts
- Do use exactly one primary button per view.
- Do keep body text at 1rem on every breakpoint.
- Don't use raw hex, px font sizes or font stacks in components; use tokens.
- Don't put text below 4.5:1 contrast on any surface, in any mode.

## Accessibility
WCAG 2.2 AA. Focus ring: 2px `--border-focus` outside the element. Touch targets 44px.
```

The intro under the `#` title is not a section; keep it to two lines. Mapped names in the YAML (`surface-action`) are not in the spec's recommended list; that is allowed.

## Generating it

There is no standard DTCG → DESIGN.md converter yet (November 2026; the CLI only exports the other way). Use a small build script in the token pipeline (Style Dictionary custom format, or a plain Node script) that:

1. Reads the resolved DTCG tokens for the default mode.
2. Writes the YAML front matter from an **allowlist** of semantic and mapped tokens (not the whole tree).
3. Splices it onto a hand-written prose file (`design/DESIGN.prose.md`), so the rationale stays human-authored and the values stay generated.

Alternative for small systems: hand-write `DESIGN.md`, and in CI `export --format dtcg` it and compare the values against the real DTCG tokens.

## Checks (CI and local)

Install the CLI as a pinned devDependency (`npm i -D -E @google/design.md`) and call the dot-free bin `designmd` from scripts (the `design.md` bin name breaks on Windows):

```jsonc
// package.json
"scripts": {
  "design:lint": "designmd lint DESIGN.md",
  "design:fresh": "npm run tokens:build && git diff --exit-code DESIGN.md",
  "design:diff": "git show origin/main:DESIGN.md > .design-base.md && designmd diff .design-base.md DESIGN.md"
}
```

| Command | Does | Exit code |
|-|-|-|
| `designmd lint DESIGN.md` | Structure, section order, broken references, WCAG contrast of component text/background pairs; JSON findings | 1 on errors |
| `designmd diff before.md after.md` | Token-level added/removed/modified per group, lint delta | 1 on regression (more errors or warnings) |
| `designmd export --format css-tailwind DESIGN.md` | Tailwind v4 `@theme` block; also `json-tailwind` (v3 config), `dtcg` | 0 even with lint findings; run `lint` to gate |
| `designmd spec --rules` | Prints the spec and active lint rules (useful as agent context) | |

Recommended gates: `design:lint` passes; `design:fresh` shows `DESIGN.md` matches the tokens; a token rename or removal in `design:diff` is a major version of the design system, as with DTCG.

## Pitfalls

- **Two sources of truth.** Hand-editing YAML in `DESIGN.md` while DTCG also changes. Generate or check, always.
- **Dumping primitives.** 120 ramp colors in `DESIGN.md` invite the agent to pick `blue-600` instead of `surface-action`.
- **Prose without variable names.** The agent copies hex values into code. Name the CSS variable or Tailwind class in every rule.
- **Vague Overview.** "Modern and clean" decides nothing. State audience, density, tone and what the brand is *not*.
- **No Do's and Don'ts.** This section is where most corporate-design violations are prevented; write the rules a brand reviewer would reject a page for.
- **Alpha drift.** Re-run `lint` after upgrading the CLI; pin the version.

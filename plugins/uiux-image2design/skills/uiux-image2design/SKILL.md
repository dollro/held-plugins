---
name: uiux-image2design
description: "Analyses UI screenshots, extracts a full design system (colours, type, spacing, components, tokens) and builds it in Penpot or Figma. Use when the user provides screenshots or images and wants a design system from them, or says \"create a design from these images\", \"extract the style\", \"screenshot to design system\", \"reverse engineer this UI\", \"image2design\"."
---

# Image to Design System

Analyze UI screenshots, extract a design system, confirm it with the user, then generate
everything in Penpot or Figma: tokens, design system boards, reusable components, and
a sample screen. Detects the available design tool at startup and delegates tool-specific
work to the corresponding plugin.

This skill orchestrates shared knowledge and a tool-specific plugin:
- `uiux-design-system` — design system architecture, token format, naming, hierarchy, W3C DTCG spec, component naming, UX patterns, component patterns, accessibility, platform guidelines, color utilities
- Tool plugin (detected at Step 0): `uiux-design-penpot` or `uiux-design-figma` — tool-specific MCP API, generation recipes, known issues

## Step 0: Verify Dependencies

Run ALL checks before starting. Stop if any fail.

**0a. Find `uiux-design-system` skill.**
Search for its SKILL.md in the project's plugin directories. Confirm it exists along
with its references: `design-system-template.md`, `dtcg-format.md`, `starter-template.md`,
`platform-mapping.md`, `component-patterns.md`, `accessibility.md`, `platform-guidelines.md`,
`color-utilities.md`.
If missing, tell the user to install it and stop.

**0b. Find a tool-specific skill.**
Search for `uiux-design-penpot` or `uiux-design-figma` SKILL.md in the project's plugin
directories. If `uiux-design-penpot` is found, confirm its references exist:
`penpot-api-reference.md`, `penpot-color-patterns.md`, `prototyping-interactions.md`,
`generation-recipes.md`, `mcp-known-issues.md`, `penpot-design-system-guide.md`.
If `uiux-design-figma` is found, confirm its references exist:
`figma-api-reference.md`, `generation-recipes.md`, `variable-mapping.md`,
`variable-binding.md`, `figma-design-system-guide.md`.
If neither is found, tell the user to install one and stop.

**0c. Test design tool MCP connection.**
Based on which tool skill was found in 0b, test the corresponding MCP connection:

- **Penpot:** Call `mcp__penpot__penpot_api_info`. If it fails, refer to
  `uiux-design-penpot/references/setup-troubleshooting.md`.
- **Figma:** Call `mcp__figma__figma_get_status`. If it fails, refer to
  `uiux-design-figma/references/setup-troubleshooting.md`.

If both tool skills exist, prefer whichever has a working MCP connection. If both
connect, ask the user which tool to target.

Set `TOOL = 'penpot' | 'figma'` for the rest of the workflow.

**0d. Report readiness.** Confirm all checks passed, report detected tool, ask for screenshots.

---

## The 6-Phase Workflow

```
Phase 1: Screenshot Analysis    ──→ Design Inventory
Phase 2: User Confirmation      ──→ Confirmed Spec
Phase 3: Token Generation       ──→ Token files + design tool tokens/variables + tokenMap
Phase 4: Board Generation       ──→ Pages (cover, foundations, atoms, molecules, organisms, screens-*)
Phase 5: Screen Pages           ──→ screens-* pages from Confirmed Spec
Phase 6: Token Binding Audit    ──→ All shapes bound to tokens, coverage report
```

Each phase completes before the next begins.
Drive forward autonomously — only pause at Phase 2 for user confirmation.
Phases 3-6 delegate tool-specific work to the detected tool plugin (Penpot or Figma).

---

## Phase 1: Screenshot Analysis

**Read** `references/analysis-guide.md` — the full 10-section extraction methodology.

**Core directive** (internalize this when analyzing):

> Deeply analyze the design of the attached screenshot to create a design system layout
> of every UI component needed in a design system for a SaaS product service. Pay close
> attention to spacing, fonts, colors, design styles and design principles.

If the user has described their product, append that context to sharpen the analysis:

> ...for **a B2B analytics dashboard**. Also identify data visualization patterns,
> metric card layouts, and filter/control components specific to dashboard interfaces.

**Execute the 10-section analysis in order:**
1. Initial Assessment (platform, design language, density, color mode)
2. Color Palette (by role, with hex values and `observed in:` attributions)
3. Typography (font family with confidence level, sizes with `~` prefix)
4. Spacing (base unit, scale as multipliers, component padding, gap patterns)
5. Layout Structure (grid, section map, visual hierarchy, alignment)
6. Border Radius (values with usage contexts)
7. Shadows & Depth (classify strategy first, then extract values)
8. Component Inventory (variants, visible states, missing states)
9. Iconography (style, size, set identification)
10. Known Gaps (MANDATORY — states not visible, uncertain values, next steps)

**Output:** Present the full Design Inventory to the user.
Read `references/confirmation-templates.md` for the inventory output format.

---

## Phase 2: User Confirmation

**Read** `references/confirmation-templates.md` — output formats and interaction patterns.

### Step 2a: Category-Level Review

Present the inventory and ask for per-category feedback:
- ✅ Looks good
- ✏️ Needs adjustments (drill down)
- ❌ Skip
- ➕ Add something not in screenshots

Categories: Colors, Typography, Spacing, Layout, Radius, Shadows & Depth,
Components, Iconography, Additional Patterns, Known Gaps.

The **Gaps** category is special: present each gap as a decision with a proposed default.
Example: "Hover states not visible. I propose: 10% darker for hover, 20% for active. OK?"

### Step 2b: Drill-Down

For any category marked ✏️, present individual elements and ask for specific changes.
Absorb all feedback before moving on.

### Step 2c: Confirm Final Spec

Present the clean **Confirmed Spec** summary. Ask for one final "go ahead."
Do NOT proceed to Phase 3 without explicit confirmation.

---

## Phase 3: Token Generation

**Read these now** (paths verified in Step 0):
- `uiux-design-system/SKILL.md`
- `uiux-design-system/references/dtcg-format.md`
- `uiux-design-system/references/starter-template.md`
- `uiux-design-system/references/platform-mapping.md`

Read them fresh — the user may have updated them since the last run.

**Read tool-specific token API patterns:**
- If TOOL=penpot: read `uiux-design-penpot/SKILL.md` (sections: "Design Tokens API",
  "Token Binding", "Connection Stability") and `uiux-design-penpot/references/mcp-known-issues.md`
- If TOOL=figma: read `uiux-design-figma/SKILL.md` (sections: "Variable / Token Management",
  "Variable Binding") and `uiux-design-figma/references/variable-mapping.md`

### Framework-Agnostic Principle

Token and design tool output is independent of any frontend framework. The design system
works whether the user implements in Vue, React, Svelte, or plain HTML. If the user has
framework-specific skills installed (e.g. Tailwind CSS v4), mention that CSS/Tailwind
output is available — but never make it a required step.

### Execute

1. **Build Primitive tokens** — raw color scales, font stacks, spacing values, radius,
   shadows, motion. Every raw value lives here exclusively.

2. **Build Semantic tokens** — map primitives to intent. Include accessibility tokens:
   `color.border.focus-ring`, `size.touch-target.min`, `size.touch-target.comfortable`.

3. **Build Component tokens** — only where components diverge from semantic defaults.

4. **Build Mapped tokens** — the four categories applied directly to components:
   - `text/*` — heading, body, action, on-action, disabled, success/warning/error/info
   - `icon/*` — mirrors text tokens (icons next to text share the same color)
   - `surface/*` — page, default, action, action-hover, action-hover-light, disabled, success/warning/error/info
   - `border/*` — default, action, action-hover, focus, disabled, success/warning/error/info
   Include both Light and Dark mode values. See `uiux-design-system/references/mapped-tokens.md` for the complete reference.

5. **Output token files** — as defined by `uiux-design-system`:
   `tokens.json` (W3C DTCG), `design-tokens.css` (CSS custom properties),
   `main.css` (Tailwind v4 `@theme`).

6. **Apply tokens/variables in design tool** — delegate to the detected tool plugin.
   Follow its sequencing rules and API patterns for token creation.

7. **Register library colors and typographies** — using the tool's library API.

8. **Build token map** — construct a `tokenMap` object mapping every semantic token name
   to its resolved hex/string value. This map is used by Phases 4, 5, and 6 for both
   visual rendering and token binding. Include all semantic color, spacing, radius,
   shadow, and typography tokens. See `uiux-design-system/references/token-binding-strategy.md`
   for the tokenMap pattern.

---

## Phase 4: Board & Component Generation

**Read shared design knowledge** (paths verified in Step 0):
- `uiux-design-system/references/color-utilities.md`
- `uiux-design-system/references/component-patterns.md`
- `uiux-design-system/references/design-system-template.md` — component inventory, pattern recipes, UX patterns, completeness checklist
- `uiux-design-system/references/token-binding-strategy.md` — greenfield binding pattern

**Read tool-specific references:**
- If TOOL=penpot: `uiux-design-penpot/SKILL.md`, `references/penpot-api-reference.md`,
  `references/penpot-design-system-guide.md`, `references/generation-recipes.md`,
  `references/token-binding.md`
- If TOOL=figma: `uiux-design-figma/SKILL.md`, `references/figma-api-reference.md`,
  `references/figma-design-system-guide.md`, `references/generation-recipes.md`,
  `references/variable-binding.md`

**Read this skill's own references:**
- `references/board-layouts.md` — board dimensions, positioning, layout patterns
- `references/component-recipes.md` — workflow orchestration for component generation

### Page Structure

Follow the page structure from the tool plugin's design system guide.
Create pages from the Confirmed Spec inventory. Not all pages are always needed.

| Page | When to create | Content |
|-|-|-|
| `cover` | Always | 1390×930 frame, version, date, status, component/token counts |
| `foundations` | Always | colors/primitives, colors/semantic, typography/scale, spacing/scale, elevation/levels, borders, icons |
| `atoms` | Always | button, input, badge-tag, avatar, toggle-checkbox-radio, divider, tooltip, spinner |
| `molecules` | If Confirmed Spec includes composed components | form-field, card, nav-item, dropdown-select, toast-alert, search-bar, pagination |
| `organisms` | If Confirmed Spec includes complex compositions | header-navbar, sidebar-navigation, data-table, modal-dialog, footer, command-palette |
| `patterns` | If layout patterns identified | layout-templates, section compositions, state patterns (empty/loading/error) |
| `screens-*` | At least one (Phase 5) | Real content screens — name by app type (e.g. `screens-dashboard`, `screens-landing`) |

**How to decide between organisms, patterns, and screens:**

- **Organism** = a self-contained, reusable UI component registered in the library.
  Test: "Can I instantiate this as a component in another context?" If yes → organism.
  Examples: header-navbar, data-table, modal-dialog, sidebar-navigation.
- **Pattern** = a layout blueprint or state variation — not a component itself, but a
  recipe for arranging components. Not registered in the library.
  Test: "Is this a structural template or a state that applies to many contexts?" If yes → pattern.
  Examples: sidebar+content layout, empty state (icon + message + CTA), loading skeleton, error state.
- **Screen** = a real application page with real content, proving the system works end-to-end.
  Composes organisms into patterns with actual data.
  Test: "Does this represent a full page a user would see?" If yes → screen.

Use the guide's naming conventions:
- Page names: lowercase with hyphens, no number prefixes
- Frame names: `{page-context}/{frame-purpose}` (e.g. `colors/primitives`, `button/variants`, `button/anatomy`)
- Component names: `{page-context}/{component-name}/{variant-property}/{variant-value}`

### Execution Constraints

1. **One board per code execution call.** Respect tool timeout limits (Penpot: 30s, Figma: 5-30s).
2. **Structure first, populate second.** Board/frame → layout → children → register.
3. **Choose flex vs grid deliberately** — read `generation-recipes.md` § "Layout Selection Guide" before applying layouts. Use grid for equal-column cards, 2D page structure, specimen boards. Use flex for 1D content flow, wrapping tags, inner component layout. Do not default to flex for everything.
4. **Check existing boards/frames** before creating to avoid overlap.
5. **Validate visually** after each major board.
6. **Bind tokens inline** — after creating each shape, immediately bind its tokens using
   the tool's binding API. Use the `tokenMap` from Phase 3 for visual values AND token binding.
   See the tool plugin's generation recipes and token-binding reference for the exact pattern.

### Component Generation Order

Build in dependency order so composite components can instantiate atomic ones:
1. Atomic — buttons, badges, tags
2. Form — inputs, selects, checkboxes, toggles
3. Composite — cards (contain buttons, badges)
4. Navigation — nav bars (contain buttons, icons)
5. Complex — modals, dropdowns (contain multiple atomic elements)

Register each component's default variant using the tool's component API.

---

## Phase 5: Screen Pages

Create one complete application screen proving the system works end-to-end.

1. Create/find the appropriate screens-* page (e.g. screens-dashboard, screens-landing)
2. Create main board/frame at target device size (from Confirmed Spec layout)
3. Build layout structure — header, content, navigation
4. Instantiate registered components from library
5. Apply final styling — fills, text content, spacing — using `tokenMap` values
6. **Bind tokens inline** — every shape gets its tokens bound at creation time
7. Optionally add prototyping interactions (tool-specific)
8. Export and validate visually

**Validation checklist:**
- Colors match Confirmed Spec
- Typography hierarchy is correct
- Spacing follows base grid
- Components match their board definitions
- Touch targets ≥ 44px
- Layout matches original screenshot intent
- **Token bindings are applied** (not just visual values)

---

## Phase 6: Token Binding Audit

**Read:**
- `uiux-design-system/references/token-binding-strategy.md` — confidence scoring, sweep algorithm
- Tool-specific binding reference: `uiux-design-penpot/references/token-binding.md` or
  `uiux-design-figma/references/variable-binding.md`

Run the binding sweep for each page in order:
`foundations → atoms → molecules → organisms → patterns → screens-*`

After each page, report to the user:
- Bindings applied (high/medium confidence): count and summary
- Items needing input (low confidence): list with shape name, property,
  candidate tokens, and why confidence is low

Collect user decisions for low-confidence items. Apply confirmed bindings.

**Final summary:** total bindings before/after, coverage percentage per page.
Target: >90% of shapes with at least one token binding on foundations and atoms pages,
>70% on screen pages.

**Standalone usage:** Phase 6 can be triggered independently on any existing design file.
The user says "bind my tokens", "audit token bindings", or "wire up tokens" and the
sweep runs without needing Phases 1-5.

---

## Error Recovery

See the detected tool plugin's known-issues reference for comprehensive API workarounds.

**Connection lost:** Tell user to reconnect. Resume from failed operation.
**Timeout:** Split into smaller calls. One variant row per call for large boards.
**Visual mismatch:** Find shape, fix, re-export.
**Token/variable API errors:** Follow the tool plugin's documented workarounds.
**Token binding failures:** If inline binding fails during Phases 4-5, Phase 6
will catch unbound shapes in the sweep. Don't block on individual binding failures.

---

## Adaptation

**Desktop dashboard:** 1440×900, sidebar nav, card grid, consider data viz components.
**Mobile app:** 375×812 or 390×844, bottom nav, stack layout, safe areas (44px status, 34px home).
**Marketing page:** 1440×900+, hero + feature sections, focus on typography and whitespace.
**Low quality screenshots:** Be transparent about uncertainty. Flag in Gaps. Confirm in Phase 2.

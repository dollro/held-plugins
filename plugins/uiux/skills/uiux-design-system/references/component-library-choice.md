# Choosing and Theming a Component Library

For product UIs, build on one established component library and spend the identity on tokens and the signature. Re-implementing a library's components by hand costs accessibility and consistency and buys nothing a theme can't give. Bespoke components only where the library has no equivalent, built from its primitives.

## Criteria

| Criterion | Question |
|-|-|
| Theming depth | Can every visual value (colour, radius, type, spacing, focus ring, motion) come from our CSS custom properties, without overriding internal class names? |
| Ownership | Is component code copied into the repo (full control, we maintain it) or a dependency (updates, less control)? |
| Accessibility | Keyboard, focus management, ARIA for menus, dialogs, comboboxes, tabs, date pickers built in? |
| Data components | Does it have a serious data table (sorting, column sizing, virtualisation, sticky columns) if the product is data-heavy? |
| Fit with the direction | Does its default look pull toward a style the direction rejects (Material elevation, rounded consumer look)? |
| Maintenance | Active releases, issue response, migration path between majors? |

## Vue 3 (reference stack: Vue 3, Vite, Tailwind v4)

| Library | Type | Strength | Watch |
|-|-|-|-|
| shadcn-vue on Reka UI | Copy-in components on headless primitives, styled with Tailwind | Full theming through tokens, you own the code, accessible primitives; default for most product UIs on this stack | You maintain the copied code; the untouched default look is a recognisable template, so theme it |
| Reka UI alone | Headless primitives | Maximum control for a strongly bespoke direction | Every visual is yours to build |
| PrimeVue (unstyled or with design tokens) | Full component suite | Rich data table, tree, charts, enterprise widgets | Pick the unstyled/pass-through or token theming mode; styled presets fight a custom direction |
| Nuxt UI | Reka UI + Tailwind, styled | Fast for Nuxt apps, good defaults | Nuxt-oriented; theme deeply or it reads as stock |
| Vuetify | Material Design suite | Complete, mature | Pulls toward Material; hard to make it not look like Material |

Data-heavy screens: pair a themeable library with TanStack Table (headless) when its own table is not enough.

## React equivalents

shadcn/ui (Radix or Base UI primitives), React Aria Components (headless, strongest accessibility), Mantine (full suite, token theming), MUI (Material; same caveat as Vuetify).

## Theming rules

- Map the library's theme variables to the **mapped** tokens (`surface-*`, `text-*`, `border-*`), never to primitives, so dark mode and brands switch automatically.
- Theme these before any screen work: radius, font family and sizes, focus ring, control heights (density), colours of primary/secondary/ghost/destructive variants, motion durations and easing.
- Keep the library's component names and variants as the design system's component inventory where possible; `DESIGN.md` names them ("Use `Button variant=primary` for the one main action").
- Record the choice and the reason in `DESIGN.md › Components` and in the repo's `AGENTS.md`, including the rule: "Theme the library with our tokens; do not re-implement its components."
- Check the result with `uiux-visual-review`: off-token colours and font sizes in library components mean a variable was not mapped.

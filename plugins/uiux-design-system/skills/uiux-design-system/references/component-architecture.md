# Component Architecture

How a design system organises UI into tiers, names components and variants, and which states and properties every component exposes. Uses **atomic design**, the industry standard shared by Figma, Penpot and code-based systems. For when and how granular to componentize, see `componentization-guide.md`; for per-component build recipes with token bindings, see `component-patterns.md`.

## The 5 Tiers

| Tier | What it is | Examples |
|-|-|-|
| **Atoms** | Smallest meaningful UI unit. Has states, no sub-components | button, input field, badge, avatar, toggle, checkbox, radio, divider, tooltip, spinner, label |
| **Molecules** | Small group of atoms functioning as a unit | form-field (label + input + hint), card, nav-item, dropdown, toast, alert, search-bar, pagination, checkbox-label, switch-label |
| **Organisms** | Complex UI sections composed of molecules + atoms | header, sidebar, data-table, modal, footer, command-palette, tab-bar, menu, carousel |
| **Patterns** | Reusable layout/section/state recipes (not registered as components) | layout templates, section recipes (hero, pricing), state patterns (empty, loading, error) |
| **Screens** | Full-page compositions at specific breakpoints | landing/desktop, dashboard/default, settings/profile, auth/login |

## Component Naming Convention

Slash-separated hierarchy creates nested groups in asset panels:

```
{tier}/{component}/{variant-type}/{variant-value}
```

```
atoms/button/primary/default       atoms/input/text/focus
atoms/button/primary/hover         atoms/badge/status/success
atoms/button/secondary/disabled    atoms/avatar/image/lg
molecules/card/content/default     molecules/form-field/error
molecules/dropdown/single/open     molecules/toast/success
organisms/header/desktop/default   organisms/sidebar/expanded/default
organisms/header/mobile/menu-open  organisms/data-table/empty
organisms/modal/confirm/default    organisms/footer/mega/default
```

For components with multiple variant axes, prefer **variant properties** over encoding everything in the slash-name:

```
Component: atoms/button
Variant properties:
  - style:  primary | secondary | outline | ghost | danger
  - size:   sm | md | lg
  - state:  default | hover | active | disabled | loading
```

## Internal vs Published Components

Prefix private/internal building blocks with a dot (`.`):

```
.menu-item     → internal building block, not published
Menu           → published, composed of .menu-item instances

.tab-item      → internal
Tab Bar        → published

.carousel-item → internal
Carousel       → published

.text-area     → internal (the raw text box)
Text Area      → published (label + text area + hint text)
```

The dot prefix tells design tools not to publish it in the library. End users only see composed components, not the building blocks. In code-based systems, use `_` prefix or an `internal/` directory. More detail in `componentization-guide.md` §0.

## Responsive Variants

Breakpoints are component variants, not separate trees:

```
organisms/header/desktop/default
organisms/header/tablet/default
organisms/header/mobile/menu-open
```

Each organism and pattern should have frames at standard breakpoints (1440px desktop, 768px tablet, 375px mobile).

## State Variants

Every interactive component needs these states:

| State | Surface Token | Border Token | Text/Icon Token | Notes |
|-|-|-|-|-|
| **Default** | `surface/default` or `surface/action` | `border/default` or `border/action` | `text/body` or `text/on-action` | Resting state |
| **Hover** | `surface/action-hover` or `surface/action-hover-light` | `border/action-hover` | `text/action-hover` | Mouse over |
| **Focus** | Same as default | `border/focus` (2px) | Same as default | Keyboard navigation — accessibility critical |
| **Disabled** | `surface/disabled` | `border/disabled` | `text/disabled` / `icon/disabled` | Non-interactive |
| **Error** | `surface/error` | `border/error` | `text/error` | Validation failure |
| **Selected** | `surface/action` | `border/action` | `text/on-action` | Toggled/active |

**Focus ring implementation:** Use a separate shape layered around the component with absolute positioning — 2px stroke on the outside, no fill, constrained to resize with the component. 1px is too subtle; 2px provides clear keyboard-navigation visibility.

## Component Properties Pattern

Every component should expose these property types as appropriate:

| Property Type | Use Case | Example |
|-|-|-|
| **Text** | Editable text content | Button label, input placeholder |
| **Instance Swap** | Swappable nested components | Icon left/right in buttons |
| **Layer** (Boolean) | Show/hide elements | Toggle icon visibility, show/hide hint text |
| **Variant** | Switch between states/types | status: default/hover/focus/disabled; type: filled/outline |

**Icon handling convention:** Standard icon size 20×20px across all components. Use instance swap properties for icon left and icon right. Add a layer (boolean) property to toggle icon visibility.

## Recommended Build Order (short form)

Build atoms first, then compose upward:

1. **Button** → **Label** → **Input Field** → **Input** (composed: label + field + hint)
2. **Checkbox** → **Radio** → **Switch** (each with label molecule)
3. **Text Area** → **Menu Item** (internal) → **Menu** → **Tab Item** (internal) → **Tab Bar**
4. **Button Group** → **Link** (+ breadcrumb variant) → **Avatar** (+ avatar group) → **Tag/Chip** → **Badge**
5. **Loader/Spinner** → **Progress Bar** (+ progress circle) → **Snackbar/Toast**
6. **Button Icon** → **Carousel** → **Table** (most complex — cells → columns → table)

The phased version with reasons is in `componentization-guide.md` §10.

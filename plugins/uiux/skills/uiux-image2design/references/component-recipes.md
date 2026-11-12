# Component Generation Orchestration

Workflow guide for generating design system boards and UI components in Penpot.
For the actual `execute_code` templates, read:
→ `uiux-design-penpot/references/generation-recipes.md`

## Board Generation Order

Build boards in this dependency order — composite components may instantiate atomic ones:

1. **cover page** (no dependencies)
   - Version-info board (1390×930)

2. **foundations page** (no dependencies)
   - colors/primitives board
   - colors/semantic board
   - typography/scale board
   - spacing/scale board
   - elevation/levels board (if applicable)

3. **atoms page** (depends on registered library colors/typographies)
   - buttons, badges, tags, inputs, toggles, checkboxes, radio, avatar, divider, tooltip, spinner

4. **molecules page** (depends on registered atoms)
   - form-fields, cards, nav-items, dropdown-selects, toast-alerts, search-bar, pagination

5. **organisms page** (depends on registered atoms + molecules)
   - header-navbar, sidebar-navigation, data-table, modal-dialog, footer, command-palette

6. **screens-* pages** (depends on registered components)

## Mapping Confirmed Spec → Recipe Placeholders

For each recipe in `generation-recipes.md`, replace placeholder values with Confirmed Spec data:

| Recipe placeholder | Source in Confirmed Spec |
|-|-|
| Color hex values | Colors table → Hex column |
| `FONT_FAMILY` | Typography → Family column |
| Font sizes/weights | Typography → Size, Weight columns |
| `RADIUS` values | Border Radius → Value column |
| Shadow values | Depth Strategy → shadow levels |
| `BLOCK_COLOR` (spacing) | Use primary color from Colors |
| Component state colors | Derive from palette: hover = primary-600, active = primary-700 |
| `DEVICE_WIDTH` | Layout → target dimensions |

## Component Selection Logic

Based on the Confirmed Spec's component inventory:

1. **Always generate**: Colors, Typography, Spacing boards (every design system needs these)
2. **Generate if listed**: Each component from the "Components to Generate" table
3. **Skip if marked ❌**: Components the user explicitly excluded in Phase 2
4. **Infer variants**: Use the "Variants" and "States" columns to determine how many
   individual shapes to create before assembling the grid board
5. **Register defaults**: After assembling each component board, register the default
   variant (e.g., `btn-primary-default`) as a library component

# Figma Design System Guide

Page structure, naming conventions, and organization patterns for building design
systems in Figma using `figma-console-mcp`.

---

## Page Structure

Use an Atomic Design hierarchy. Create pages via `figma_execute`:

```javascript
const pages = ['Cover', 'Foundations', 'Atoms', 'Molecules', 'Organisms', 'Screens'];
for (const name of pages) {
  const existing = figma.root.children.find(p => p.name === name);
  if (!existing) {
    const page = figma.createPage();
    page.name = name;
  }
}
return 'Pages created';
```

| Page | Contents |
|-|-|
| **Cover** | Title frame, version badge, last-updated date, team info |
| **Foundations** | Color swatches, typography scale, spacing scale, elevation, iconography |
| **Atoms** | Button, Badge, Tag, Avatar, Checkbox, Radio, Toggle, Input, Divider |
| **Molecules** | Search bar, Form field (label + input + helper), Card, Dropdown, Toast |
| **Organisms** | Nav bar, Sidebar, Modal, Data table, Form section |
| **Screens** | Assembled page layouts using instances of organisms and molecules |

---

## Section and Frame Naming

Figma has native **Sections** (canvas-level grouping, not nested in frames). Use
Sections to group related content on a page. Within each section, use frames as
component boards.

```
Page: Foundations
  Section: Colors
    Frame: Primitive Colors    (swatch grid)
    Frame: Semantic Colors     (swatch grid)
  Section: Typography
    Frame: Type Scale           (font samples)
  Section: Spacing
    Frame: Spacing Scale        (spacing blocks)
```

Create a section via `figma_execute`:

```javascript
const section = figma.createSection();
section.name = 'Colors';
section.resizeWithoutConstraints(1200, 800);
```

> Sections cannot contain auto-layout. Use frames inside sections for auto-layout.

---

## Component Naming

Use `/` delimiters to create variant groupings. Figma interprets `/`-separated names
as variant property=value pairs inside component sets.

| Pattern | Example | Result in Figma |
|-|-|-|
| `Category/Variant` | `Button/Primary` | Component set "Button", variant "Primary" |
| `Type=Value, State=Value` | `Type=Primary, State=Default` | Two-axis variant grid |
| `Nested/Path` | `Icons/Navigation/Arrow Left` | Nested component grouping in Assets panel |

### Variant Properties

When creating component sets, Figma derives properties from the component names.
Use `Property=Value` syntax for multi-axis grids:

```javascript
// Creates a 2x4 grid: Type (Primary, Secondary) x State (Default, Hover, Active, Disabled)
const names = [];
for (const type of ['Primary', 'Secondary']) {
  for (const state of ['Default', 'Hover', 'Active', 'Disabled']) {
    names.push(`Type=${type}, State=${state}`);
  }
}
```

After creating variants, use `figma_arrange_component_set` to generate the labeled grid.

---

## Auto-Layout Patterns

All component boards should use auto-layout for responsive behavior.

### Vertical Stack (Column)

```javascript
frame.layoutMode = 'VERTICAL';
frame.itemSpacing = 8;
frame.paddingTop = 16;
frame.paddingBottom = 16;
frame.paddingLeft = 16;
frame.paddingRight = 16;
frame.primaryAxisSizingMode = 'AUTO';   // height wraps content
frame.counterAxisSizingMode = 'FIXED';  // width is fixed
```

### Horizontal Row

```javascript
frame.layoutMode = 'HORIZONTAL';
frame.itemSpacing = 12;
frame.primaryAxisAlignItems = 'CENTER';   // main axis (horizontal)
frame.counterAxisAlignItems = 'CENTER';   // cross axis (vertical)
frame.primaryAxisSizingMode = 'AUTO';
frame.counterAxisSizingMode = 'AUTO';
```

### Fill Container (Stretch)

```javascript
// Child stretches to fill parent's cross-axis
child.layoutSizingHorizontal = 'FILL';
child.layoutSizingVertical = 'HUG';   // or 'FIXED' or 'FILL'
```

### Spacing with Variables

Bind auto-layout spacing to variables for consistent token usage:

```javascript
frame.itemSpacing = 16;
await VR.bind(frame, 'itemSpacing', 'primitives', 'spacing/4');
```

---

## Library Publishing Workflow

1. **Create components** on the appropriate Atomic Design page
2. **Add descriptions** via `figma_set_description` for Dev Mode documentation
3. **Organize variants** with `figma_arrange_component_set`
4. **Publish the library** manually in Figma: Assets panel > Team library icon > Publish
5. **Consume from other files** using `figma_search_components` with `libraryFileKey`
   and `figma_instantiate_component`

> Publishing must be done manually in the Figma UI. The MCP server cannot trigger
> a publish. After publishing, use `figma_get_library_components` to verify.

---

## File Organization Checklist

- [ ] Pages follow Atomic Design hierarchy (Cover through Screens)
- [ ] Each page uses Sections to group related content
- [ ] Components use `Property=Value` naming for variant grids
- [ ] All components have descriptions for Dev Mode
- [ ] Variables are organized in collections (Primitives, Semantic)
- [ ] Auto-layout is used on all component frames
- [ ] Color, spacing, and radius values are bound to variables

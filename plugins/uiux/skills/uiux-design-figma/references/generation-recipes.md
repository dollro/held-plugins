# Generation Recipes for Figma MCP

Reusable `figma_execute` templates for generating UI components and design system boards
in Figma. Adapt placeholder values to match your project's design system.

> **Execution constraints:**
> - `figma_execute` max timeout 30 s (default 5 s — pass `timeout: 15000` for recipes)
> - Fonts must be loaded: `await figma.loadFontAsync({ family, style })`
> - Colors use `{ r, g, b }` in 0-1 range — use the `hexToRgb` helper
> - Always `return` a result to confirm success
> - **Bind variables to nodes** — see [variable-binding.md](variable-binding.md)
> - After creation, validate with `figma_take_screenshot`
>
> **Coverage note:** This file covers core recipes (color swatches, typography, spacing,
> button, text input, card). For components not covered here (toggle, metric card, bottom
> nav, etc.), adapt the patterns from these recipes — the structure is the same:
> create frame → auto-layout → children → bind variables.

## Shared Helpers

### Color Conversion

```javascript
function hexToRgb(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  return {
    r: parseInt(hex.substring(0, 2), 16) / 255,
    g: parseInt(hex.substring(2, 4), 16) / 255,
    b: parseInt(hex.substring(4, 6), 16) / 255,
  };
}
```

### Variable Resolver (initVarResolver)

Paste at the top of any script that binds variables.

```javascript
async function initVarResolver() {
  const collections = await figma.variables.getLocalVariableCollectionsAsync();
  const _cache = {};
  return {
    async resolve(collectionName, varPath) {
      const key = collectionName + '/' + varPath;
      if (_cache[key] !== undefined) return _cache[key];
      const coll = collections.find(c => c.name === collectionName);
      if (!coll) { _cache[key] = null; return null; }
      for (const vid of coll.variableIds) {
        const v = await figma.variables.getVariableByIdAsync(vid);
        if (v && v.name === varPath) { _cache[key] = v; return v; }
      }
      _cache[key] = null;
      return null;
    },
    async bind(node, field, collectionName, varPath) {
      const v = await this.resolve(collectionName, varPath);
      if (v) node.setBoundVariable(field, v);
      return !!v;
    }
  };
}
const VR = await initVarResolver();
```

**Usage** — set visual value, then bind variable:
```javascript
frame.fills = [{ type: 'SOLID', color: hexToRgb(tokenMap['bg.interactive']) }];
await VR.bind(frame, 'fills', 'semantic', 'bg/interactive');
```

### Position After Existing Content

```javascript
const children = figma.currentPage.children;
let nextX = 0;
children.forEach(n => {
  const right = n.x + n.width;
  if (right + 100 > nextX) nextX = right + 100;
});
```

---

## Layout Selection Guide

**Read this before generating any layout.** Figma uses auto-layout (equivalent to CSS Flexbox)
for all dynamic layouts. There is no CSS Grid equivalent, but the same design *decisions* apply.
For the tool-agnostic theory, see `uiux-design-system/references/layout-patterns.md`.

### Layout patterns in Figma

| Scenario | Figma pattern |
|-|-|
| Items in a row or column | Auto-layout `HORIZONTAL` or `VERTICAL` |
| Equal-width columns (cards, dashboards) | Auto-layout `HORIZONTAL` + all children `layoutSizingHorizontal = 'FILL'` |
| Responsive grid that wraps | Auto-layout `HORIZONTAL` + `layoutWrap = 'WRAP'` + children with `minWidth` |
| 2D page structure (sidebar + main) | Nested auto-layouts: outer `HORIZONTAL`, inner `VERTICAL` |
| Push item to bottom (button in card) | Auto-layout `VERTICAL` + middle child `layoutSizingVertical = 'FILL'` |
| Tags/chips that wrap | Auto-layout `HORIZONTAL` + `layoutWrap = 'WRAP'` |

### Key rule: equal sizing requires FILL on every child

Unlike CSS Grid where the *parent* enforces equal columns via `1fr`, Figma requires
setting `layoutSizingHorizontal = 'FILL'` on *each child*. Forget one and that child
stays at its natural width while others stretch.

### Equal-column card grid

```javascript
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
await figma.loadFontAsync({ family: 'Inter', style: 'Semi Bold' });

// Outer container — horizontal auto-layout, children fill equally
const container = figma.createFrame();
container.name = 'card-grid';
container.layoutMode = 'HORIZONTAL';
container.itemSpacing = 24;
container.paddingLeft = container.paddingRight = 24;
container.paddingTop = container.paddingBottom = 24;
container.primaryAxisSizingMode = 'FIXED';
container.counterAxisSizingMode = 'AUTO';
container.fills = [];

function createCard(title, desc) {
  const card = figma.createFrame();
  card.name = 'card-' + title.toLowerCase().replace(/\s/g, '-');
  card.cornerRadius = 12;
  card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  card.effects = [{ type: 'DROP_SHADOW', color: { r: 0, g: 0, b: 0, a: 0.1 },
    offset: { x: 0, y: 2 }, radius: 8, spread: -2, visible: true }];

  card.layoutMode = 'VERTICAL';
  card.itemSpacing = 12;
  card.paddingTop = card.paddingBottom = 20;
  card.paddingLeft = card.paddingRight = 20;
  card.primaryAxisSizingMode = 'AUTO';
  card.counterAxisSizingMode = 'FIXED';

  const h = figma.createText();
  h.characters = title;
  h.fontName = { family: 'Inter', style: 'Semi Bold' };
  h.fontSize = 18;
  h.fills = [{ type: 'SOLID', color: hexToRgb('#171717') }];
  card.appendChild(h);

  const p = figma.createText();
  p.characters = desc;
  p.fontName = { family: 'Inter', style: 'Regular' };
  p.fontSize = 14;
  p.fills = [{ type: 'SOLID', color: hexToRgb('#525252') }];
  card.appendChild(p);
  // Text fills remaining vertical space — pushes anything below to bottom
  p.layoutSizingVertical = 'FILL';
  p.layoutSizingHorizontal = 'FILL';

  return card;
}

const cards = [
  createCard('Feature A', 'Short description.'),
  createCard('Feature B', 'A longer description that spans multiple lines to show equal sizing.'),
  createCard('Feature C', 'Medium length text here.'),
];

cards.forEach(card => {
  container.appendChild(card);
  card.layoutSizingHorizontal = 'FILL';  // equal-width columns
  card.layoutSizingVertical = 'FILL';    // equal-height cards
});

container.resize(900, container.height);
figma.currentPage.appendChild(container);
return { id: container.id, name: container.name };
```

### Button-at-bottom card

```javascript
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
await figma.loadFontAsync({ family: 'Inter', style: 'Semi Bold' });

const card = figma.createFrame();
card.name = 'card-with-cta';
card.cornerRadius = 12;
card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];

card.layoutMode = 'VERTICAL';
card.itemSpacing = 12;
card.paddingTop = card.paddingBottom = 20;
card.paddingLeft = card.paddingRight = 20;
card.primaryAxisSizingMode = 'FIXED';  // fixed height so FILL works
card.counterAxisSizingMode = 'FIXED';
card.resize(320, 280);

// Heading
const heading = figma.createText();
heading.characters = 'Feature Title';
heading.fontName = { family: 'Inter', style: 'Semi Bold' };
heading.fontSize = 18;
heading.fills = [{ type: 'SOLID', color: hexToRgb('#171717') }];
card.appendChild(heading);
heading.layoutSizingHorizontal = 'FILL';

// Body — fills remaining space, pushes button to bottom
const body = figma.createText();
body.characters = 'Description text of varying length across cards.';
body.fontName = { family: 'Inter', style: 'Regular' };
body.fontSize = 14;
body.fills = [{ type: 'SOLID', color: hexToRgb('#525252') }];
card.appendChild(body);
body.layoutSizingHorizontal = 'FILL';
body.layoutSizingVertical = 'FILL';  // stretches to push button down

// Button — always at bottom
const btn = figma.createFrame();
btn.name = 'btn-cta';
btn.cornerRadius = 8;
btn.fills = [{ type: 'SOLID', color: hexToRgb('#3B82F6') }];
btn.layoutMode = 'HORIZONTAL';
btn.counterAxisAlignItems = 'CENTER';
btn.primaryAxisAlignItems = 'CENTER';
btn.paddingLeft = btn.paddingRight = 16;
btn.paddingTop = btn.paddingBottom = 10;
btn.primaryAxisSizingMode = 'AUTO';
btn.counterAxisSizingMode = 'AUTO';
const btnLabel = figma.createText();
btnLabel.characters = 'Learn More';
btnLabel.fontName = { family: 'Inter', style: 'Semi Bold' };
btnLabel.fontSize = 14;
btnLabel.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
btn.appendChild(btnLabel);
card.appendChild(btn);
btn.layoutSizingHorizontal = 'FILL';

figma.currentPage.appendChild(card);
return { id: card.id, name: card.name };
```

### Responsive wrap (tags / card grid)

```javascript
// Tags that wrap onto next line when container narrows
const container = figma.createFrame();
container.name = 'tag-cloud';
container.layoutMode = 'HORIZONTAL';
container.layoutWrap = 'WRAP';       // enables flex-wrap behavior
container.itemSpacing = 8;           // horizontal gap
container.counterAxisSpacing = 8;    // vertical gap between wrapped rows
container.primaryAxisSizingMode = 'FIXED';
container.counterAxisSizingMode = 'AUTO';
container.fills = [];

await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });

const tags = ['New', 'Sale', 'Popular', 'Featured', 'Limited', 'Trending', 'Hot'];
tags.forEach(label => {
  const tag = figma.createFrame();
  tag.name = 'tag-' + label.toLowerCase();
  tag.cornerRadius = 16;
  tag.fills = [{ type: 'SOLID', color: hexToRgb('#F3F4F6') }];
  tag.layoutMode = 'HORIZONTAL';
  tag.counterAxisAlignItems = 'CENTER';
  tag.paddingLeft = tag.paddingRight = 12;
  tag.paddingTop = tag.paddingBottom = 6;
  tag.primaryAxisSizingMode = 'AUTO';
  tag.counterAxisSizingMode = 'AUTO';

  const txt = figma.createText();
  txt.characters = label;
  txt.fontName = { family: 'Inter', style: 'Regular' };
  txt.fontSize = 13;
  txt.fills = [{ type: 'SOLID', color: hexToRgb('#374151') }];
  tag.appendChild(txt);
  container.appendChild(tag);
});

container.resize(300, container.height);
figma.currentPage.appendChild(container);
return { id: container.id, name: container.name };
```

### Nested layout (sidebar + main)

```javascript
// Page structure: horizontal outer, vertical inners
const page = figma.createFrame();
page.name = 'page-layout';
page.layoutMode = 'HORIZONTAL';
page.primaryAxisSizingMode = 'FIXED';
page.counterAxisSizingMode = 'FIXED';
page.resize(1440, 900);
page.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
page.itemSpacing = 0;

// Sidebar — fixed width, vertical flow
const sidebar = figma.createFrame();
sidebar.name = 'sidebar';
sidebar.layoutMode = 'VERTICAL';
sidebar.itemSpacing = 4;
sidebar.paddingTop = sidebar.paddingBottom = 16;
sidebar.paddingLeft = sidebar.paddingRight = 12;
sidebar.primaryAxisSizingMode = 'AUTO';
sidebar.counterAxisSizingMode = 'FIXED';
sidebar.fills = [{ type: 'SOLID', color: hexToRgb('#F9FAFB') }];
page.appendChild(sidebar);
sidebar.layoutSizingVertical = 'FILL';
sidebar.resize(240, sidebar.height);  // fixed 240px wide

// Main — fills remaining width, vertical flow
const main = figma.createFrame();
main.name = 'main-content';
main.layoutMode = 'VERTICAL';
main.itemSpacing = 24;
main.paddingTop = main.paddingBottom = 24;
main.paddingLeft = main.paddingRight = 24;
main.primaryAxisSizingMode = 'AUTO';
main.counterAxisSizingMode = 'FIXED';
main.fills = [];
page.appendChild(main);
main.layoutSizingHorizontal = 'FILL';  // takes remaining space
main.layoutSizingVertical = 'FILL';

figma.currentPage.appendChild(page);
return { id: page.id, name: page.name };
```

### Responsive constraints (min/max sizing)

```javascript
// Card fills container but caps at 400px wide
parent.appendChild(card);
card.layoutSizingHorizontal = 'FILL';
card.maxWidth = 400;
card.minWidth = 200;
// Fills small containers, stays bounded on wide screens
```

---

## Design System Boards

### Color Swatches Board

```javascript
const colors = {
  'Primitives': [
    { name: 'Neutral 50', hex: '#FAFAFA', varPath: 'color/neutral/50' },
    { name: 'Primary 500', hex: '#3B82F6', varPath: 'color/primary/500' },
    // ... extend with full palette
  ],
  'Semantic': [
    { name: 'BG Surface', hex: '#FAFAFA', varPath: 'bg/surface' },
    { name: 'BG Primary', hex: '#3B82F6', varPath: 'bg/interactive' },
    { name: 'Text Primary', hex: '#171717', varPath: 'text/primary' },
  ]
};

const SWATCH = 64, GAP = 16, COLS = 6;
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
await figma.loadFontAsync({ family: 'Inter', style: 'Medium' });

const board = figma.createFrame();
board.name = 'Colors';
board.resizeWithoutConstraints(600, 400);
board.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
board.x = nextX; board.y = 0;

let yOff = 24;
for (const [groupName, swatches] of Object.entries(colors)) {
  const header = figma.createText();
  header.characters = groupName;
  header.fontName = { family: 'Inter', style: 'Bold' };
  header.fontSize = 20;
  header.fills = [{ type: 'SOLID', color: hexToRgb('#171717') }];
  board.appendChild(header); header.x = 24; header.y = yOff;
  yOff += 36;

  for (let i = 0; i < swatches.length; i++) {
    const s = swatches[i];
    const col = i % COLS, row = Math.floor(i / COLS);
    const x = 24 + col * (SWATCH + GAP), y = yOff + row * (SWATCH + 32 + GAP);

    const rect = figma.createRectangle();
    rect.resizeWithoutConstraints(SWATCH, SWATCH);
    rect.fills = [{ type: 'SOLID', color: hexToRgb(s.hex) }];
    rect.cornerRadius = 8;
    board.appendChild(rect); rect.x = x; rect.y = y;
    await VR.bind(rect, 'fills', groupName.toLowerCase(), s.varPath);

    const label = figma.createText();
    label.characters = s.name + '\n' + s.hex;
    label.fontName = { family: 'Inter', style: 'Medium' };
    label.fontSize = 10;
    label.fills = [{ type: 'SOLID', color: hexToRgb('#525252') }];
    board.appendChild(label); label.x = x; label.y = y + SWATCH + 4;
  }
  yOff += Math.ceil(swatches.length / COLS) * (SWATCH + 32 + GAP) + 16;
}
return 'Colors board created';
```

### Typography Board

```javascript
const styles = [
  { name: 'Display', size: 48, fStyle: 'Bold',      sample: 'Display Heading' },
  { name: 'H1',      size: 36, fStyle: 'Bold',      sample: 'Heading Level 1' },
  { name: 'H2',      size: 24, fStyle: 'Semi Bold', sample: 'Heading Level 2' },
  { name: 'Body',    size: 16, fStyle: 'Regular',   sample: 'Body text for content.' },
  { name: 'Small',   size: 14, fStyle: 'Regular',   sample: 'Small text' },
  { name: 'Caption', size: 12, fStyle: 'Medium',    sample: 'CAPTION LABELS' },
];
const FONT = 'Inter', PAD = 32;
for (const s of styles) await figma.loadFontAsync({ family: FONT, style: s.fStyle });
await figma.loadFontAsync({ family: FONT, style: 'Regular' });

const board = figma.createFrame();
board.name = 'Typography';
board.resizeWithoutConstraints(800, PAD * 2 + styles.length * 88);
board.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
board.x = nextX; board.y = 0;

let y = PAD;
for (const s of styles) {
  const meta = figma.createText();
  meta.fontName = { family: FONT, style: 'Regular' }; meta.fontSize = 12;
  meta.characters = `${s.name} -- ${FONT} ${s.fStyle} / ${s.size}px`;
  meta.fills = [{ type: 'SOLID', color: hexToRgb('#9CA3AF') }];
  board.appendChild(meta); meta.x = PAD; meta.y = y;

  const sample = figma.createText();
  sample.fontName = { family: FONT, style: s.fStyle }; sample.fontSize = s.size;
  sample.characters = s.sample;
  sample.fills = [{ type: 'SOLID', color: hexToRgb('#171717') }];
  board.appendChild(sample); sample.x = PAD; sample.y = y + 18;
  y += s.size + 48;
}
return 'Typography board created';
```

### Spacing Board

```javascript
const spacings = [
  { name: 'space-2',  value: 8,  varPath: 'spacing/2' },
  { name: 'space-4',  value: 16, varPath: 'spacing/4' },
  { name: 'space-6',  value: 24, varPath: 'spacing/6' },
  { name: 'space-8',  value: 32, varPath: 'spacing/8' },
  { name: 'space-16', value: 64, varPath: 'spacing/16' },
];
await figma.loadFontAsync({ family: 'Inter', style: 'Medium' });

const board = figma.createFrame();
board.name = 'Spacing';
board.resizeWithoutConstraints(500, 48 + spacings.length * 48);
board.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
board.x = nextX; board.y = 0;

let y = 24;
for (const sp of spacings) {
  const rect = figma.createRectangle();
  rect.resizeWithoutConstraints(sp.value, 24);
  rect.fills = [{ type: 'SOLID', color: hexToRgb('#3B82F6'), opacity: 0.3 }];
  rect.cornerRadius = 2;
  board.appendChild(rect); rect.x = 24; rect.y = y;

  const label = figma.createText();
  label.fontName = { family: 'Inter', style: 'Medium' }; label.fontSize = 12;
  label.characters = `${sp.name}  --  ${sp.value}px`;
  label.fills = [{ type: 'SOLID', color: hexToRgb('#525252') }];
  board.appendChild(label); label.x = 24 + Math.max(sp.value, 20) + 16; label.y = y + 4;
  y += 48;
}
return 'Spacing board created';
```

---

## Component Recipes

### Button Component

Creates a single button with auto-layout and variable bindings. Call once per
variant x state, then combine into a component set.

```javascript
const VARIANT = 'primary', STATE = 'default', LABEL_TEXT = 'Button Label';
const FONT = 'Inter', RADIUS = 8, PAD_X = 24, PAD_Y = 12;

const STYLES = {
  primary: {
    default: { bg: '#3B82F6', text: '#FFFFFF', vars: { bg: 'bg/interactive', text: 'text/on-interactive' } },
    hover:   { bg: '#2563EB', text: '#FFFFFF', vars: { bg: 'bg/interactive/hover', text: 'text/on-interactive' } },
    disabled:{ bg: '#3B82F6', text: '#FFFFFF', opacity: 0.5, vars: { bg: 'bg/interactive', text: 'text/on-interactive' } },
  },
  secondary: {
    default: { bg: null, text: '#3B82F6', border: '#3B82F6', vars: { text: 'text/interactive', border: 'border/interactive' } },
  },
};
const style = STYLES[VARIANT][STATE];
await figma.loadFontAsync({ family: FONT, style: 'Semi Bold' });

const btn = figma.createFrame();
btn.name = `${VARIANT}/${STATE}`;
btn.cornerRadius = RADIUS;
btn.fills = style.bg ? [{ type: 'SOLID', color: hexToRgb(style.bg) }] : [];
if (style.border) {
  btn.strokes = [{ type: 'SOLID', color: hexToRgb(style.border) }];
  btn.strokeWeight = 1; btn.strokeAlign = 'INSIDE';
}
if (style.opacity) btn.opacity = style.opacity;

btn.layoutMode = 'HORIZONTAL';
btn.primaryAxisAlignItems = 'CENTER';
btn.counterAxisAlignItems = 'CENTER';
btn.paddingLeft = PAD_X; btn.paddingRight = PAD_X;
btn.paddingTop = PAD_Y; btn.paddingBottom = PAD_Y;
btn.primaryAxisSizingMode = 'AUTO';
btn.counterAxisSizingMode = 'AUTO';
btn.minHeight = 44;

const label = figma.createText();
label.fontName = { family: FONT, style: 'Semi Bold' };
label.fontSize = 14; label.characters = LABEL_TEXT;
label.fills = [{ type: 'SOLID', color: hexToRgb(style.text) }];
btn.appendChild(label);

// Bind variables
if (style.vars?.bg) await VR.bind(btn, 'fills', 'semantic', style.vars.bg);
if (style.vars?.border) await VR.bind(btn, 'strokes', 'semantic', style.vars.border);
if (style.vars?.text) await VR.bind(label, 'fills', 'semantic', style.vars.text);
for (const f of ['topLeftRadius','topRightRadius','bottomLeftRadius','bottomRightRadius'])
  await VR.bind(btn, f, 'semantic', 'radius/md');

figma.currentPage.appendChild(btn);
return { id: btn.id, name: btn.name };
```

### Component Set Assembly

After creating variant frames, convert to a component set:

```javascript
const variants = figma.currentPage.children.filter(
  n => n.type === 'FRAME' && ['primary/', 'secondary/'].some(p => n.name.startsWith(p))
);
const components = variants.map(f => figma.createComponentFromNode(f));
if (components.length > 1) {
  const set = figma.combineAsVariants(components, figma.currentPage);
  set.name = 'Button';
  return { componentSetId: set.id, variantCount: components.length };
}
return 'Not enough variants';
```

Then call `figma_arrange_component_set` to organize the grid with labels.

### Text Input Component

```javascript
const STATE = 'default', LABEL_TEXT = 'Email', PLACEHOLDER = 'you@example.com';
const STYLES = {
  default: { border: '#D1D5DB', bg: '#FFFFFF', placeholder: '#9CA3AF', label: '#374151' },
  focus:   { border: '#3B82F6', bg: '#FFFFFF', placeholder: '#9CA3AF', label: '#374151' },
  error:   { border: '#EF4444', bg: '#FEF2F2', placeholder: '#9CA3AF', label: '#374151' },
};
const style = STYLES[STATE], FONT = 'Inter';
await figma.loadFontAsync({ family: FONT, style: 'Regular' });
await figma.loadFontAsync({ family: FONT, style: 'Medium' });

const wrapper = figma.createFrame();
wrapper.name = `input-${STATE}`;
wrapper.layoutMode = 'VERTICAL'; wrapper.itemSpacing = 6;
wrapper.primaryAxisSizingMode = 'AUTO'; wrapper.counterAxisSizingMode = 'AUTO';
wrapper.fills = [];

const lbl = figma.createText();
lbl.fontName = { family: FONT, style: 'Medium' }; lbl.fontSize = 14;
lbl.characters = LABEL_TEXT;
lbl.fills = [{ type: 'SOLID', color: hexToRgb(style.label) }];
wrapper.appendChild(lbl);

const input = figma.createFrame();
input.resizeWithoutConstraints(320, 44); input.cornerRadius = 8;
input.fills = [{ type: 'SOLID', color: hexToRgb(style.bg) }];
input.strokes = [{ type: 'SOLID', color: hexToRgb(style.border) }];
input.strokeWeight = STATE === 'focus' ? 2 : 1; input.strokeAlign = 'INSIDE';
input.layoutMode = 'HORIZONTAL'; input.counterAxisAlignItems = 'CENTER';
input.paddingLeft = 12; input.paddingRight = 12;

const txt = figma.createText();
txt.fontName = { family: FONT, style: 'Regular' }; txt.fontSize = 16;
txt.characters = PLACEHOLDER;
txt.fills = [{ type: 'SOLID', color: hexToRgb(style.placeholder) }];
input.appendChild(txt); wrapper.appendChild(input);

figma.currentPage.appendChild(wrapper);
return { id: wrapper.id, name: wrapper.name };
```

### Card Component

```javascript
const FONT = 'Inter';
await figma.loadFontAsync({ family: FONT, style: 'Regular' });
await figma.loadFontAsync({ family: FONT, style: 'Semi Bold' });

const card = figma.createFrame();
card.name = 'card-content';
card.resizeWithoutConstraints(320, 200); card.cornerRadius = 12;
card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
card.strokes = [{ type: 'SOLID', color: hexToRgb('#E5E5E5') }];
card.strokeWeight = 1; card.strokeAlign = 'INSIDE';
card.effects = [{
  type: 'DROP_SHADOW', color: { r: 0, g: 0, b: 0, a: 0.1 },
  offset: { x: 0, y: 2 }, radius: 8, spread: -2,
  visible: true, blendMode: 'NORMAL',
}];
card.layoutMode = 'VERTICAL'; card.itemSpacing = 12;
card.paddingTop = 20; card.paddingBottom = 20;
card.paddingLeft = 20; card.paddingRight = 20;
card.primaryAxisSizingMode = 'AUTO'; card.counterAxisSizingMode = 'FIXED';

const category = figma.createText();
category.fontName = { family: FONT, style: 'Semi Bold' }; category.fontSize = 12;
category.characters = 'CATEGORY'; category.textCase = 'UPPER';
category.fills = [{ type: 'SOLID', color: hexToRgb('#3B82F6') }];
card.appendChild(category);

const title = figma.createText();
title.fontName = { family: FONT, style: 'Semi Bold' }; title.fontSize = 18;
title.characters = 'Card Title';
title.fills = [{ type: 'SOLID', color: hexToRgb('#171717') }];
card.appendChild(title);

const desc = figma.createText();
desc.fontName = { family: FONT, style: 'Regular' }; desc.fontSize = 14;
desc.characters = 'A brief description spanning multiple lines.';
desc.fills = [{ type: 'SOLID', color: hexToRgb('#525252') }];
desc.layoutSizingHorizontal = 'FILL';
card.appendChild(desc);

await VR.bind(card, 'fills', 'semantic', 'bg/surface');
await VR.bind(card, 'strokes', 'semantic', 'border/default');
await VR.bind(title, 'fills', 'semantic', 'text/primary');
await VR.bind(desc, 'fills', 'semantic', 'text/secondary');

figma.currentPage.appendChild(card);
return { id: card.id, name: card.name };
```

---

## Register as Component

```javascript
const node = await figma.getNodeByIdAsync('NODE_ID');
if (node && node.type === 'FRAME') {
  const component = figma.createComponentFromNode(node);
  return { componentId: component.id, name: component.name };
}
return 'Node not found or not a frame';
```

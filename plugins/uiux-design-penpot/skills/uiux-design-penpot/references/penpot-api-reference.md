# Penpot Plugin API Reference

## Contents

- Core Entry Point
- Shape Properties (ShapeBase)
- Shape Methods
- Board
- Color & Fill
- Shadow & Blur
- Text
- Path
- Flex Layout
- Grid Layout
- Layout Child Properties
- Library
- Design Tokens
- Page
- Viewport
- Events
- History / Undo
- Font Management
- Utilities
- Export & Markup
- Snippets

Full API reference for the `penpot` object available inside `execute_code`. Source: https://doc.plugins.penpot.app/

## Core Entry Point

The global `penpot` object is the main API entry point.

### Properties

| Property | Type | Writable | Notes |
|-|-|-|-|
| `root` | Shape \| null | no | Root shape of current page |
| `currentFile` | File \| null | no | Current file data |
| `currentPage` | Page \| null | no | Active page |
| `selection` | Shape[] | yes | Currently selected shapes |
| `viewport` | Viewport | no | Viewport settings |
| `history` | HistoryContext | no | Undo/redo context |
| `library` | LibraryContext | no | Access via `penpot.library.local` |
| `fonts` | FontsContext | no | Font management |
| `currentUser` | User | no | Active user info |
| `activeUsers` | ActiveUser[] | no | All connected users |
| `theme` | Theme | no | `"light"` or `"dark"` |
| `localStorage` | LocalStorage | no | Plugin-specific storage proxy |

### Methods

| Method | Returns | Purpose |
|-|-|-|
| `on(type, callback, props?)` | symbol | Register event listener |
| `off(listenerId)` | void | Remove event listener |
| `shapesColors(shapes)` | (Color & ColorShapeInfo)[] | Get colors used in shapes |
| `replaceColor(shapes, oldColor, newColor)` | void | Swap colors across shapes |
| `uploadMediaUrl(name, url)` | Promise\<ImageData\> | Upload media from URL |
| `uploadMediaData(name, data, mimeType)` | Promise\<ImageData\> | Upload binary media |
| `group(shapes)` | Group \| null | Group shapes |
| `ungroup(group, ...others)` | void | Ungroup |
| `createRectangle()` | Rectangle | |
| `createBoard()` | Board | |
| `createEllipse()` | Ellipse | |
| `createPath()` | Path | |
| `createText(text)` | Text \| null | |
| `createBoolean(boolType, shapes)` | Boolean \| null | Union, difference, intersection, exclude |
| `createShapeFromSvg(svgString)` | Group \| null | SVG string to shapes |
| `createPage()` | Page | |
| `openPage(page, newWindow?)` | void | Navigate to page |
| `alignHorizontal(shapes, dir)` | void | `"left"` \| `"center"` \| `"right"` |
| `alignVertical(shapes, dir)` | void | `"top"` \| `"center"` \| `"bottom"` |
| `distributeHorizontal(shapes)` | void | Even horizontal spacing |
| `distributeVertical(shapes)` | void | Even vertical spacing |
| `flatten(shapes)` | Path[] | Convert shapes to paths |
| `generateMarkup(shapes, {type?})` | string | Generate `"html"` or `"svg"` |
| `generateStyle(shapes, options?)` | string | Generate CSS |
| `generateFontFaces(shapes)` | Promise\<string\> | Generate @font-face CSS |
| `openViewer()` | void | Open view mode |

## Shape Properties (ShapeBase)

| Property | Type | Writable | Notes |
|-|-|-|-|
| `id` | string | no | Unique identifier |
| `name` | string | yes | Display name |
| `parent` | Shape \| null | no | |
| `parentIndex` | number | no | Index in parent |
| `x` | number | yes | Absolute X position |
| `y` | number | yes | Absolute Y position |
| `width` | number | **no** | Use `resize(w, h)` |
| `height` | number | **no** | Use `resize(w, h)` |
| `bounds` | Bounds | no | `{x, y, width, height}` |
| `center` | Point | no | `{x, y}` geometric center |
| `blocked` | boolean | yes | Locked state |
| `hidden` | boolean | yes | |
| `visible` | boolean | yes | |
| `proportionLock` | boolean | yes | Aspect ratio lock |
| `constraintsHorizontal` | string | yes | `"left"` \| `"right"` \| `"center"` \| `"leftright"` \| `"scale"` |
| `constraintsVertical` | string | yes | `"top"` \| `"bottom"` \| `"center"` \| `"topbottom"` \| `"scale"` |
| `borderRadius` | number | yes | All corners |
| `borderRadiusTopLeft` | number | yes | |
| `borderRadiusTopRight` | number | yes | |
| `borderRadiusBottomRight` | number | yes | |
| `borderRadiusBottomLeft` | number | yes | |
| `opacity` | number | yes | 0–1 |
| `blendMode` | string | yes | See blend modes list |
| `shadows` | Shadow[] | yes | |
| `blur` | Blur | yes | |
| `exports` | Export[] | yes | Export presets |
| `boardX` | number | yes | Relative to parent board |
| `boardY` | number | yes | |
| `parentX` | number | **no** | Use `penpotUtils.setParentXY()` |
| `parentY` | number | **no** | |
| `flipX` | boolean | yes | Horizontal mirror |
| `flipY` | boolean | yes | Vertical mirror |
| `rotation` | number | **no** | Use `rotate(angle, center?)` |
| `fills` | Fill[] \| "mixed" | yes | |
| `strokes` | Stroke[] | yes | |
| `layoutChild` | LayoutChildProperties | no | Layout child settings |
| `layoutCell` | LayoutCellProperties | no | Grid cell settings |
| `tokens` | object | no | Design token mappings |
| `interactions` | Interaction[] | no | |

## Shape Methods

| Method | Returns | Purpose |
|-|-|-|
| `resize(width, height)` | void | Change dimensions |
| `rotate(angle, center?)` | void | Rotate in degrees; center defaults to geometric center |
| `clone()` | Shape | Duplicate |
| `remove()` | void | Delete from parent |
| `bringToFront()` | void | Top of stack |
| `bringForward()` | void | One step up |
| `sendToBack()` | void | Bottom of stack |
| `sendBackward()` | void | One step down |
| `setParentIndex(index)` | void | Reposition among siblings |
| `export(config)` | Promise\<Uint8Array\> | Programmatic export |
| `addInteraction(trigger, action, delay?)` | Interaction | Add prototyping behavior |
| `removeInteraction(interaction)` | void | Remove interaction |
| `applyToken(token, properties?)` | void | Apply design token |

### Component Methods

| Method | Returns | Purpose |
|-|-|-|
| `isComponentInstance()` | boolean | Inside component instance? |
| `isComponentMainInstance()` | boolean | Inside main instance? |
| `isComponentCopyInstance()` | boolean | Inside copy instance? |
| `isComponentRoot()` | boolean | Root of component tree? |
| `isComponentHead()` | boolean | Head of nested component? |
| `componentRefShape()` | Shape \| null | Equivalent in main instance |
| `componentRoot()` | Shape \| null | Component tree root |
| `componentHead()` | Shape \| null | Component tree head |
| `component()` | LibraryComponent \| null | Associated component |
| `detach()` | void | Remove component link |
| `swapComponent(component)` | void | Replace component reference |
| `switchVariant(pos, value)` | void | Switch variant |
| `combineAsVariants(ids)` | void | Combine into variant |
| `isVariantHead()` | boolean | Heads variant structure? |

### Plugin Data Methods

Available on shapes, pages, and libraries:

| Method | Returns |
|-|-|
| `getPluginData(key)` | string |
| `setPluginData(key, value)` | void |
| `getPluginDataKeys()` | string[] |
| `getSharedPluginData(namespace, key)` | string |
| `setSharedPluginData(namespace, key, value)` | void |
| `getSharedPluginDataKeys(namespace)` | string[] |

## Board

Properties unique to Board (extends ShapeBase):

| Property | Type | Writable | Notes |
|-|-|-|-|
| `type` | `"board"` | no | |
| `children` | Shape[] | yes | Reorder via this property |
| `clipContent` | boolean | yes | Clip children inside board |
| `showInViewMode` | boolean | yes | |
| `grid` | GridLayout \| undefined | no | |
| `flex` | FlexLayout \| undefined | no | |
| `guides` | Guide[] | yes | |
| `rulerGuides` | RulerGuide[] | yes | |
| `horizontalSizing` | `"auto"` \| `"fix"` | yes | |
| `verticalSizing` | `"auto"` \| `"fix"` | yes | |

| Method | Returns | Purpose |
|-|-|-|
| `appendChild(child)` | void | Add child shape |
| `insertChild(index, child)` | void | Insert at index (z-ordering) |
| `addFlexLayout()` | FlexLayout | Add flex layout |
| `addGridLayout()` | GridLayout | Add grid layout |
| `addRulerGuide(orientation, value)` | RulerGuide | Add ruler guide |
| `removeRulerGuide(guide)` | void | Remove guide |

## Color & Fill

**CRITICAL: Penpot only accepts hex color strings (`#RRGGBB`). CSS color functions are NOT supported.**

### Fill

| Property | Type | Notes |
|-|-|-|
| `fillColor` | string | Hex e.g. `'#FF5733'` |
| `fillOpacity` | number | 0–1, defaults to 1 |
| `fillColorGradient` | Gradient | Gradient fill |
| `fillColorRefFile` | string | External file ref |
| `fillColorRefId` | string | External color ref |
| `fillImage` | ImageData | Image fill |

### Stroke

| Property | Type | Notes |
|-|-|-|
| `strokeColor` | string | Hex color |
| `strokeOpacity` | number | 0–1 |
| `strokeStyle` | string | `"solid"` \| `"dotted"` \| `"dashed"` \| `"svg"` \| `"none"` \| `"mixed"` |
| `strokeWidth` | number | |
| `strokeAlignment` | string | `"center"` \| `"inner"` \| `"outer"` |
| `strokeCapStart` | StrokeCap | |
| `strokeCapEnd` | StrokeCap | |
| `strokeColorGradient` | Gradient | Gradient stroke |

### Color (for library colors, shapesColors, replaceColor)

| Property | Type | Notes |
|-|-|-|
| `color` | string | Hex e.g. `'#FF5733'` |
| `opacity` | number | |
| `gradient` | Gradient | |
| `image` | ImageData | |
| `name` | string | |
| `path` | string | Category path |
| `id` | string | External reference ID |
| `fileId` | string | External file reference |

### Gradient

```
{
  type: "linear" | "radial",
  startX: number, startY: number,
  endX: number, endY: number,
  width: number,
  stops: [{ color: string, opacity?: number, offset: number }]
}
```

## Shadow & Blur

### Shadow

| Property | Type | Notes |
|-|-|-|
| `style` | string | `"drop-shadow"` \| `"inner-shadow"` |
| `offsetX` | number | |
| `offsetY` | number | |
| `blur` | number | Blur radius |
| `spread` | number | Spread radius |
| `hidden` | boolean | |
| `color` | Color | Shadow color |

### Blur

| Property | Type | Notes |
|-|-|-|
| `type` | `"layer-blur"` | Only supported type |
| `value` | number | Intensity |
| `hidden` | boolean | |

### Blend Modes

`normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color-dodge`, `color-burn`, `hard-light`, `soft-light`, `difference`, `exclusion`, `hue`, `saturation`, `color`, `luminosity`

## Text

Properties unique to Text (extends ShapeBase):

| Property | Type | Writable |
|-|-|-|
| `type` | `"text"` | no |
| `characters` | string | yes |
| `growType` | `"fixed"` \| `"auto-width"` \| `"auto-height"` | yes |
| `fontId` | string | yes |
| `fontFamily` | string | yes |
| `fontVariantId` | string | yes |
| `fontSize` | string | yes |
| `fontWeight` | string | yes |
| `fontStyle` | `"normal"` \| `"italic"` \| `"mixed"` \| null | yes |
| `lineHeight` | string | yes |
| `letterSpacing` | string | yes |
| `textTransform` | `"uppercase"` \| `"capitalize"` \| `"lowercase"` \| `"mixed"` \| null | yes |
| `textDecoration` | `"underline"` \| `"line-through"` \| `"mixed"` \| null | yes |
| `direction` | `"ltr"` \| `"rtl"` \| `"mixed"` \| null | yes |
| `align` | `"left"` \| `"center"` \| `"right"` \| `"justify"` \| `"mixed"` \| null | yes |
| `verticalAlign` | `"top"` \| `"center"` \| `"bottom"` \| null | yes |

| Method | Returns | Purpose |
|-|-|-|
| `getRange(start, end)` | TextRange | Get substring with formatting |
| `applyTypography(typography)` | void | Apply LibraryTypography |

### TextRange

Per-character styling. Writable properties: `fontId`, `fontFamily`, `fontVariantId`, `fontSize`, `fontWeight`, `fontStyle`, `lineHeight`, `letterSpacing`, `textTransform`, `textDecoration`, `direction`, `fills`, `align`, `verticalAlign`.

Readonly: `shape` (parent Text), `characters`.

Method: `applyTypography(typography)`.

## Path

| Property | Type | Notes |
|-|-|-|
| `type` | `"path"` | |
| `d` | string | SVG path data (d attribute) |
| `commands` | PathCommand[] | Path as command array |
| `content` | string | Deprecated — use `d` |

## Flex Layout

All properties writable:

| Property | Type | Values |
|-|-|-|
| `dir` | string | `"row"` \| `"row-reverse"` \| `"column"` \| `"column-reverse"` |
| `wrap` | string | `"wrap"` \| `"nowrap"` |
| `alignItems` | string | `"start"` \| `"center"` \| `"end"` \| `"stretch"` |
| `alignContent` | string | `"start"` \| `"center"` \| `"end"` \| `"stretch"` \| `"space-between"` \| `"space-around"` \| `"space-evenly"` |
| `justifyItems` | string | same as alignItems |
| `justifyContent` | string | same as alignContent |
| `rowGap` | number | |
| `columnGap` | number | |
| `horizontalPadding` | number | Both sides |
| `verticalPadding` | number | Both sides |
| `topPadding` | number | |
| `rightPadding` | number | |
| `bottomPadding` | number | |
| `leftPadding` | number | |
| `horizontalSizing` | string | `"fill"` \| `"auto"` \| `"fix"` |
| `verticalSizing` | string | `"fill"` \| `"auto"` \| `"fix"` |

Methods: `appendChild(child)`, `remove()`.

**Gotcha:** Children array order is REVERSED for `dir="column"` or `dir="row"`.

## Grid Layout

Same alignment/padding/sizing properties as Flex, plus:

| Property | Type | Writable |
|-|-|-|
| `dir` | `"row"` \| `"column"` | yes |
| `rows` | Track[] | no |
| `columns` | Track[] | no |

| Method | Parameters | Purpose |
|-|-|-|
| `addRow(type, value?)` | TrackType | Add row |
| `addRowAtIndex(index, type, value?)` | | Insert row |
| `addColumn(type, value?)` | TrackType | Add column |
| `addColumnAtIndex(index, type, value?)` | | Insert column |
| `removeRow(index)` | | |
| `removeColumn(index)` | | |
| `setColumn(index, type, value?)` | | Update column |
| `setRow(index, type, value?)` | | Update row |
| `appendChild(child, row, column)` | | Place child at grid position |
| `remove()` | | Remove layout |

TrackType: `"flex"` | `"fixed"` | `"percent"` | `"auto"`

## Layout Child Properties

Available on any shape inside a flex/grid container via `shape.layoutChild`:

| Property | Type | Notes |
|-|-|-|
| `absolute` | boolean | Absolute positioning |
| `zIndex` | number | Stack order |
| `horizontalSizing` | string | `"fill"` \| `"auto"` \| `"fix"` |
| `verticalSizing` | string | `"fill"` \| `"auto"` \| `"fix"` |
| `alignSelf` | string | `"auto"` \| `"start"` \| `"center"` \| `"end"` \| `"stretch"` |
| `horizontalMargin` | number | Both sides |
| `verticalMargin` | number | Both sides |
| `topMargin` | number | |
| `rightMargin` | number | |
| `bottomMargin` | number | |
| `leftMargin` | number | |
| `maxWidth` | number \| null | Cap growth on wide screens — set with `horizontalSizing='fill'` |
| `maxHeight` | number \| null | Cap vertical growth — set with `verticalSizing='fill'` |
| `minWidth` | number \| null | Prevent collapse below readable width |
| `minHeight` | number \| null | Prevent collapse below usable height |

**Responsive constraint pattern:** Set sizing to `"fill"` so the child expands to use available space, then set `maxWidth`/`maxHeight` to cap growth. This creates fluid elements that fill mobile screens but stay bounded on desktop — without breakpoints.

```javascript
// Card fills container but caps at 400px wide
board.appendChild(card);
card.layoutChild.horizontalSizing = 'fill';
card.layoutChild.maxWidth = 400;
card.layoutChild.minWidth = 200;
```

### Grid Cell Properties

Via `shape.layoutCell`:

| Property | Type | Notes |
|-|-|-|
| `row` | number | Starting row |
| `rowSpan` | number | |
| `column` | number | Starting column |
| `columnSpan` | number | |
| `areaName` | string | Named grid area |
| `position` | string | `"auto"` \| `"manual"` \| `"area"` |

## Library

Access: `penpot.library.local`

| Property | Type |
|-|-|
| `id` | string (readonly) |
| `name` | string (readonly) |
| `colors` | LibraryColor[] (readonly) |
| `typographies` | LibraryTypography[] (readonly) |
| `components` | LibraryComponent[] (readonly) |
| `tokens` | TokenCatalog (readonly) |

| Method | Returns |
|-|-|
| `createColor()` | LibraryColor |
| `createTypography()` | LibraryTypography |
| `createComponent(shapes)` | LibraryComponent |

### LibraryColor

Properties: `id`, `libraryId`, `name`, `path` (string), `color` (hex), `opacity` (number), `gradient` (Gradient), `image` (ImageData).

| Method | Returns |
|-|-|
| `asFill()` | Fill |
| `asStroke()` | Stroke |

### LibraryTypography

Properties: `id`, `libraryId`, `name`, `path`, `fontId`, `fontFamilies`, `fontVariantId`, `fontSize`, `fontWeight`, `fontStyle`, `lineHeight`, `letterSpacing`, `textTransform`.

| Method | Parameters |
|-|-|
| `applyToText(shape)` | Apply to Text shape |
| `applyToTextRange(range)` | Apply to TextRange |
| `setFont(font, variant?)` | Set font and variant |

### LibraryComponent

Properties: `id`, `libraryId`, `name`, `path`.

| Method | Returns | Purpose |
|-|-|-|
| `instance()` | Shape | Create instance |
| `mainInstance()` | Shape | Reference main component |
| `isVariant()` | boolean | |
| `transformInVariant()` | void | Convert to variant |

## Design Tokens

Access: `penpot.library.local.tokens` → TokenCatalog

### TokenCatalog

| Property/Method | Type/Returns |
|-|-|
| `themes` | TokenTheme[] (readonly) |
| `sets` | TokenSet[] (readonly) |
| `addTheme({group, name})` | TokenTheme |
| `addSet({name})` | TokenSet — name can include group path with `/` |
| `getThemeById(id)` | TokenTheme \| undefined |
| `getSetById(id)` | TokenSet \| undefined |

### TokenSet

| Property/Method | Type/Returns |
|-|-|
| `id` | string |
| `name` | string (may include group path `/`) |
| `active` | boolean |
| `tokens` | Token[] (alphabetical) |
| `tokensByType` | [string, Token[]][] |
| `toggleActive()` | void |
| `getTokenById(id)` | Token \| undefined |
| `addToken({type, name, value})` | Token |
| `duplicate()` | TokenSet |
| `remove()` | void |

### TokenTheme

| Property/Method | Type/Returns |
|-|-|
| `id` | string (readonly) |
| `externalId` | string \| undefined (readonly) |
| `group` | string |
| `name` | string |
| `active` | boolean |
| `activeSets` | TokenSet[] (readonly) |
| `toggleActive()` | void |
| `addSet(tokenSet)` | void |
| `removeSet(tokenSet)` | void |
| `duplicate()` | TokenTheme |
| `remove()` | void |

### TokenType (17 types)

`"borderRadius"` | `"shadow"` | `"color"` | `"dimension"` | `"fontFamilies"` | `"fontSizes"` | `"fontWeights"` | `"letterSpacing"` | `"number"` | `"opacity"` | `"rotation"` | `"sizing"` | `"spacing"` | `"borderWidth"` | `"textCase"` | `"textDecoration"` | `"typography"`

### Applying Tokens

```javascript
shape.applyToken(token, properties?);
// properties defaults to "all"
// TokenColorProps: "fill" | "strokeColor"
// Note: "fill" maps to fillColor of the FIRST fill
```

## Page

| Property | Type |
|-|-|
| `id` | string |
| `name` | string |
| `root` | Shape — parent of all shapes |
| `rulerGuides` | RulerGuide[] |
| `flows` | Flow[] |

| Method | Returns | Purpose |
|-|-|-|
| `getShapeById(id)` | Shape \| null | Direct lookup |
| `findShapes(criteria?)` | Shape[] | Search by `{name?, nameLike?, type?}` |
| `createFlow(name, board)` | Flow | Prototyping entry point |
| `removeFlow(flow)` | void | |
| `addRulerGuide(orientation, value, board?)` | RulerGuide | |
| `removeRulerGuide(guide)` | void | |
| `addCommentThread(content, position)` | Promise\<CommentThread\> | |
| `removeCommentThread(thread)` | Promise\<void\> | |
| `findCommentThreads(criteria?)` | Promise\<CommentThread[]\> | `{onlyYours?, showResolved?}` |

## Viewport

| Property | Type | Writable | Notes |
|-|-|-|-|
| `center` | Point | yes | Setting changes viewport position |
| `zoom` | number | yes | 1 = 100% |
| `bounds` | Bounds | no | Current coordinates |

| Method | Purpose |
|-|-|
| `zoomReset()` | Reset to default |
| `zoomToFitAll()` | Fit all shapes |
| `zoomIntoView(shapes)` | Fit specified shapes |

## Events

Register: `const id = penpot.on('eventname', callback, props?)`
Remove: `penpot.off(id)`

| Event | Payload | Notes |
|-|-|-|
| `pagechange` | Page | Active page changed |
| `filechange` | File | File modified |
| `selectionchange` | string[] | Selected shape IDs |
| `themechange` | Theme | Light/dark changed |
| `finish` | string | Operation completed |
| `shapechange` | Shape | Requires `{ shapeId: '<id>' }` in props |
| `contentsave` | void | File saved |

## History / Undo

Batch operations as a single undo step:

```javascript
const blockId = penpot.history.undoBlockBegin();
// ... multiple operations ...
penpot.history.undoBlockFinish(blockId);
```

## Font Management

Access: `penpot.fonts`

| Property/Method | Returns |
|-|-|
| `all` | Font[] — all available fonts |
| `findById(id)` | Font \| null |
| `findByName(name)` | Font \| null |
| `findAllById(id)` | Font[] |
| `findAllByName(name)` | Font[] |

## Utilities

### Geometry

`penpot.utils.geometry.center(shapes)` → `{x, y} | null` — centroid of bounding boxes

### Type Guards

| Method | Type Guard |
|-|-|
| `penpot.utils.types.isBoard(shape)` | shape is Board |
| `penpot.utils.types.isGroup(shape)` | shape is Group |
| `penpot.utils.types.isMask(shape)` | shape is Group (mask) |
| `penpot.utils.types.isBool(shape)` | shape is Boolean |
| `penpot.utils.types.isRectangle(shape)` | shape is Rectangle |
| `penpot.utils.types.isPath(shape)` | shape is Path |
| `penpot.utils.types.isText(shape)` | shape is Text |
| `penpot.utils.types.isEllipse(shape)` | shape is Ellipse |
| `penpot.utils.types.isSVG(shape)` | shape is SvgRaw |
| `penpot.utils.types.isVariantContainer(shape)` | shape is VariantContainer |

## Export & Markup

| Method | Returns | Notes |
|-|-|-|
| `penpot.generateMarkup(shapes, {type?})` | string | `"html"` or `"svg"` |
| `penpot.generateStyle(shapes, options?)` | string | CSS output |
| `penpot.generateFontFaces(shapes)` | Promise\<string\> | @font-face CSS |
| `shape.export(config)` | Promise\<Uint8Array\> | Per-shape export |

---

## Snippets

Worked examples for common operations (moved from SKILL.md).

### Shape Operations

Beyond `createBoard()`, `createRectangle()`, `createText()`:

| Method | Returns | Purpose |
|-|-|-|
| `penpot.createEllipse()` | Ellipse | Circle/oval shapes |
| `penpot.createPath()` | Path | Custom vector paths |
| `penpot.createBoolean(type, shapes)` | Boolean | Union, difference, intersection, exclude |
| `penpot.createShapeFromSvg(svgString)` | Group | Import SVG as shapes |
| `penpot.group(shapes)` | Group | Group shapes together |
| `penpot.ungroup(group)` | void | Ungroup |
| `shape.clone()` | Shape | Duplicate a shape |
| `shape.remove()` | void | Delete a shape |
| `shape.rotate(angle, center?)` | void | Rotate in degrees |
| `shape.export(config)` | Promise\<Uint8Array\> | Programmatic export |

#### Z-Ordering & Alignment

```javascript
shape.bringToFront();    // top of stack
shape.bringForward();    // one step up
shape.sendToBack();      // bottom of stack
shape.sendBackward();    // one step down

penpot.alignHorizontal(shapes, 'center'); // 'left' | 'center' | 'right'
penpot.alignVertical(shapes, 'top');      // 'top' | 'center' | 'bottom'
penpot.distributeHorizontal(shapes);      // even spacing
penpot.distributeVertical(shapes);
```

### Grid Layout

Boards support grid layout in addition to flex:

```javascript
const board = penpot.createBoard();
board.resize(600, 400);
const grid = board.addGridLayout();

// Add tracks — types: "flex", "fixed", "percent", "auto"
grid.addColumn('fixed', 200);  // sidebar
grid.addColumn('flex', 1);     // main content
grid.addRow('fixed', 64);      // header
grid.addRow('flex', 1);        // body

// Place children at specific row/column
grid.appendChild(sidebar, 0, 0);   // row 0, col 0
grid.appendChild(header, 0, 1);    // row 0, col 1
grid.appendChild(content, 1, 1);   // row 1, col 1
```

Grid shares the same padding/gap/sizing properties as flex (`rowGap`, `columnGap`, `horizontalPadding`, etc.).

### Effects

```javascript
// Drop shadow
shape.shadows = [{
  style: 'drop-shadow', offsetX: 0, offsetY: 4,
  blur: 12, spread: 0,
  color: { color: '#000000', opacity: 0.15 }
}];

// Inner shadow
shape.shadows = [{ style: 'inner-shadow', offsetX: 0, offsetY: 2, blur: 4, spread: 0, color: { color: '#000000', opacity: 0.1 } }];

// Blur
shape.blur = { type: 'layer-blur', value: 8 };

// Strokes
shape.strokes = [{
  strokeColor: '#D1D5DB', strokeOpacity: 1,
  strokeStyle: 'solid',  // 'solid' | 'dotted' | 'dashed'
  strokeWidth: 1,
  strokeAlignment: 'inner' // 'center' | 'inner' | 'outer'
}];
```

Blend modes: `normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color-dodge`, `color-burn`, `hard-light`, `soft-light`, `difference`, `exclusion`, `hue`, `saturation`, `color`, `luminosity`

### Text & Typography

```javascript
// Create styled text
const text = penpot.createText('Hello World');
text.fontFamily = 'Inter';
text.fontSize = '24';
text.fontWeight = '600';
text.align = 'center';

// Per-character styling with TextRange
const range = text.getRange(0, 5); // "Hello"
range.fontWeight = '700';
range.fills = [{ fillColor: '#3B82F6' }];

// Apply library typography
const typo = penpot.library.local.typographies.find(t => t.name === 'Heading');
if (typo) text.applyTypography(typo);

// Font discovery
const inter = penpot.fonts.findByName('Inter');
const allFonts = penpot.fonts.all;
```

### Library Management

```javascript
// Create library color
const libColor = penpot.library.local.createColor();
libColor.name = 'Primary';
libColor.path = 'Brand';
libColor.color = '#3B82F6';

// Use library colors as fills/strokes
shape.fills = [libColor.asFill()];
shape.strokes = [libColor.asStroke()];

// Create library typography
const libTypo = penpot.library.local.createTypography();
libTypo.name = 'Body';
const font = penpot.fonts.findByName('Inter');
if (font) libTypo.setFont(font);
libTypo.fontSize = '16';

// Create component from shapes
const component = penpot.library.local.createComponent([shape1, shape2]);
const instance = component.instance(); // create instance

// Color operations
const colors = penpot.shapesColors(penpot.selection); // discover colors
penpot.replaceColor(penpot.selection, { color: '#FF0000' }, { color: '#3B82F6' }); // swap
```


### Page, Viewport & Events

```javascript
// Page management
const page = penpot.createPage();
page.name = 'Settings';
penpot.openPage(page);

// Find shapes on current page (built-in — no penpotUtils needed)
const buttons = penpot.currentPage.findShapes({ nameLike: 'btn-' });
const boards = penpot.currentPage.findShapes({ type: 'board' });
const shape = penpot.currentPage.getShapeById('some-id');

// Viewport control
penpot.viewport.zoomIntoView(shapes);  // zoom to fit shapes
penpot.viewport.zoomToFitAll();        // zoom to fit all
penpot.viewport.zoom = 1.5;           // set zoom level (1 = 100%)

// Events
const id = penpot.on('selectionchange', (ids) => { /* shape IDs */ });
penpot.off(id); // remove listener
// Events: pagechange, filechange, selectionchange, themechange, shapechange, contentsave

// History — batch operations as single undo step
const blockId = penpot.history.undoBlockBegin();
// ... multiple operations ...
penpot.history.undoBlockFinish(blockId);

// Upload media
const imgData = await penpot.uploadMediaUrl('logo', 'https://example.com/logo.png');
```

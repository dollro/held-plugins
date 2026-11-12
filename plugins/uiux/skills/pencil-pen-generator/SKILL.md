---
name: pencil-pen-generator
description: "Generates and converts Pencil .pen design files, the JSON format of pencil.dev: UI components, page layouts, design tokens and systems, and conversions from Vue, HTML or Figma designs into .pen. Use when the user mentions .pen files, Pencil or pencil.dev, or asks to create, edit or convert a design as .pen (\"pen file\", \"pencil design\", \"convert to pen\", \"design-as-code\")."
---

# Pencil .pen File Generator

Generate valid .pen files — the JSON-based design format used by [pencil.dev](https://pencil.dev).
The .pen format describes an object tree on an infinite 2D canvas, similar to HTML/SVG but with a component/instance system, flexbox layout, variables, and theming.

## Before You Start

Read the reference files in this skill's `references/` directory as needed:

- **`references/schema.md`** — The complete TypeScript schema. Consult this whenever you need to verify a property name, type constraint, or supported value. This is the authoritative reference.
- **`references/examples.md`** — Ready-to-use patterns for common UI elements (buttons, cards, navbars, forms, pages) and a Tailwind-to-.pen mapping table. Start here for inspiration and to match the user's Vue3/Tailwind stack.

## Core Concepts

### Document Structure

Every .pen file is a JSON object with this shape:

```json
{
  "version": "2.8",
  "themes": { ... },       // optional
  "variables": { ... },    // optional
  "imports": { ... },      // optional
  "children": [ ... ]      // required — top-level objects on the canvas
}
```

The version MUST be `"2.8"` — older versions like `"0.0.1"` are rejected by the Pencil app.

Top-level children MUST have `x` and `y` coordinates. Nested children are positioned relative to their parent (or controlled by parent's flexbox layout, in which case `x`/`y` are ignored).

### Object Types

The supported types are: `frame`, `group`, `rectangle`, `ellipse`, `line`, `path`, `polygon`, `text`, `note`, `prompt`, `context`, `icon_font`, `ref`.

Every object MUST have:
- `id` — a short random alphanumeric string (5 chars, e.g. `"xP3nL"`, `"MzSDs"`, `"6xhgh"`). No slashes allowed.
- `type` — one of the types above

**Frame** is the workhorse — a rectangle that can have children and flexbox layout. Think of it like a `<div>`.

**Text** requires careful handling of `textGrowth`: never set `width` or `height` on a text node without also setting `textGrowth`. Use `"auto"` for text that sizes itself, `"fixed-width"` for text that wraps within a set width, or `"fixed-width-height"` for fully fixed dimensions. Always include `lineHeight` (as a multiplier, e.g. `1.4286` for 14px font), `textAlign`, `textAlignVertical`, `fontFamily`, `fontSize`, and `fontWeight`.

**Ref** creates an instance of a reusable component (any object with `reusable: true`).

### Layout System

Frames support flexbox-style layout:

```json
{
  "type": "frame",
  "layout": "vertical",
  "gap": 16,
  "padding": [8, 16],
  "justifyContent": "center",
  "alignItems": "center"
}
```

**Sizing behaviors** for width/height:
- Fixed number: `"width": 200`
- `"fill_container"` — stretch to fill parent (like `w-full`)
- `"fit_content"` — shrink to fit children (like `w-fit`)
- `"fit_content(200)"` — fit children, with 200 as fallback when no children

### Graphics

**Fill** can be a simple hex color string, a variable reference like `"$--background"`, or an object with type `"color"`, `"gradient"`, `"image"`, or `"mesh_gradient"`. Multiple fills are supported as an array (painted in order).

**Stroke** is a single object with `align`, `thickness`, `fill` properties. Thickness can be a single number or per-side `{ top, right, bottom, left }`.

**Effects** can be `"blur"`, `"background_blur"`, or `"shadow"`. Shadows have `shadowType: "inner" | "outer"`.

### Components & Instances

Mark any object as reusable with `"reusable": true`. Then create instances with `"type": "ref"`:

```json
{ "id": "e8v1X", "type": "frame", "reusable": true, ... }
{ "id": "kL2mN", "type": "ref", "ref": "e8v1X", "descendants": { "Tr3Fv": { "content": "Submit" } } }
```

**Descendants** customize nested children by their `id`. For deeply nested children inside other refs, use slash-separated paths: `"sODDz/xFmFv"`.

**Object replacement** in descendants: if you include a `type` field in the descendant override, it fully replaces that node.

**Children replacement**: provide a `children` array in the descendant override to replace a frame's children (ideal for container/slot patterns).

**Slots**: mark a frame with `"slot": ["component-id-1", "component-id-2"]` to indicate it's designed to receive instances of those components.

### Variables & Theming

Variables use CSS custom property naming with `--` prefix, referenced with `$--`:

```json
{
  "variables": {
    "--primary": { "type": "color", "value": "#171717" }
  },
  "children": [
    { "id": "aB3cD", "type": "rectangle", "fill": "$--primary", ... }
  ]
}
```

Variable types: `"color"`, `"number"`, `"string"`, `"boolean"`.

For theming, give a variable multiple values. The first entry (no `theme` key) is the default. The last matching theme wins:

```json
"--background": {
  "type": "color",
  "value": [
    { "value": "#ffffff" },
    { "value": "#0a0a0a", "theme": { "Mode": "Dark" } }
  ]
}
```

Theme axes use **capitalized** names. Declare them in the document's `themes` property — the first value in each axis array is the default:

```json
"themes": {
  "Mode": ["Light", "Dark"],
  "Base": ["Neutral", "Gray", "Slate", "Zinc", "Stone"]
}
```

## Generation Guidelines

### ID Convention

Generate IDs as **5-character random alphanumeric strings** mixing upper/lowercase letters and digits (e.g. `"xP3nL"`, `"MzSDs"`, `"7kBq2"`). This matches what Pencil itself generates. IDs must be unique within the document and must not contain `/`.

### Structure Approach

1. **Start with variables** — define design tokens using `--` prefix CSS custom property names
2. **Build reusable components** — buttons, inputs, cards, etc. Mark them `reusable: true`
3. **Compose pages** from component instances (`ref`) and raw frames
4. **Add theming** if light/dark mode is needed

### Variable Naming Convention

Use CSS custom property style with `--` prefix, matching shadcn/Tailwind conventions. The standard shadcn variable set (which Pencil's built-in Shadcn UI kit uses) is:

```
--background, --foreground
--card, --card-foreground
--popover, --popover-foreground
--primary, --primary-foreground
--secondary, --secondary-foreground
--muted, --muted-foreground
--accent, --accent-foreground
--destructive
--border, --input, --ring
--sidebar, --sidebar-foreground, --sidebar-primary, --sidebar-border, --sidebar-accent, --sidebar-accent-foreground
--white, --black
```

For custom numeric tokens, use the same pattern: `--spacing-sm`, `--radius-md`, `--text-base`, etc.

### Typography Defaults

Unless the user specifies otherwise, use:
- Font family: `"Inter"`
- Font size: 14 (body), 12 (captions), 16+ (headings)
- Line height: as a multiplier, e.g. `1.4286` for 14px, `1.6667` for 12px
- Weights: `"normal"` (body), `"500"` (labels/buttons), `"600"` (headings), `"700"` (bold)
- Always set `textAlign` and `textAlignVertical` on text nodes

### Icons

Use `icon_font` type with `iconFontFamily: "lucide"`. In real Pencil files, icons are typically wrapped in a frame with `layout: "none"`:

```json
{
  "type": "frame",
  "id": "sR0hI",
  "name": "icon-wrapper",
  "width": 20,
  "height": 20,
  "stroke": { "align": "inside", "thickness": 1 },
  "layout": "none",
  "children": [{
    "type": "icon_font",
    "id": "kFgRh",
    "x": 2, "y": 2,
    "width": 16, "height": 16,
    "iconFontName": "plus",
    "iconFontFamily": "lucide",
    "fill": "$--secondary-foreground"
  }]
}
```

### When Converting from Vue/Tailwind

Consult the Tailwind mapping table in `references/examples.md`. Key mappings:
- `flex flex-col` → `layout: "vertical"`
- `flex flex-row` → `layout: "horizontal"`
- `gap-N` → `gap: N*4` (Tailwind's spacing scale)
- `p-N` → `padding: N*4`
- `w-full` → `width: "fill_container"`
- `rounded-lg` → `cornerRadius: 12`
- `shadow-md` → effect with `type: "shadow"`

When converting a Vue SFC:
1. Map the `<template>` structure to nested frames and elements
2. Extract Tailwind classes to .pen properties
3. Identify reusable sub-components and mark them `reusable: true`
4. Map CSS variables or Tailwind config values to .pen `--` variables

### Output Format

Always output the complete, valid JSON. The file should be saved with a `.pen` extension. Use 2-space indentation for readability. Use the `name` property on objects for human-readable labels (e.g. `"name": "Button/Primary"`, `"name": "Sidebar Header"`). Use the `context` field for additional notes.

### Common Pitfalls to Avoid

1. **Wrong version** — MUST be `"2.8"`, not `"0.0.1"` or anything else
2. **Descriptive IDs** — Pencil uses short random alphanumeric IDs, not kebab-case names. Use `name` for human-readable labels.
3. **Missing `x`/`y` on top-level children** — every direct child of the document `children` array needs canvas coordinates
4. **Setting `width`/`height` on text without `textGrowth`** — always set `textGrowth` first
5. **Variable names without `--` prefix** — variables must use CSS custom property naming: `--background`, not `color.background`
6. **Variable references without `$--`** — reference as `"$--background"`, not `"$background"` or `"$color.background"`
7. **Lowercase theme axes** — use `"Mode"` not `"mode"`, `"Light"` not `"light"`
8. **Slashes in IDs** — IDs must never contain `/` (slashes are used in `descendants` key paths)
9. **Non-unique IDs** — every `id` in the document must be unique
10. **Referencing undefined components** — a `ref`'s `ref` property must point to an existing object with `reusable: true`

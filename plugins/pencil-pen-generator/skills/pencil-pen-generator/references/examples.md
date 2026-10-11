# .pen Format — Common Patterns & Examples

All examples use version `"2.8"`, 5-char random alphanumeric IDs, `--` prefix variable names, and capitalized theme axes — matching real Pencil output.

## Minimal Valid Document

```json
{
  "version": "2.8",
  "children": [
    {
      "type": "frame",
      "id": "aB3cD",
      "x": 0,
      "y": 0,
      "name": "My Frame",
      "width": 400,
      "height": 300,
      "fill": "#ffffff"
    }
  ]
}
```

## Reusable Button Component (matches Pencil's shadcn pattern)

```json
{
  "type": "frame",
  "id": "e8v1X",
  "x": 0,
  "y": 0,
  "name": "Button/Primary",
  "reusable": true,
  "fill": "$--primary",
  "cornerRadius": 6,
  "gap": 6,
  "padding": [8, 16],
  "justifyContent": "center",
  "alignItems": "center",
  "children": [
    {
      "type": "frame",
      "id": "soROh",
      "name": "Leading Icon",
      "width": 20,
      "height": 20,
      "stroke": { "align": "inside", "thickness": 1 },
      "layout": "none",
      "children": [
        {
          "type": "icon_font",
          "id": "SlKX1",
          "x": 2,
          "y": 2,
          "width": 16,
          "height": 16,
          "iconFontName": "plus",
          "iconFontFamily": "lucide",
          "fill": "$--primary-foreground"
        }
      ]
    },
    {
      "type": "text",
      "id": "Tr3Fv",
      "name": "Label",
      "fill": "$--primary-foreground",
      "content": "Button",
      "lineHeight": 1.4286,
      "textAlign": "center",
      "textAlignVertical": "middle",
      "fontFamily": "Inter",
      "fontSize": 14,
      "fontWeight": "500"
    }
  ]
}
```

## Outline Button Variant

```json
{
  "type": "frame",
  "id": "C10zH",
  "x": 0,
  "y": 80,
  "name": "Button/Outline",
  "reusable": true,
  "fill": "$--background",
  "cornerRadius": 6,
  "stroke": {
    "align": "inside",
    "thickness": 1,
    "fill": "$--border"
  },
  "effect": {
    "type": "shadow",
    "shadowType": "outer",
    "color": "#0000000d",
    "offset": { "x": 0, "y": 1 },
    "blur": 1.75
  },
  "gap": 6,
  "padding": [8, 16],
  "justifyContent": "center",
  "alignItems": "center",
  "children": [
    {
      "type": "text",
      "id": "nD4kQ",
      "name": "Label",
      "fill": "$--foreground",
      "content": "Button",
      "lineHeight": 1.4286,
      "textAlign": "center",
      "textAlignVertical": "middle",
      "fontFamily": "Inter",
      "fontSize": 14,
      "fontWeight": "500"
    }
  ]
}
```

## Instance with Overrides

```json
{
  "id": "kL2mN",
  "type": "ref",
  "ref": "e8v1X",
  "x": 100,
  "y": 200,
  "descendants": {
    "Tr3Fv": {
      "content": "Submit"
    },
    "SlKX1": {
      "iconFontName": "check"
    }
  }
}
```

## Card Component with Slot

```json
{
  "type": "frame",
  "id": "pQ7rS",
  "x": 0,
  "y": 0,
  "name": "Card",
  "reusable": true,
  "width": 360,
  "height": "fit_content(200)",
  "layout": "vertical",
  "padding": 24,
  "gap": 16,
  "cornerRadius": 8,
  "fill": "$--card",
  "stroke": {
    "align": "inside",
    "thickness": 1,
    "fill": "$--border"
  },
  "effect": {
    "type": "shadow",
    "shadowType": "outer",
    "offset": { "x": 0, "y": 1 },
    "blur": 2,
    "color": "#0000000d"
  },
  "children": [
    {
      "type": "text",
      "id": "tU8vW",
      "name": "Title",
      "content": "Card Title",
      "fontFamily": "Inter",
      "fontSize": 16,
      "fontWeight": "600",
      "lineHeight": 1.5,
      "fill": "$--card-foreground"
    },
    {
      "type": "frame",
      "id": "xY9zA",
      "name": "Content",
      "width": "fill_container",
      "height": "fit_content(100)",
      "layout": "vertical",
      "gap": 8,
      "slot": ["e8v1X"]
    }
  ]
}
```

## Input Field Component

```json
{
  "type": "frame",
  "id": "bC2dE",
  "x": 0,
  "y": 200,
  "name": "Input",
  "reusable": true,
  "width": 320,
  "height": "fit_content(68)",
  "layout": "vertical",
  "gap": 6,
  "children": [
    {
      "type": "text",
      "id": "fG3hI",
      "name": "Label",
      "content": "Label",
      "fontFamily": "Inter",
      "fontSize": 14,
      "fontWeight": "500",
      "lineHeight": 1.4286,
      "fill": "$--foreground"
    },
    {
      "type": "frame",
      "id": "jK4lM",
      "name": "Input Box",
      "width": "fill_container",
      "height": 40,
      "layout": "horizontal",
      "alignItems": "center",
      "padding": [0, 12],
      "cornerRadius": 6,
      "fill": "$--background",
      "stroke": {
        "align": "inside",
        "thickness": 1,
        "fill": "$--input"
      },
      "children": [
        {
          "type": "text",
          "id": "nO5pQ",
          "name": "Placeholder",
          "content": "Placeholder...",
          "fontFamily": "Inter",
          "fontSize": 14,
          "fontWeight": "normal",
          "lineHeight": 1.4286,
          "fill": "$--muted-foreground"
        }
      ]
    }
  ]
}
```

## Variables with Light/Dark Theming (shadcn-style)

```json
{
  "version": "2.8",
  "themes": {
    "Mode": ["Light", "Dark"]
  },
  "variables": {
    "--background": {
      "type": "color",
      "value": [
        { "value": "#ffffff" },
        { "value": "#0a0a0a", "theme": { "Mode": "Dark" } }
      ]
    },
    "--foreground": {
      "type": "color",
      "value": [
        { "value": "#0a0a0a" },
        { "value": "#fafafa", "theme": { "Mode": "Dark" } }
      ]
    },
    "--primary": {
      "type": "color",
      "value": [
        { "value": "#171717" },
        { "value": "#fafafa", "theme": { "Mode": "Dark" } }
      ]
    },
    "--primary-foreground": {
      "type": "color",
      "value": [
        { "value": "#fafafa" },
        { "value": "#171717", "theme": { "Mode": "Dark" } }
      ]
    },
    "--secondary": {
      "type": "color",
      "value": [
        { "value": "#f5f5f5" },
        { "value": "#262626", "theme": { "Mode": "Dark" } }
      ]
    },
    "--secondary-foreground": {
      "type": "color",
      "value": [
        { "value": "#171717" },
        { "value": "#fafafa", "theme": { "Mode": "Dark" } }
      ]
    },
    "--muted": {
      "type": "color",
      "value": [
        { "value": "#f5f5f5" },
        { "value": "#262626", "theme": { "Mode": "Dark" } }
      ]
    },
    "--muted-foreground": {
      "type": "color",
      "value": [
        { "value": "#737373" },
        { "value": "#a3a3a3", "theme": { "Mode": "Dark" } }
      ]
    },
    "--border": {
      "type": "color",
      "value": [
        { "value": "#e5e5e5" },
        { "value": "#ffffff1a", "theme": { "Mode": "Dark" } }
      ]
    },
    "--input": {
      "type": "color",
      "value": [
        { "value": "#e5e5e5" },
        { "value": "#ffffff1a", "theme": { "Mode": "Dark" } }
      ]
    },
    "--ring": {
      "type": "color",
      "value": [
        { "value": "#a3a3a3" },
        { "value": "#737373", "theme": { "Mode": "Dark" } }
      ]
    },
    "--destructive": {
      "type": "color",
      "value": [
        { "value": "#e7000b" },
        { "value": "#ff666999", "theme": { "Mode": "Dark" } }
      ]
    },
    "--card": {
      "type": "color",
      "value": [
        { "value": "#ffffff" },
        { "value": "#0a0a0a", "theme": { "Mode": "Dark" } }
      ]
    },
    "--card-foreground": {
      "type": "color",
      "value": [
        { "value": "#0a0a0a" },
        { "value": "#fafafa", "theme": { "Mode": "Dark" } }
      ]
    },
    "--accent": {
      "type": "color",
      "value": [
        { "value": "#f5f5f5" },
        { "value": "#262626", "theme": { "Mode": "Dark" } }
      ]
    },
    "--accent-foreground": {
      "type": "color",
      "value": [
        { "value": "#171717" },
        { "value": "#fafafa", "theme": { "Mode": "Dark" } }
      ]
    },
    "--white": { "type": "color", "value": "#ffffffff" },
    "--black": { "type": "color", "value": "#000000" }
  },
  "children": []
}
```

## Page-Level Layout (Vertical Stack)

```json
{
  "type": "frame",
  "id": "rS1tU",
  "x": 0,
  "y": 0,
  "name": "Page",
  "width": 1440,
  "height": "fit_content(900)",
  "layout": "vertical",
  "fill": "$--background",
  "children": [
    {
      "type": "frame",
      "id": "vW2xY",
      "name": "Header",
      "width": "fill_container",
      "height": 64,
      "layout": "horizontal",
      "justifyContent": "space_between",
      "alignItems": "center",
      "padding": [0, 24],
      "fill": "$--background",
      "stroke": {
        "align": "inside",
        "thickness": { "bottom": 1 },
        "fill": "$--border"
      }
    },
    {
      "type": "frame",
      "id": "zA3bC",
      "name": "Main Content",
      "width": "fill_container",
      "height": "fit_content(600)",
      "layout": "vertical",
      "padding": 24,
      "gap": 16
    },
    {
      "type": "frame",
      "id": "dE4fG",
      "name": "Footer",
      "width": "fill_container",
      "height": 80,
      "layout": "horizontal",
      "alignItems": "center",
      "padding": [0, 24]
    }
  ]
}
```

## Converting Tailwind/Vue Patterns

When converting from Vue3 + Tailwind, map these common patterns:

| Tailwind Class | .pen Equivalent |
|-|-|
| `flex flex-col` | `layout: "vertical"` |
| `flex flex-row` | `layout: "horizontal"` |
| `gap-4` | `gap: 16` |
| `p-4` | `padding: 16` |
| `px-4 py-2` | `padding: [8, 16]` |
| `items-center` | `alignItems: "center"` |
| `justify-between` | `justifyContent: "space_between"` |
| `justify-center` | `justifyContent: "center"` |
| `rounded-md` | `cornerRadius: 6` |
| `rounded-lg` | `cornerRadius: 12` |
| `w-full` | `width: "fill_container"` |
| `h-auto` / `h-fit` | `height: "fit_content"` |
| `text-sm` (14px) | `fontSize: 14` |
| `font-medium` | `fontWeight: "500"` |
| `font-semibold` | `fontWeight: "600"` |
| `bg-white` | `fill: "#ffffff"` |
| `border border-gray-200` | `stroke: { align: "inside", thickness: 1, fill: "#e5e5e5" }` |
| `shadow-sm` | `effect: { type: "shadow", shadowType: "outer", offset: { x: 0, y: 1 }, blur: 1.75, color: "#0000000d" }` |
| `overflow-hidden` | `clip: true` |
| `opacity-50` | `opacity: 0.5` |

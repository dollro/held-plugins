# Starter Token Template

A minimal but complete design token set in W3C DTCG format. Use as scaffolding for new projects — adapt to your brand and needs.

> **This is a starting point, not a prescription.** Rename, remove, or extend tokens to match your project. The structure and naming conventions matter more than the specific values.

## Primitive Tokens

```json
{
  "color": {
    "neutral": {
      "$type": "color",
      "50": { "$value": "#fafafa" }, "100": { "$value": "#f5f5f5" }, "200": { "$value": "#e5e5e5" },
      "300": { "$value": "#d4d4d4" }, "400": { "$value": "#a3a3a3" }, "500": { "$value": "#737373" },
      "600": { "$value": "#525252" }, "700": { "$value": "#404040" }, "800": { "$value": "#262626" },
      "900": { "$value": "#171717" }, "950": { "$value": "#0a0a0a" }
    },
    "primary": {
      "$type": "color",
      "50": { "$value": "#eff6ff" }, "100": { "$value": "#dbeafe" }, "200": { "$value": "#bfdbfe" },
      "300": { "$value": "#93c5fd" }, "400": { "$value": "#60a5fa" }, "500": { "$value": "#3b82f6" },
      "600": { "$value": "#2563eb" }, "700": { "$value": "#1d4ed8" }, "800": { "$value": "#1e40af" },
      "900": { "$value": "#1e3a8a" }, "950": { "$value": "#172554" }
    },
    "success": { "$type": "color", "base": { "$value": "#22c55e" }, "light": { "$value": "#bbf7d0" }, "dark": { "$value": "#15803d" } },
    "warning": { "$type": "color", "base": { "$value": "#eab308" }, "light": { "$value": "#fef08a" }, "dark": { "$value": "#a16207" } },
    "danger": { "$type": "color", "base": { "$value": "#ef4444" }, "light": { "$value": "#fecaca" }, "dark": { "$value": "#b91c1c" } },
    "info": { "$type": "color", "base": { "$value": "#06b6d4" }, "light": { "$value": "#a5f3fc" }, "dark": { "$value": "#0e7490" } }
  },
  "font": {
    "family": {
      "sans": { "$type": "fontFamily", "$value": ["Inter", "system-ui", "sans-serif"] },
      "mono": { "$type": "fontFamily", "$value": ["JetBrains Mono", "Fira Code", "monospace"] }
    },
    "size": {
      "$type": "dimension",
      "100": { "$value": { "value": 0.75, "unit": "rem" } }, "200": { "$value": { "value": 0.875, "unit": "rem" } },
      "300": { "$value": { "value": 1, "unit": "rem" } }, "400": { "$value": { "value": 1.125, "unit": "rem" } },
      "500": { "$value": { "value": 1.25, "unit": "rem" } }, "600": { "$value": { "value": 1.5, "unit": "rem" } },
      "700": { "$value": { "value": 1.875, "unit": "rem" } }, "800": { "$value": { "value": 2.25, "unit": "rem" } },
      "900": { "$value": { "value": 3, "unit": "rem" } }
    },
    "weight": {
      "$type": "fontWeight",
      "regular": { "$value": 400 }, "medium": { "$value": 500 },
      "semibold": { "$value": 600 }, "bold": { "$value": 700 }
    },
    "line-height": {
      "$type": "number",
      "tight": { "$value": 1.25 }, "normal": { "$value": 1.5 }, "relaxed": { "$value": 1.75 }
    },
    "letter-spacing": {
      "$type": "dimension",
      "tight": { "$value": { "value": -0.025, "unit": "em" } },
      "normal": { "$value": { "value": 0, "unit": "em" } },
      "wide": { "$value": { "value": 0.025, "unit": "em" } }
    },
    "paragraph-spacing": {
      "$type": "dimension",
      "none": { "$value": { "value": 0, "unit": "rem" } },
      "md": { "$value": { "value": 1, "unit": "rem" } }
    }
  },
  "space": {
    "$type": "dimension", "$description": "4px base grid",
    "1": { "$value": { "value": 0.25, "unit": "rem" } }, "2": { "$value": { "value": 0.5, "unit": "rem" } },
    "3": { "$value": { "value": 0.75, "unit": "rem" } }, "4": { "$value": { "value": 1, "unit": "rem" } },
    "6": { "$value": { "value": 1.5, "unit": "rem" } }, "8": { "$value": { "value": 2, "unit": "rem" } },
    "12": { "$value": { "value": 3, "unit": "rem" } }, "16": { "$value": { "value": 4, "unit": "rem" } }
  },
  "scale": {
    "$type": "dimension", "$description": "4px base grid — unified number scale for spacing, sizing, borders",
    "0": { "$value": { "value": 0, "unit": "px" } },
    "25": { "$value": { "value": 1, "unit": "px" }, "$description": "Exception: borders" },
    "50": { "$value": { "value": 2, "unit": "px" }, "$description": "Exception: focus rings" },
    "100": { "$value": { "value": 4, "unit": "px" } },
    "200": { "$value": { "value": 8, "unit": "px" } },
    "300": { "$value": { "value": 12, "unit": "px" } },
    "400": { "$value": { "value": 16, "unit": "px" } },
    "500": { "$value": { "value": 20, "unit": "px" } },
    "600": { "$value": { "value": 24, "unit": "px" } },
    "700": { "$value": { "value": 28, "unit": "px" } },
    "800": { "$value": { "value": 32, "unit": "px" } },
    "900": { "$value": { "value": 36, "unit": "px" } },
    "1000": { "$value": { "value": 40, "unit": "px" } },
    "1100": { "$value": { "value": 48, "unit": "px" } },
    "1200": { "$value": { "value": 64, "unit": "px" } }
  },
  "border": {
    "width": {
      "$type": "dimension",
      "1": { "$value": { "value": 1, "unit": "px" } },
      "2": { "$value": { "value": 2, "unit": "px" } },
      "4": { "$value": { "value": 4, "unit": "px" } }
    },
    "style": {
      "$type": "strokeStyle",
      "solid": { "$value": "solid" },
      "dashed": { "$value": "dashed" }
    }
  },
  "radius": {
    "$type": "dimension",
    "none": { "$value": { "value": 0, "unit": "px" } }, "xs": { "$value": { "value": 2, "unit": "px" } },
    "s": { "$value": { "value": 4, "unit": "px" } }, "m": { "$value": { "value": 8, "unit": "px" } },
    "l": { "$value": { "value": 12, "unit": "px" } }, "xl": { "$value": { "value": 16, "unit": "px" } },
    "full": { "$value": { "value": 9999, "unit": "px" } }
  },
  "shadow": {
    "elevation": {
      "$type": "shadow",
      "1": { "$value": { "color": "#0000000d", "offsetX": { "value": 0, "unit": "px" }, "offsetY": { "value": 1, "unit": "px" }, "blur": { "value": 3, "unit": "px" }, "spread": { "value": 0, "unit": "px" } } },
      "2": { "$value": { "color": "#0000001a", "offsetX": { "value": 0, "unit": "px" }, "offsetY": { "value": 4, "unit": "px" }, "blur": { "value": 8, "unit": "px" }, "spread": { "value": -2, "unit": "px" } } },
      "3": { "$value": { "color": "#00000026", "offsetX": { "value": 0, "unit": "px" }, "offsetY": { "value": 10, "unit": "px" }, "blur": { "value": 20, "unit": "px" }, "spread": { "value": -4, "unit": "px" } } }
    }
  },
  "motion": {
    "duration": {
      "$type": "duration",
      "instant": { "$value": { "value": 0, "unit": "ms" } },
      "fast": { "$value": { "value": 150, "unit": "ms" } },
      "normal": { "$value": { "value": 300, "unit": "ms" } },
      "slow": { "$value": { "value": 500, "unit": "ms" } }
    },
    "easing": {
      "$type": "cubicBezier",
      "ease-out": { "$value": [0.0, 0.0, 0.58, 1.0] },
      "ease-in-out": { "$value": [0.42, 0.0, 0.58, 1.0] },
      "linear": { "$value": [0.0, 0.0, 1.0, 1.0] }
    }
  },
  "opacity": {
    "$type": "number",
    "subtle": { "$value": 0.15 }, "medium": { "$value": 0.5 },
    "strong": { "$value": 0.75 }, "opaque": { "$value": 1.0 }
  },
  "size": {
    "$type": "dimension",
    "icon": {
      "sm": { "$value": { "value": 1, "unit": "rem" } },
      "md": { "$value": { "value": 1.25, "unit": "rem" } },
      "lg": { "$value": { "value": 1.5, "unit": "rem" } }
    },
    "avatar": {
      "sm": { "$value": { "value": 2, "unit": "rem" } },
      "md": { "$value": { "value": 2.5, "unit": "rem" } },
      "lg": { "$value": { "value": 3, "unit": "rem" } }
    }
  }
}
```

## Semantic Tokens

```json
{
  "color": {
    "background": {
      "$type": "color",
      "surface": { "$value": "{color.neutral.50}" }, "subtle": { "$value": "{color.neutral.100}" },
      "primary": { "$value": "{color.primary.500}" }, "danger": { "$value": "{color.danger.light}" },
      "warning": { "$value": "{color.warning.light}" }, "success": { "$value": "{color.success.light}" },
      "info": { "$value": "{color.info.light}" }
    },
    "text": {
      "$type": "color",
      "primary": { "$value": "{color.neutral.900}" }, "secondary": { "$value": "{color.neutral.600}" },
      "disabled": { "$value": "{color.neutral.400}" }, "on-primary": { "$value": "{color.neutral.50}" },
      "danger": { "$value": "{color.danger.dark}" }, "success": { "$value": "{color.success.dark}" }
    },
    "border": {
      "$type": "color",
      "default": { "$value": "{color.neutral.200}" }, "strong": { "$value": "{color.neutral.400}" }, "interactive": { "$value": "{color.primary.500}" },
      "focus-ring": { "$value": "{color.primary.500}" }
    },
    "interactive": {
      "$type": "color",
      "default": { "$value": "{color.primary.500}" }, "hover": { "$value": "{color.primary.600}" }, "active": { "$value": "{color.primary.700}" }
    },
    "feedback": {
      "$type": "color",
      "success": { "$value": "{color.success.base}" }, "warning": { "$value": "{color.warning.base}" },
      "danger": { "$value": "{color.danger.base}" }, "info": { "$value": "{color.info.base}" }
    }
  },
  "font": {
    "heading": {
      "$type": "typography",
      "xl": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.800}", "fontWeight": "{font.weight.bold}", "lineHeight": "{font.line-height.tight}", "letterSpacing": "{font.letter-spacing.tight}" } },
      "lg": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.600}", "fontWeight": "{font.weight.semibold}", "lineHeight": "{font.line-height.tight}", "letterSpacing": "{font.letter-spacing.tight}" } },
      "md": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.500}", "fontWeight": "{font.weight.semibold}", "lineHeight": "{font.line-height.tight}", "letterSpacing": "{font.letter-spacing.tight}" } }
    },
    "body": {
      "$type": "typography",
      "default": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.300}", "fontWeight": "{font.weight.regular}", "lineHeight": "{font.line-height.normal}", "letterSpacing": "{font.letter-spacing.normal}" } },
      "small": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.200}", "fontWeight": "{font.weight.regular}", "lineHeight": "{font.line-height.normal}", "letterSpacing": "{font.letter-spacing.normal}" } }
    },
    "caption": {
      "$type": "typography",
      "default": { "$value": { "fontFamily": "{font.family.sans}", "fontSize": "{font.size.100}", "fontWeight": "{font.weight.medium}", "lineHeight": "{font.line-height.normal}", "letterSpacing": "{font.letter-spacing.normal}" } }
    }
  },
  "space": {
    "inline": {
      "$type": "dimension",
      "sm": { "$value": "{space.2}" }, "md": { "$value": "{space.4}" }, "lg": { "$value": "{space.8}" }
    },
    "stack": {
      "$type": "dimension",
      "sm": { "$value": "{space.2}" }, "md": { "$value": "{space.4}" }, "lg": { "$value": "{space.8}" }
    },
    "inset": {
      "$type": "dimension",
      "sm": { "$value": "{space.2}" }, "md": { "$value": "{space.4}" }, "lg": { "$value": "{space.6}" }
    }
  },
  "shadow": {
    "card": { "$type": "shadow", "$value": "{shadow.elevation.1}" },
    "dropdown": { "$type": "shadow", "$value": "{shadow.elevation.2}" },
    "overlay": { "$type": "shadow", "$value": "{shadow.elevation.3}" }
  },
  "opacity": {
    "disabled": { "$type": "number", "$value": "{opacity.medium}" },
    "overlay": { "$type": "number", "$value": "{opacity.strong}" }
  },
  "border": {
    "focus-ring": {
      "$type": "border",
      "$value": {
        "color": "{color.border.focus-ring}",
        "width": { "value": 2, "unit": "px" },
        "style": "solid"
      }
    }
  },
  "size": {
    "touch-target": {
      "$type": "dimension",
      "min": { "$value": { "value": 24, "unit": "px" } },
      "comfortable": { "$value": { "value": 44, "unit": "px" } }
    }
  },
  "z": {
    "$type": "number",
    "base": { "$value": 0 },
    "dropdown": { "$value": 1000 },
    "sticky": { "$value": 1100 },
    "modal": { "$value": 1300 },
    "toast": { "$value": 1400 }
  },
  "breakpoint": {
    "$type": "dimension",
    "sm": { "$value": { "value": 640, "unit": "px" } },
    "md": { "$value": { "value": 768, "unit": "px" } },
    "lg": { "$value": { "value": 1024, "unit": "px" } },
    "xl": { "$value": { "value": 1280, "unit": "px" } }
  }
}
```

## Mapped / Component Tokens (Tier 3)

The mapped tier defines the four token categories that get applied directly to components. Each references semantic tokens — never raw values.

> **Note:** This tier is optional for small projects. Start with primitives + semantics. Add mapped tokens when you need component-specific divergence or multi-brand/dark mode support. Production systems with dark mode should always include this tier.

```json
{
  "text": {
    "$type": "color",
    "heading": { "$value": "{color.text.primary}" },
    "body": { "$value": "{color.text.secondary}" },
    "action": { "$value": "{color.interactive.default}" },
    "action-hover": { "$value": "{color.interactive.hover}" },
    "on-action": { "$value": "{color.text.on-primary}" },
    "disabled": { "$value": "{color.text.disabled}" },
    "success": { "$value": "{color.feedback.success}" },
    "warning": { "$value": "{color.feedback.warning}" },
    "error": { "$value": "{color.feedback.danger}" },
    "information": { "$value": "{color.feedback.info}" }
  },
  "icon": {
    "$type": "color",
    "$description": "Icon tokens mirror text tokens — icons next to text should share the same color",
    "default": { "$value": "{color.text.secondary}" },
    "action": { "$value": "{color.interactive.default}" },
    "on-action": { "$value": "{color.text.on-primary}" },
    "disabled": { "$value": "{color.text.disabled}" },
    "success": { "$value": "{color.feedback.success}" },
    "error": { "$value": "{color.feedback.danger}" }
  },
  "surface": {
    "$type": "color",
    "page": { "$value": "#ffffff", "$description": "Full page background" },
    "default": { "$value": "{color.background.surface}" },
    "action": { "$value": "{color.interactive.default}" },
    "action-hover": { "$value": "{color.interactive.hover}" },
    "action-hover-light": { "$value": "{color.background.info}", "$description": "Subtle hover for inputs/rows" },
    "disabled": { "$value": "{color.background.subtle}" },
    "success": { "$value": "{color.background.success}" },
    "warning": { "$value": "{color.background.warning}" },
    "error": { "$value": "{color.background.danger}" },
    "information": { "$value": "{color.background.info}" }
  },
  "border": {
    "$type": "color",
    "default": { "$value": "{color.border.default}" },
    "action": { "$value": "{color.interactive.default}" },
    "action-hover": { "$value": "{color.interactive.hover}" },
    "focus": { "$value": "{color.border.focus-ring}" },
    "disabled": { "$value": "{color.border.default}" },
    "success": { "$value": "{color.feedback.success}" },
    "warning": { "$value": "{color.feedback.warning}" },
    "error": { "$value": "{color.feedback.danger}" },
    "information": { "$value": "{color.feedback.info}" }
  }
}
```

---

## Scaling Up

This starter template uses minimal stops for feedback colors (base/light/dark). For production design systems with dark mode support, expand each feedback color to a full 50–950 shade range — same structure as the `primary` and `neutral` scales. This enables the mapped tier's light/dark mode tables (e.g., `surface/error` maps to `error.50` in light mode and `error.900` in dark mode).

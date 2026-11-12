# .pen Format — TypeScript Schema Reference

This is the **authoritative, exhaustive** schema for all supported types and properties in .pen files.
When generating .pen files, every property and type used MUST conform to this schema.

## Core Types

```ts
/** Each key must be an existing theme axis, and each value must be one of the possible values for that axis. E.g. { 'device': 'phone' } */
export interface Theme {
  [key: string]: string;
}

/** To bind a variable to a property, set the property to the dollar-prefixed name of the variable! */
export type Variable = string;

export type NumberOrVariable = number | Variable;

/** Colors can be 8-digit RGBA hex strings (e.g. #AABBCCDD), 6-digit RGB hex strings (e.g. #AABBCC) or 3-digit RGB hex strings (e.g. #ABC which means #AABBCC). */
export type Color = string;

export type ColorOrVariable = Color | Variable;

export type BooleanOrVariable = boolean | Variable;

export type StringOrVariable = string | Variable;
```

## Layout

```ts
export interface Layout {
  /** Enable flex layout. None means all children are absolutely positioned and will not be affected by layout properties. Frames default to horizontal, groups default to none. */
  layout?: "none" | "vertical" | "horizontal";
  /** The gap between children in the main axis direction. Defaults to 0. */
  gap?: NumberOrVariable;
  layoutIncludeStroke?: boolean;
  /** The Inside padding along the edge of the container */
  padding?:
    | /** The inside padding to all sides */ NumberOrVariable
    | /** The inside horizontal and vertical padding */ [
        NumberOrVariable,
        NumberOrVariable,
      ]
    | /** Top, Right, Bottom, Left padding */ [
        NumberOrVariable,
        NumberOrVariable,
        NumberOrVariable,
        NumberOrVariable,
      ];
  /** Control the justify alignment of the children along the main axis. Defaults to 'start'. */
  justifyContent?:
    | "start"
    | "center"
    | "end"
    | "space_between"
    | "space_around";
  /** Control the alignment of children along the cross axis. Defaults to 'start'. */
  alignItems?: "start" | "center" | "end";
}
```

## Sizing

```ts
/** SizingBehavior controls the dynamic layout size.
- fit_content: Use the combined size of all children for the container size. Fallback is used when there are no children.
- fill_container: Use the parent size for the container size. Fallback is used when the parent has no layout.
Optional number in parentheses (e.g., 'fit_content(100)') specifies the fallback size. */
export type SizingBehavior = string;

export interface Position {
  x?: number;
  y?: number;
}

export interface Size {
  width?: NumberOrVariable | SizingBehavior;
  height?: NumberOrVariable | SizingBehavior;
}

export interface CanHaveRotation {
  /** Rotation is represented in degrees, measured counter-clockwise. */
  rotation?: NumberOrVariable;
}
```

## Graphics — Fills, Strokes, Effects

```ts
export type BlendMode =
  | "normal"
  | "darken"
  | "multiply"
  | "linearBurn"
  | "colorBurn"
  | "light"
  | "screen"
  | "linearDodge"
  | "colorDodge"
  | "overlay"
  | "softLight"
  | "hardLight"
  | "difference"
  | "exclusion"
  | "hue"
  | "saturation"
  | "color"
  | "luminosity";

export type Fill =
  | ColorOrVariable
  | {
      type: "color";
      enabled?: BooleanOrVariable;
      blendMode?: BlendMode;
      color: ColorOrVariable;
    }
  | {
      type: "gradient";
      enabled?: BooleanOrVariable;
      blendMode?: BlendMode;
      gradientType?: "linear" | "radial" | "angular";
      opacity?: NumberOrVariable;
      center?: Position;
      size?: { width?: NumberOrVariable; height?: NumberOrVariable };
      rotation?: NumberOrVariable;
      colors?: { color: ColorOrVariable; position: NumberOrVariable }[];
    }
  | {
      type: "image";
      enabled?: BooleanOrVariable;
      blendMode?: BlendMode;
      opacity?: NumberOrVariable;
      url: string;
      mode?: "stretch" | "fill" | "fit";
    }
  | {
      type: "mesh_gradient";
      enabled?: BooleanOrVariable;
      blendMode?: BlendMode;
      opacity?: NumberOrVariable;
      columns?: number;
      rows?: number;
      colors?: ColorOrVariable[];
      points?: (
        | [number, number]
        | {
            position: [number, number];
            leftHandle?: [number, number];
            rightHandle?: [number, number];
            topHandle?: [number, number];
            bottomHandle?: [number, number];
          }
      )[];
    };

export type Fills = Fill | Fill[];

export interface Stroke {
  align?: "inside" | "center" | "outside";
  thickness?:
    | NumberOrVariable
    | {
        top?: NumberOrVariable;
        right?: NumberOrVariable;
        bottom?: NumberOrVariable;
        left?: NumberOrVariable;
      };
  join?: "miter" | "bevel" | "round";
  miterAngle?: NumberOrVariable;
  cap?: "none" | "round" | "square";
  dashPattern?: number[];
  fill?: Fills;
}

export type Effect =
  | { enabled?: BooleanOrVariable; type: "blur"; radius?: NumberOrVariable }
  | {
      enabled?: BooleanOrVariable;
      type: "background_blur";
      radius?: NumberOrVariable;
    }
  | {
      type: "shadow";
      enabled?: BooleanOrVariable;
      shadowType?: "inner" | "outer";
      offset?: { x: NumberOrVariable; y: NumberOrVariable };
      spread?: NumberOrVariable;
      blur?: NumberOrVariable;
      color?: ColorOrVariable;
      blendMode?: BlendMode;
    };

export type Effects = Effect | Effect[];
```

## Entity Base & Object Types

```ts
export interface CanHaveGraphics {
  stroke?: Stroke;
  fill?: Fills;
  effect?: Effects;
}

export interface CanHaveEffects {
  effect?: Effects;
}

export interface Entity extends Position, CanHaveRotation {
  /** A unique string that MUST NOT contain slash (/) characters. If omitted, a unique ID will be generated automatically. */
  id: string;
  name?: string;
  context?: string;
  reusable?: boolean;
  theme?: Theme;
  enabled?: BooleanOrVariable;
  opacity?: NumberOrVariable;
  flipX?: BooleanOrVariable;
  flipY?: BooleanOrVariable;
  metadata?: { type: string; [key: string]: any };
}

export interface Rectangleish extends Entity, Size, CanHaveGraphics {
  cornerRadius?:
    | NumberOrVariable
    | [NumberOrVariable, NumberOrVariable, NumberOrVariable, NumberOrVariable];
}
```

### Rectangle
```ts
export interface Rectangle extends Rectangleish {
  type: "rectangle";
}
```

### Ellipse
```ts
export interface Ellipse extends Entity, Size, CanHaveGraphics {
  type: "ellipse";
  innerRadius?: NumberOrVariable;
  startAngle?: NumberOrVariable;
  sweepAngle?: NumberOrVariable;
}
```

### Line
```ts
export interface Line extends Entity, Size, CanHaveGraphics {
  type: "line";
}
```

### Polygon
```ts
export interface Polygon extends Entity, Size, CanHaveGraphics {
  type: "polygon";
  polygonCount?: NumberOrVariable;
  cornerRadius?: NumberOrVariable;
}
```

### Path
```ts
export interface Path extends Entity, Size, CanHaveGraphics {
  fillRule?: "nonzero" | "evenodd";
  geometry?: string;
  type: "path";
}
```

### Text
```ts
export interface TextStyle {
  fontFamily?: StringOrVariable;
  fontSize?: NumberOrVariable;
  fontWeight?: StringOrVariable;
  letterSpacing?: NumberOrVariable;
  fontStyle?: StringOrVariable;
  underline?: BooleanOrVariable;
  lineHeight?: NumberOrVariable;
  textAlign?: "left" | "center" | "right" | "justify";
  textAlignVertical?: "top" | "middle" | "bottom";
  strikethrough?: BooleanOrVariable;
  href?: string;
}

export type TextContent = StringOrVariable | TextStyle[];

export interface Text extends Entity, Size, CanHaveGraphics, TextStyle {
  type: "text";
  content?: TextContent;
  /** IMPORTANT: Never set width or height without also setting textGrowth. */
  textGrowth?: "auto" | "fixed-width" | "fixed-width-height";
}
```

### Frame (container with children)
```ts
export interface CanHaveChildren {
  children?: Child[];
}

export interface Frame extends Rectangleish, CanHaveChildren, Layout {
  type: "frame";
  clip?: BooleanOrVariable;
  placeholder?: boolean;
  slot?: string[];
}
```

### Group
```ts
export interface Group extends Entity, CanHaveChildren, CanHaveEffects, Layout {
  type: "group";
  width?: SizingBehavior;
  height?: SizingBehavior;
}
```

### Note, Prompt, Context
```ts
export interface Note extends Entity, Size, TextStyle {
  type: "note";
  content?: TextContent;
}

export interface Prompt extends Entity, Size, TextStyle {
  type: "prompt";
  content?: TextContent;
  model?: StringOrVariable;
}

export interface Context extends Entity, Size, TextStyle {
  type: "context";
  content?: TextContent;
}
```

### IconFont
```ts
export interface IconFont extends Entity, Size, CanHaveEffects {
  type: "icon_font";
  iconFontName?: StringOrVariable;
  /** Valid fonts: 'lucide', 'feather', 'Material Symbols Outlined', 'Material Symbols Rounded', 'Material Symbols Sharp', 'phosphor' */
  iconFontFamily?: StringOrVariable;
  weight?: NumberOrVariable;
  fill?: Fills;
}
```

### Ref (instance of a reusable component)
```ts
export interface Ref extends Entity {
  type: "ref";
  ref: string;
  descendants?: {
    [key: string]: {};
  };
  [key: string]: any;
}
```

## Child & Document Types

```ts
export type Child =
  | Frame
  | Group
  | Rectangle
  | Ellipse
  | Line
  | Path
  | Polygon
  | Text
  | Note
  | Prompt
  | Context
  | IconFont
  | Ref;

export interface Document {
  version: string;
  themes?: { [key: string]: string[] };
  imports?: {
    [key: string]: string;
  };
  variables?: {
    [key: string]:
      | {
          type: "boolean";
          value: BooleanOrVariable | { value: BooleanOrVariable; theme?: Theme }[];
        }
      | {
          type: "color";
          value: ColorOrVariable | { value: ColorOrVariable; theme?: Theme }[];
        }
      | {
          type: "number";
          value: NumberOrVariable | { value: NumberOrVariable; theme?: Theme }[];
        }
      | {
          type: "string";
          value: StringOrVariable | { value: StringOrVariable; theme?: Theme }[];
        };
  };
  children: (
    | Frame
    | Group
    | Rectangle
    | Ellipse
    | Line
    | Polygon
    | Path
    | Text
    | Note
    | Context
    | Prompt
    | IconFont
    | Ref
  )[];
}
```

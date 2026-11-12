# Figma Console MCP — Tool Reference

Complete catalog of tools provided by `figma-console-mcp`. All write tools require the
Desktop Bridge plugin running in Figma Desktop. Mode column indicates availability:
**All** = any connection, **Local** = NPX/Git only, **Local/Cloud** = NPX/Git or Cloud relay.

---

## Navigation and Status

| Tool | Mode | Description |
|-|-|-|
| `figma_navigate` | All | Open a Figma URL and start monitoring |
| `figma_get_status` | All | Check connection, transport, and WebSocket status |
| `figma_reconnect` | Local | Reconnect to Figma Desktop |

### `figma_navigate`

```
{ url: string }
```

Returns: navigation status, current URL, console monitoring state.

### `figma_get_status`

No parameters. Returns `setup.valid`, `setup.transport` (`websocket` or `none`),
active file key, connected port, and other instance info.

---

## Console Debugging

| Tool | Mode | Description |
|-|-|-|
| `figma_get_console_logs` | All | Retrieve console logs with count/level/since filters |
| `figma_watch_console` | All | Stream logs in real-time for a duration (max 300 s) |
| `figma_clear_console` | All | Clear the log buffer |
| `figma_reload_plugin` | All | Reload the current Figma page |

### `figma_get_console_logs`

```
{ count?: number, level?: 'log'|'info'|'warn'|'error'|'debug'|'all', since?: number }
```

Returns: array of `{ timestamp, level, message, args, stackTrace }`.

---

## Visual Debugging

### `figma_take_screenshot`

```
{ target?: 'plugin'|'full-page'|'viewport', format?: 'png'|'jpeg', quality?: number, filename?: string }
```

Returns: screenshot image and metadata.

---

## Design System Extraction

| Tool | Mode | Description |
|-|-|-|
| `figma_get_design_system_kit` | All | Full design system in one call (tokens, components, styles, visual specs) |
| `figma_get_variables` | All | Extract design tokens/variables with optional enrichment |
| `figma_get_styles` | All | Get color, text, effect, grid styles |
| `figma_get_component` | All | Component metadata or reconstruction spec |
| `figma_get_component_for_development` | All | Component data + rendered image for UI implementation |
| `figma_get_component_image` | All | Render a node as PNG/JPG/SVG/PDF |
| `figma_get_file_data` | All | File structure with verbosity control (`summary`/`standard`/`full`) |
| `figma_get_file_for_plugin` | All | File data optimized for plugin work (depth up to 5) |
| `figma_get_design_system_summary` | Local/Cloud | High-level design system overview |
| `figma_get_token_values` | Local/Cloud | Variable values filtered by mode |

### `figma_get_design_system_kit`

```
{ fileKey?: string, include?: ('tokens'|'components'|'styles')[],
  componentIds?: string[], includeImages?: boolean,
  format?: 'full'|'summary'|'compact' }
```

Returns: `{ tokens, components, styles, ai_instruction }`. Adaptive compression
for large payloads. `visualSpec` on components includes fills, strokes, effects,
cornerRadius, layout (auto-layout props), and typography.

### `figma_get_variables`

```
{ fileUrl?: string, includePublished?: boolean, enrich?: boolean,
  export_formats?: ('css'|'tailwind'|'sass')[], include_usage?: boolean,
  include_dependencies?: boolean, refreshCache?: boolean }
```

Supports branch URLs. Falls back to Styles API if Enterprise Variables API is unavailable.

### `figma_get_component`

```
{ fileUrl?: string, nodeId: string, format?: 'metadata'|'reconstruction', enrich?: boolean }
```

`reconstruction` format returns full node tree spec compatible with Figma Component Reconstructor.

---

## Design Creation

| Tool | Mode | Description |
|-|-|-|
| `figma_execute` | Local/Cloud | Run arbitrary Figma Plugin API code |
| `figma_arrange_component_set` | Local/Cloud | Organize variants into a labeled component set grid |
| `figma_set_description` | Local/Cloud | Add markdown descriptions to components/styles |

### `figma_execute`

```
{ code: string, timeout?: number }
```

> The power tool. Has full access to the `figma` global object. Use `await` for
> async operations (`figma.loadFontAsync`, `figma.getNodeByIdAsync`). Max timeout 30 000 ms.

**Runtime context inside `code`:**

- `figma` — full Figma Plugin API
- `figma.currentPage` — active page
- `figma.viewport.center` — current viewport center (for positioning)
- `figma.variables` — variable/collection CRUD
- Must `return` a value to get results back
- Fonts must be loaded before setting text: `await figma.loadFontAsync({ family, style })`

**Return:** `{ success, result, error, resultAnalysis, fileContext }`.
Check `resultAnalysis.warning` for silent failures (empty arrays, null returns).

### `figma_arrange_component_set`

```
{ componentSetId?: string, componentSetName?: string,
  options?: { gap?: number, cellPadding?: number, columnProperty?: string } }
```

Creates white container frame with title, row labels, column headers, and Figma's
native purple dashed border visualization.

---

## Component Tools

| Tool | Mode | Description |
|-|-|-|
| `figma_search_components` | Local/Cloud | Find components by name (local + published library) |
| `figma_get_library_components` | Local | Discover published library components with variant detail |
| `figma_get_component_details` | Local/Cloud | Full component details by key |
| `figma_instantiate_component` | Local/Cloud | Create a component instance on canvas |
| `figma_add_component_property` | Local/Cloud | Add BOOLEAN/TEXT/INSTANCE_SWAP/VARIANT property |
| `figma_edit_component_property` | Local/Cloud | Edit existing component property |
| `figma_delete_component_property` | Local/Cloud | Remove a component property |

### `figma_instantiate_component`

```
{ componentKey?: string, nodeId?: string, x?: number, y?: number,
  overrides?: Record<string, any> }
```

> Always pass **both** `componentKey` and `nodeId` for automatic fallback. Re-search
> at the start of each session — nodeIds are session-specific.

---

## Variable Management

| Tool | Mode | Description |
|-|-|-|
| `figma_create_variable_collection` | Local/Cloud | Create collection with optional modes |
| `figma_create_variable` | Local/Cloud | Create COLOR/FLOAT/STRING/BOOLEAN variable |
| `figma_update_variable` | Local/Cloud | Update a variable value in a mode |
| `figma_rename_variable` | Local/Cloud | Rename variable (preserves values) |
| `figma_delete_variable` | Local/Cloud | Delete a variable |
| `figma_delete_variable_collection` | Local/Cloud | Delete collection and all its variables |
| `figma_add_mode` | Local/Cloud | Add mode to collection (Light, Dark, etc.) |
| `figma_rename_mode` | Local/Cloud | Rename existing mode |
| `figma_batch_create_variables` | Local/Cloud | Create up to 100 variables in one call (10-50x faster) |
| `figma_batch_update_variables` | Local/Cloud | Update up to 100 variable values in one call |
| `figma_setup_design_tokens` | Local/Cloud | Atomic: collection + modes + variables in one call |

### `figma_setup_design_tokens`

```
{ collectionName: string, modes: string[], tokens: { name, resolvedType, description?, values }[] }
```

Values are keyed by **mode name** (not mode ID). Ideal for bootstrapping entire token systems.

### `figma_batch_create_variables`

```
{ collectionId: string, variables: { name, resolvedType, description?, valuesByMode? }[] }
```

Up to 100 variables per call. Single Plugin API roundtrip.

### Value Formats

| Type | Format | Example |
|-|-|-|
| COLOR | hex string | `'#3B82F6'` or `'#3B82F6FF'` |
| FLOAT | number | `16` or `1.5` |
| STRING | text | `'Hello World'` |
| BOOLEAN | boolean | `true` / `false` |

---

## Node Manipulation

| Tool | Mode | Parameters |
|-|-|-|
| `figma_resize_node` | Local/Cloud | `{ nodeId, width, height }` |
| `figma_move_node` | Local/Cloud | `{ nodeId, x, y }` |
| `figma_clone_node` | Local/Cloud | `{ nodeId }` |
| `figma_delete_node` | Local/Cloud | `{ nodeId }` |
| `figma_rename_node` | Local/Cloud | `{ nodeId, newName }` |
| `figma_set_text` | Local/Cloud | `{ nodeId, characters }` |
| `figma_set_fills` | Local/Cloud | `{ nodeId, fills }` |
| `figma_set_strokes` | Local/Cloud | `{ nodeId, strokes, strokeWeight? }` |
| `figma_create_child` | Local/Cloud | `{ parentId, type, name }` |
| `figma_set_image_fill` | Local/Cloud | `{ nodeId, imageUrl }` |

---

## Design-Code Parity

| Tool | Mode | Description |
|-|-|-|
| `figma_check_design_parity` | All | Compare Figma component specs against code, returns scored diff |
| `figma_generate_component_doc` | All | Generate markdown docs merging Figma data with code info |

---

## Design Lint

### `figma_lint_design`

Mode: Local/Cloud. WCAG accessibility and design quality checks on the current file.

---

## Comments

| Tool | Mode | Description |
|-|-|-|
| `figma_get_comments` | All | Get comments on a Figma file |
| `figma_post_comment` | All | Post a comment, optionally pinned to a node |
| `figma_delete_comment` | All | Delete a comment by ID |

---

## Cloud Relay

### `figma_pair_plugin`

Mode: Cloud. Generate a 6-character pairing code for the Desktop Bridge plugin.
Code expires in 5 minutes. After pairing, all Local/Cloud tools become available
through the cloud relay.

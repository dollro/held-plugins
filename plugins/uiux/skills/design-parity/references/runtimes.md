# Runtime Adapters

`parity.config.yaml → runtime:` selects how browser operations are dispatched.

|-|-|
| Value | Behavior |
| `auto` | detect in order: `mcp-playwright` → `mcp-chrome-devtools` → `node-playwright` |
| `node-playwright` | bundled Node runtime shells out to Playwright directly |
| `mcp-playwright` | emit a JSON plan; caller executes via Playwright MCP tools |
| `mcp-chrome-devtools` | emit a JSON plan; caller executes via Chrome DevTools MCP |

## Why this matters

When Claude Code is invoked in a session that already has a Playwright MCP or Chrome-DevTools MCP server connected, spawning a second browser is wasteful and occasionally broken (port clashes, profile locks, permission prompts). The adapter lets the skill run identically whether it's a plain dev box or an MCP-assisted agent loop.

## Detection rules (runtime: auto)

1. `PARITY_RUNTIME=<name>` — hard override.
2. `PARITY_MCP_PLAYWRIGHT=1` — use Playwright MCP.
3. `PARITY_MCP_CHROME_DEVTOOLS=1` — use Chrome DevTools MCP.
4. `playwright` resolvable from `node_modules` — use Node runtime.
5. Fail with a remediation message.

Agents: set the matching env var at the start of the session so subsequent `parity run` calls pick up the right adapter.

## MCP plan shape

`parity plan` prints JSON like:

```json
{
  "iteration": 3,
  "runtime": "mcp-playwright",
  "plans": [
    {
      "screen": "dashboard",
      "viewport": [1440, 900],
      "steps": [
        { "tool": "browser_new_page", "args": {} },
        { "tool": "browser_resize", "args": { "width": 1440, "height": 900 } },
        { "tool": "browser_navigate", "args": { "url": "http://localhost:3000/dashboard", "waitUntil": "networkidle" } },
        { "tool": "browser_evaluate", "args": { "script": "/* stabilization IIFE */" } },
        { "tool": "browser_take_screenshot", "args": { "path": ".parity/runs/dashboard/iteration_3/impl.png" } },
        { "tool": "browser_close", "args": {} }
      ],
      "followup": { "note": "After steps, run diff.mjs locally to finish the iteration." }
    }
  ]
}
```

The calling agent iterates `steps[]` and dispatches each via the relevant MCP tool. `__parity_note__` entries are directives for the agent, not real tool calls — skip them.

## Stabilization is the same everywhere

Regardless of runtime, every screenshot goes through the same pipeline:

1. Disable CSS animations + transitions (init script / pre-nav evaluate).
2. Navigate with `networkidle`.
3. `await document.fonts.ready`.
4. Finish Web Animations via `getAnimations().finish()`.
5. Scroll full page height to trigger lazy images, then scroll to top.
6. Settle (400ms).
7. Apply masks: selectors (visibility:hidden), regions (opaque overlay), regex-over-text (whitespace replacement).
8. Capture.

If you ever find yourself adapting stabilization per runtime, stop — you'll get drift. All three adapters emit the same JS.

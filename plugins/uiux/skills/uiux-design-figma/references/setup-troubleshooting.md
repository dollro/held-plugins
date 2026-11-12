# Setup and Troubleshooting — figma-console-mcp

Installation, connection, and common issue resolution for the Figma Console MCP server.

---

## Prerequisites

- **Node.js 18+** — check with `node --version` ([download](https://nodejs.org))
- **Figma Desktop** installed (not the web app — required for Desktop Bridge plugin)
- **Figma Personal Access Token** — create at
  [Manage personal access tokens](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)
  (starts with `figd_`)
- **An MCP client** — Claude Code, Cursor, Windsurf, or Claude Desktop

---

## Installation (NPX — Recommended)

### Step 1: Add MCP Server to Claude Code

```bash
claude mcp add figma-console -s user \
  -e FIGMA_ACCESS_TOKEN=figd_YOUR_TOKEN_HERE \
  -e ENABLE_MCP_APPS=true \
  -- npx -y figma-console-mcp@latest
```

For other clients, add to the MCP config file:

```json
{
  "mcpServers": {
    "figma-console": {
      "command": "npx",
      "args": ["-y", "figma-console-mcp@latest"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "figd_YOUR_TOKEN_HERE",
        "ENABLE_MCP_APPS": "true"
      }
    }
  }
}
```

### Step 2: Install Desktop Bridge Plugin

1. Open Figma Desktop (normal launch — no special flags)
2. Go to **Plugins > Development > Import plugin from manifest...**
3. Select `~/.figma-console-mcp/plugin/manifest.json` (auto-created by MCP server)
4. Run the plugin in your Figma file

> **One-time import.** The plugin uses a bootloader that dynamically loads fresh
> code from the MCP server. No re-import needed when the server updates.

### Step 3: Verify Connection

```
Check Figma status
```

Expected response:
```json
{
  "setup": {
    "valid": true,
    "message": "Figma Desktop connected via WebSocket (Desktop Bridge Plugin)"
  }
}
```

---

## Cloud Relay Mode (Web AI Clients)

For Claude.ai, v0, Replit, or Lovable — no Node.js required. Add MCP endpoint
`https://figma-console-mcp.southleft.com/mcp`, open the Desktop Bridge plugin,
tell your AI "Connect to my Figma plugin", and enter the 6-character pairing code.

---

## Port Configuration

WebSocket defaults to port **9223**, auto-falls back through **9224-9232**.

| Variable | Default | Purpose |
|-|-|-|
| `FIGMA_WS_PORT` | `9223` | Preferred WebSocket port |
| `FIGMA_WS_HOST` | `localhost` | Bind address (`0.0.0.0` for Docker) |

---

## Common Issues

### Plugin Shows "Disconnected"

**Cause:** MCP server is not running.
**Fix:** Start or restart your MCP client so the MCP server process starts.

### Plugin Not Appearing in Development Plugins

**Cause:** Plugin manifest not imported.
**Fix:** Plugins > Development > Import plugin from manifest... >
select `~/.figma-console-mcp/plugin/manifest.json`.

### Port 9223 Already in Use

**Cause:** Orphaned MCP process from a closed tab.
**Fix:** The server (v1.14+) auto-cleans orphaned processes on startup and falls
back to the next port. Restart your MCP client to trigger cleanup.

### Plugin Shows "MCP scanning" or "No MCP server found"

**Cause:** No MCP server running, or all ports 9223-9232 are occupied.
**Fix:** Ensure an MCP client is running with figma-console-mcp configured. Check
`figma_get_status` from your AI client.

### Claude Code OAuth Completes But Connection Fails

**Cause:** Known bug in Claude Code's native SSE transport.
**Fix:** Use `mcp-remote` instead:

```bash
claude mcp add figma-console -s user \
  -- npx -y mcp-remote@latest https://figma-console-mcp.southleft.com/sse
```

### Commands Timeout Despite Plugin Connected

**Cause:** Plugin running in a different Figma file than expected.
**Fix:** The MCP server routes to the active file. Ensure the plugin is running
in the target file. Use `figma_get_status` to see connected files.

### Variables API Returns Empty (Enterprise Limitation)

**Cause:** Figma Variables REST API requires Enterprise plan.
**Fix:** Use the Desktop Bridge plugin — it accesses variables via the Plugin API
on all plans. MCP tools fall back to the plugin transport automatically.

### Docker Setup

Set `FIGMA_WS_HOST=0.0.0.0` and expose port: `docker run -e FIGMA_WS_HOST=0.0.0.0 -p 9223:9223 ...`

---

## Multi-Instance Support

Multiple instances run simultaneously (Chat + Code tabs). Each claims the next
port in 9223-9232. The plugin connects to all active servers automatically.

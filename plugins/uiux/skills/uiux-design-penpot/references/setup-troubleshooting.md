# Penpot MCP Server Setup & Troubleshooting

> Covers the MCP server **built into Penpot** (integrated in 2.15, current as of 2.18). The standalone `penpot/penpot-mcp` repo (local ports 4400-4403, `npm run bootstrap`) is archived. Its code now lives in `penpot/penpot/mcp`. Don't set it up for new projects.
> Sources: https://help.penpot.app/mcp/, https://github.com/penpot/penpot/blob/develop/mcp/README.md, Penpot CHANGES.md. Verified on Penpot 2.18.5.

## Contents

- Architecture Overview
- Server Side (Self-Hosted Admin)
- User Side
- Verifying the Setup
- Long-Running Sessions
- Upstream Status (Oct 2026)
- Troubleshooting
- Getting Help
- Old Patterns

---

## Architecture Overview

```
MCP client (Claude Code, Claude Desktop, Cursor, ...)
        |  Streamable HTTP
        v
https://<penpot-host>/mcp/stream?userToken=<MCP key>
        |  frontend nginx proxies to penpot-mcp:4401
        v
penpot-mcp service  <--- WebSocket /mcp/ws (penpot-mcp:4402) --->  Penpot browser tab
                                                                   (File → MCP Server → Connect)
```

The MCP server runs code by sending it to a **Penpot browser tab with a design file open**. Without a connected tab, every tool call fails.

---

## Server Side (Self-Hosted Admin)

1. Add `enable-mcp` to `PENPOT_FLAGS` (it is not on by default). `disable-mcp` turns it off.
2. Add the `penpot-mcp` service, as in the official compose file:
   ```yaml
   penpot-mcp:
     image: penpotapp/mcp:${PENPOT_VERSION:-2.18}
     networks: [penpot]
   ```
   Then make `penpot-frontend` depend on it. Reference: https://github.com/penpot/penpot/blob/main/docker/images/docker-compose.yaml
3. When the flag is set, the frontend nginx proxies two paths:
   - `/mcp/stream` → `PENPOT_MCP_URI` (default `http://penpot-mcp:4401`), query string kept
   - `/mcp/ws` → `PENPOT_MCP_URI_WS` (default `http://penpot-mcp:4402`), WebSocket upgrade
4. **An external reverse proxy** (Traefik, Caddy, another nginx) must forward both paths and allow the **WebSocket upgrade on `/mcp/ws`**.
5. Useful server env vars (see mcp/README.md):

| Variable | Purpose |
|-|-|
| `PENPOT_MCP_TOOL_TIMEOUT_S` | Per-tool execution timeout (default 120). Raise it (e.g. 300) for bulk work such as token sweeps; most 120 s timeouts in practice were slow batches, not failures |
| `PENPOT_MCP_REDIS_URI` | Shared state when running several MCP instances |
| `PENPOT_MCP_REMOTE_MODE` | Remote mode (the default for the built-in deployment) |

The legacy SSE endpoint is not proxied on 2.18 and was removed in 2.19. Use `/mcp/stream` only.

---

## User Side

### Step 1: Create the MCP Key

**Your account → Integrations → MCP Server**
1. Turn on the **Status** toggle.
2. Create the MCP key and pick an expiry: never, 30, 60, 90 or 180 days.
3. Copy the full server URL: `https://<penpot-host>/mcp/stream?userToken=<key>`

There is one key per user. Regenerating it revokes the old key immediately. Since 2.18 the key is not accepted as a general API access token.

**The key is a secret.** It grants write access to every file you can open. Keep it out of committed config and use local or user scope.

### Step 2: Connect a Penpot Tab

1. Open a design file in Penpot.
2. **File → MCP Server → Connect.**
3. MCP is active in **one tab only**. Choose that tab with the MCP status button. Tools act on the focused page of that file.
4. Keep that tab open and in the foreground if you can. Browsers throttle or freeze background tabs, and tasks fail until the tab is focused again.

### Step 3: Configure the MCP Client

**Claude Code (CLI)**, using local scope so the key stays out of the repo:
```bash
claude mcp add --transport http --scope local penpot "https://<penpot-host>/mcp/stream?userToken=<key>"
claude mcp get penpot   # should show: Status ✔ Connected, Type: http
```

**The key ends up in the transcript.** Even with the `!` prefix, the `claude mcp add ... userToken=<key>` command line is echoed into the conversation. If that matters, add the server by editing `~/.claude.json` directly instead, or regenerate the MCP key afterwards (verified on 2.18, Oct 2026).

**Claude Desktop / claude.ai**: add a custom connector at claude.ai/customize/connectors with the URL above. Alternatively, use the stdio bridge:
```json
{
  "mcpServers": {
    "penpot": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://<penpot-host>/mcp/stream?userToken=<key>"]
    }
  }
}
```

**Other clients (Cursor, VS Code, ...)**: the Penpot docs suggest `npx -y add-mcp -g -n penpot "<URL>"`. Or add an HTTP/streamable MCP server with the same URL in the client's MCP config.

Restart the client after changing its config.

---

## Verifying the Setup

1. `claude mcp get penpot` shows **Connected**. This proves only the HTTP endpoint and key work.
2. Call `mcp__penpot__high_level_overview` once per session (the server asks for this).
3. Run a smoke test through `execute_code`. It needs the browser tab:
   ```javascript
   return { version: penpot.version, file: penpot.currentFile?.name, page: penpot.currentPage?.name };
   ```
   A version and file name back means the tab is connected.

### Checking the Endpoint Without the Client

If the client tools are unavailable, you can still test the endpoint over plain HTTP (Streamable HTTP, JSON-RPC). Verified on 2.18, Oct 2026.

1. POST `initialize` to `https://<penpot-host>/mcp/stream?userToken=<key>` with headers `Content-Type: application/json` and `Accept: application/json, text/event-stream`.
2. Take the `Mcp-Session-Id` response header and send it on every following request.
3. POST `notifications/initialized`.
4. POST `tools/list` or `tools/call`. Responses arrive as SSE `data:` lines.

The built-in server reports `serverInfo` name `penpot`, version `1.0.0`, and exposes 4 tools: `execute_code`, `high_level_overview`, `penpot_api_info`, `export_shape`. A `tools/call` of `execute_code` still needs the connected tab.

---

## Long-Running Sessions

**Status: verified on 2.18, Oct 2026** (bulk token binding, ~900 `applyToken` calls over many `execute_code` calls)

How execution works: each `execute_code` call is queued **per tab** and runs in the browser. The server stops waiting after `PENPOT_MCP_TOOL_TIMEOUT_S` (120 s), but the tab keeps working.

- A write call that timed out (`Task <id> timed out after 120 seconds`) had in fact finished all its work (167 `applyToken` calls). Another finished only part of its batch (160 of 231).
- After a suspension, even a trivial read-only call timed out, because the tab was still draining the earlier queued task.
- Reloading or restarting the tab wipes `storage` (`typeof storage.verifyPage === "undefined"`). Everything written to the design file persists.

Checklist:

- [ ] **Keep the Penpot tab focused.** In the background the browser suspends it: calls hang until the timeout, then fail with `The Penpot plugin tab appears to be suspended by the browser (no heartbeat for Ns)`.
- [ ] **Cap batches.** ~80 `applyToken` calls per call was too slow on a 112-shape page; 40 per call was reliable. Give write helpers a `max` parameter and return the remaining count.
- [ ] **Verify before retry.** After a timeout or suspension, never re-run blindly. Wait, then run a cheap read-only check of the intended end state.
- [ ] **Make writes idempotent.** Every batch skips items that are already done (for tokens: the toggle guard), so re-running is always safe.
- [ ] **Keep plans re-derivable.** Put helper and plan definitions in one self-contained, re-runnable snippet. Compute the plan deterministically from the file, so after a reload you re-run the snippet and resume from the "already bound" count.

---

## Upstream Status (Oct 2026)

**Checked 2026-10-26 against the penpot/penpot repo.** Latest stable is **2.18.5**; 2.19 is unreleased on `develop`. There is no RC or nightly image: the `penpotapp/*:develop` Docker tag is years old, so running `develop` means building it yourself. Recommendation: stay on the latest 2.18.x and use the workarounds in this skill; re-check when 2.19 ships.

| Problem | Upstream status |
|-|-|
| Background tab suspended / disconnects | Open: issue [#11885](https://github.com/penpot/penpot/issues/11885). Open PRs: [#12494](https://github.com/penpot/penpot/pull/12494) (configurable heartbeat threshold), [#12415](https://github.com/penpot/penpot/pull/12415) (recover stalled WebSocket). Fixed for 2.19: endless reconnect loop in inactive tabs ([#11510](https://github.com/penpot/penpot/issues/11510)) |
| 120 s tool timeout, no cancel/progress | Timeout is configurable since [#10953](https://github.com/penpot/penpot/issues/10953); no cancel or progress API. Related open issue: [#12060](https://github.com/penpot/penpot/issues/12060) (tab saturates on large files) |
| `storage` lost on tab reload | No change found; `storage` is still in-memory |
| `applyToken` toggle | Open PR [#10668](https://github.com/penpot/penpot/pull/10668) states `applyToken` "stays idempotent" (applying twice leaves it applied). Not verified on 2.18.5: keep the toggle guard |
| `['fontFamilies']` property throws | Fixed for 2.19 ([#11566](https://github.com/penpot/penpot/pull/11566)) |
| `export_shape` with `"page"` returns 500 | No fix found. 2.19 adds export jobs ([#11296](https://github.com/penpot/penpot/pull/11296)), which may change this |
| Shadow `resolvedValue` throws | No newer fix found; still seen on 2.18.5 |

Watch [#12494](https://github.com/penpot/penpot/pull/12494) and [#10668](https://github.com/penpot/penpot/pull/10668): together they would remove most of the session friction.

---

## Troubleshooting

| Symptom | Cause / Fix |
|-|-|
| Client can't connect, 401/403 | Key wrong, expired or regenerated. Create a new key and update the client URL |
| 404 on `/mcp/stream` | `enable-mcp` missing from `PENPOT_FLAGS`, `penpot-mcp` service not running, or the reverse proxy doesn't forward `/mcp/stream` |
| Client connected, but `execute_code` says no plugin/instance is connected | No Penpot tab connected. Open a file → File → MCP Server → Connect |
| Penpot tab can't connect | Reverse proxy doesn't forward the WebSocket upgrade on `/mcp/ws` |
| Tool calls hang or time out | MCP tab is in the background or frozen. Focus it. Split long scripts. The timeout is `PENPOT_MCP_TOOL_TIMEOUT_S`. A timed-out call may still have completed in the tab, so verify before re-running (see Long-Running Sessions) |
| `The Penpot plugin tab appears to be suspended by the browser (no heartbeat for Ns)` | Browser suspended the background tab. Ask the user to click or focus the Penpot tab, then retry. A script that was running may have executed partway, so check for leftovers. Calls queued before it run first, so the next call may time out too |
| Claude Code: Penpot tools unavailable, ToolSearch reports `ECONNREFUSED`, although `claude mcp get penpot` shows Connected | The session started while the server was unreachable. Run `/mcp` and reconnect `penpot`. A new `claude mcp add` alone doesn't fix the running session |
| `typeof storage.<helper> === "undefined"` after a while | The tab was reloaded and `storage` was wiped. Re-run the helper snippet and re-derive the plan from the file |
| `export_shape` with `shapeId: "page"` returns HTTP 500 (`locator.waitFor: Timeout 10000ms exceeded`) | Seen on a components page on 2.18. Export the top-level boards by id instead |
| Works, then stops after a while | Idle sessions close after ~60 min. Reconnect the tab and restart the client session |
| Code acts on the wrong file/page | Another tab holds the MCP connection. Pick the right tab with the status button. Check `penpot.currentFile.name` |
| `Permission user:read is not granted` | 2.18 manifest omits `user:read` (fixed in 2.19). Don't read `penpot.currentUser` / `activeUsers` |
| `import_image` tool missing | Not registered in remote mode. Use `penpot.uploadMediaUrl()` or `createShapeFromSvg()` inside `execute_code` |
| `export_shape` can't save to a path | Remote mode returns the image inline only |
| Endless reconnects in an inactive tab | Known 2.18 bug (fixed in 2.19). Reload the tab and reconnect |

---

## Getting Help

- Penpot MCP docs: https://help.penpot.app/mcp/
- Server source and env vars: https://github.com/penpot/penpot/tree/develop/mcp
- Community: https://community.penpot.app
- API-level bugs and workarounds: [mcp-known-issues.md](mcp-known-issues.md)

---

## Old Patterns

<details>
<summary>Standalone penpot-mcp server (Penpot ≤2.14, archived)</summary>

Before 2.15 the MCP server ran locally from `github.com/penpot/penpot-mcp` (`npm install && npm run bootstrap`). The Penpot plugin loaded from `http://localhost:4400/manifest.json`, MCP clients connected to `http://localhost:4401/sse` (or `/mcp`), the WebSocket ran on 4402 and a REPL on 4403. That server exposed an extra `import_image` tool. The repo is archived. Upgrade Penpot and use the built-in server instead.

</details>

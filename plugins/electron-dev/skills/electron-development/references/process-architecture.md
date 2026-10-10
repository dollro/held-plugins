# Process Architecture

## Process Roles

| Process | Runs | Has access to | Use for |
|-|-|-|-|
| Main | Node + Electron main APIs | everything | app lifecycle, windows, menus, IPC handlers, file system, DB, secrets |
| Preload | before page scripts, isolated world | `contextBridge`, `ipcRenderer`, `webUtils`, `webFrame` (sandboxed subset) | exposing a narrow typed API to the page |
| Renderer | Chromium page, sandboxed | web APIs + `window.api` only | UI |
| Utility | Node child via `utilityProcess.fork` | Node, `MessagePortMain`, no Electron UI APIs | heavy, untrusted or crash-prone work |

Rule: the renderer is untrusted. Everything it asks for goes through a validated IPC contract (see typed-ipc.md, security.md).

## Module Format (ESM)

- Write main with ESM syntax; what runs is the bundle. Forge's Vite template emits main as CommonJS (`.vite/build/main.cjs`, referenced by `"main"` in `package.json`), so `__dirname` works and is the convention in this skill, and top-level `await` does not (use `app.whenReady().then(...)` or an async `main()` you call). Electron can also run an ESM main (`"type": "module"` or `.mjs`); only if you switch the main build to ESM, use `import.meta.dirname` and `await` pre-`ready` setup (e.g. `protocol.registerSchemesAsPrivileged`) at top level.
- Sandboxed preloads cannot be ESM. Bundle the preload to a single CommonJS file (Forge's Vite plugin does this). ESM preloads only work as `.mjs` with `sandbox: false`, which you should not do.
- A sandboxed preload's `require` only resolves a small set: `electron` (contextBridge, ipcRenderer, webFrame, webUtils, nativeImage, crashReporter) plus `events`, `timers`, `url`. Anything else must be bundled in.
- If you use another toolchain or change the main Vite config, check whether the bundled main is ESM or CJS and match `__dirname` vs `import.meta.dirname` to the output.

Docs: https://www.electronjs.org/docs/latest/tutorial/esm

## Main Process Setup

```typescript
// src/main/main.ts
import { app, BrowserWindow, nativeTheme } from 'electron';
import path from 'node:path';
import { registerIpc } from './ipc';
import { loadWindowState, trackWindowState } from './window-state'; // see app-lifecycle.md

let mainWindow: BrowserWindow | null = null;

function createWindow(): void {
  const state = loadWindowState();
  mainWindow = new BrowserWindow({
    ...state.bounds,
    minWidth: 800,
    minHeight: 600,
    show: false, // avoid white flash
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#1a1a1a' : '#ffffff',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
    },
  });
  if (state.isMaximized) mainWindow.maximize();
  trackWindowState(mainWindow);
  mainWindow.once('ready-to-show', () => mainWindow?.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    void mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    void mainWindow.loadURL('app://atlas/index.html'); // custom protocol, see security.md
  }
}

// Single instance, deep links, quit handling: app-lifecycle.md
if (!app.requestSingleInstanceLock()) {
  app.quit(); // async: register nothing else in this instance
} else {
  app.on('second-instance', () => {
    if (mainWindow?.isMinimized()) mainWindow.restore();
    mainWindow?.focus();
  });
  app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  // No top-level await: Forge's Vite plugin bundles main as CommonJS
  void app.whenReady().then(() => { registerIpc(); createWindow(); });
}
```

## Renderer Process

The renderer sees only what the preload exposes. Subscriptions return an unsubscribe function; call it on teardown.

```typescript
// src/renderer/update-banner.ts
const off = window.api.onUpdateReady((info) => showUpdateBanner(info.version));
// framework teardown (onUnmounted / useEffect cleanup):
off();

const { content } = await window.api.readDocument({ id: documentId }); // id issued by main
```

## Multiple Views: BaseWindow + WebContentsView

`BrowserView` is deprecated since v30. Compose windows from `BaseWindow` and `WebContentsView` instead.

```typescript
import { BaseWindow, WebContentsView } from 'electron';

const win = new BaseWindow({ width: 1200, height: 800 });

const sidebar = new WebContentsView({ webPreferences: { preload: PRELOAD, sandbox: true } });
const content = new WebContentsView({ webPreferences: { sandbox: true } }); // remote page, no preload

win.contentView.addChildView(sidebar);
win.contentView.addChildView(content);

function layout(): void {
  const { width, height } = win.getContentBounds();
  sidebar.setBounds({ x: 0, y: 0, width: 280, height });
  content.setBounds({ x: 280, y: 0, width: width - 280, height });
}
win.on('resize', layout);
layout();

void sidebar.webContents.loadURL('app://atlas/sidebar.html');
void content.webContents.loadURL('https://docs.acme.example');

win.on('closed', () => {
  sidebar.webContents.close(); // views are not destroyed with the window
  content.webContents.close();
});
```

## Embedding Web Content

| Option | Use for | Notes |
|-|-|-|
| `WebContentsView` | Third-party or remote content (docs, OAuth pages, customer sites) | Own `webContents`, own session, controlled entirely from main. The default |
| `<webview>` | Avoid | Disabled by default (`webviewTag: false`); security.md blocks `will-attach-webview`. The Electron docs advise against it (architecture in flux); it is configured from the less trusted page |
| `<iframe>` | Same-trust content only (your own `app://` pages) | Shares the embedding page's session and permission handlers; the preload does not run in subframes, and `assertTrustedSender` rejects other origins |

Isolate third-party content:

```typescript
// src/main/embedded-view.ts
import { session, WebContentsView } from 'electron';

const EMBED_HOST = 'docs.acme.example';
const embedSession = session.fromPartition('persist:embed-docs'); // no cookies/storage shared with the app

embedSession.setPermissionRequestHandler((_wc, _permission, callback) => callback(false));
embedSession.setPermissionCheckHandler(() => false);

export function createEmbeddedView(): WebContentsView {
  const view = new WebContentsView({
    webPreferences: { session: embedSession, sandbox: true, contextIsolation: true }, // no preload
  });
  const isAllowed = (raw: string) => {
    try { const u = new URL(raw); return u.protocol === 'https:' && u.hostname === EMBED_HOST; }
    catch { return false; }
  };
  view.webContents.on('will-navigate', (e, url) => { if (!isAllowed(url)) e.preventDefault(); });
  view.webContents.on('will-redirect', (e, url) => { if (!isAllowed(url)) e.preventDefault(); });
  view.webContents.setWindowOpenHandler(() => ({ action: 'deny' })); // or openExternalSafe(url)
  return view;
}
```

- No preload means the embedded page has no `window.api`; if it needs to talk to the app, use a dedicated, minimal preload and a separate contract, never the app's `AtlasApi`.
- Use a non-`persist:` partition when nothing should survive a restart (one-off OAuth flows).
- The app-wide `web-contents-created` handlers (security.md) still apply; the per-view handlers narrow them to one host.

## Utility Process for Heavy Work

`utilityProcess.fork` replaces `child_process.fork` and `ELECTRON_RUN_AS_NODE` (which stop working once the `RunAsNode` fuse is off). Use it for indexing, sync engines, native-module work, untrusted parsers: a crash there does not take down main.

```typescript
// src/main/indexer.ts
import { utilityProcess, type UtilityProcess } from 'electron';
import path from 'node:path';

let child: UtilityProcess | null = null;

export function startIndexer(): UtilityProcess {
  child = utilityProcess.fork(path.join(__dirname, 'indexer-worker.cjs'), [], {
    serviceName: 'atlas-indexer',
    stdio: 'pipe',
  });
  child.on('message', (msg: IndexerEvent) => handleIndexerEvent(msg));
  child.on('exit', (code) => {
    child = null;
    if (code !== 0) scheduleRestart(); // back off, don't loop tightly
  });
  return child;
}

export const indexFolder = (dir: string) => child?.postMessage({ type: 'index', dir });
```

```typescript
// src/workers/indexer-worker.ts (built as a separate entry)
process.parentPort.on('message', async ({ data }) => {
  if (data.type === 'index') {
    const count = await indexDirectory(data.dir);
    process.parentPort.postMessage({ type: 'done', count });
  }
});
```

`worker_threads` in main are still fine for short, pure CPU work (hashing, parsing) that cannot crash the process. Native modules (e.g. better-sqlite3) belong in main or a utility process, never the renderer.

Docs: https://www.electronjs.org/docs/latest/api/utility-process

## MessagePorts Brokered by Main

For high-volume streams (renderer to utility process, renderer to renderer), main creates a channel and hands one end to each side, then steps out of the data path.

The request goes through the contract channel `indexer:connect` (typed-ipc.md), so the usual sender and payload checks run; only the port itself travels by `postMessage`, on a name declared in the contract's `portChannels`.

```typescript
// src/main/indexer.ts (handler for 'indexer:connect')
import { MessageChannelMain, type WebContents } from 'electron';
import { portChannels } from '../shared/ipc-contract';

export function connectIndexer(sender: WebContents): void {
  const { port1, port2 } = new MessageChannelMain();
  indexer.postMessage({ type: 'port' }, [port1]);
  sender.postMessage(portChannels.indexer, null, [port2]);
}
```

```typescript
// src/preload/preload.ts: forward the port to the page's main world (type-only import keeps zod out)
import type { PortChannel } from '../shared/ipc-contract';
const INDEXER_PORT = 'indexer:port' satisfies PortChannel;
ipcRenderer.on(INDEXER_PORT, (event) => {
  window.postMessage(INDEXER_PORT, '*', event.ports);
});
```

The page calls `await window.api.connectIndexer()`, then listens for `message` events where `event.source === window` and `event.data === 'indexer:port'` and uses `event.ports[0]`. Check `event.origin` before trusting it.

## Long-Running Streams (e.g. Local AI Models)

Inference, transcription and similar token streams run in a `utilityProcess`, never in main (blocks the UI) or the renderer (no native modules, sandboxed). Main forks the worker, brokers one MessagePort per renderer session as above, and stays out of the data path.

```typescript
// src/workers/model-worker.ts
import { z } from 'zod';

const Msg = z.discriminatedUnion('type', [
  z.object({ type: z.literal('generate'), id: z.string().uuid(), prompt: z.string().max(32_000) }),
  z.object({ type: z.literal('cancel'), id: z.string().uuid() }),
  z.object({ type: z.literal('credit'), id: z.string().uuid(), n: z.number().int().min(1).max(256) }),
]);

type Run = { abort: AbortController; credit: number; wake?: () => void };
const runs = new Map<string, Run>();

process.parentPort.on('message', ({ data, ports }) => {
  if (data?.type !== 'port' || !ports[0]) return;
  const port = ports[0];
  port.on('message', ({ data: raw }) => {
    const msg = Msg.safeParse(raw);               // the renderer end is untrusted
    if (!msg.success) return;
    const m = msg.data;
    if (m.type === 'generate') void generate(port, m.id, m.prompt);
    const run = runs.get(m.id);
    if (m.type === 'cancel') run?.abort.abort();
    if (m.type === 'credit' && run) { run.credit += m.n; run.wake?.(); }
  });
  port.start();
});

async function generate(port: Electron.MessagePortMain, id: string, prompt: string): Promise<void> {
  const run: Run = { abort: new AbortController(), credit: 64 };
  runs.set(id, run);
  try {
    for await (const token of model.stream(prompt, { signal: run.abort.signal })) {
      while (run.credit === 0 && !run.abort.signal.aborted) {
        await new Promise<void>((r) => { run.wake = r; }); // renderer is behind: pause
      }
      run.credit--;
      port.postMessage({ type: 'token', id, token });
    }
    port.postMessage({ type: 'done', id, reason: run.abort.signal.aborted ? 'cancelled' : 'complete' });
  } catch (err) {
    port.postMessage({ type: 'error', id, message: String(err) }); // no stack traces to the UI
  } finally {
    runs.delete(id);
  }
}
```

- **Cancellation**: every request carries an id; `cancel` aborts the run's `AbortController`, which the inference loop checks between tokens. Also cancel all runs when the port closes (window closed or reloaded).
- **Backpressure**: MessagePorts have none built in. Use credits: the renderer grants N tokens and sends a new `credit` after rendering a batch. Batch DOM updates per animation frame instead of re-rendering per token.
- **Memory limits**: model weights live outside the V8 heap, so `--max-old-space-size` does not cap them. Load one model at a time, prefer memory-mapped weights, check free memory (`os.freemem()`) before loading, and watch the worker in `app.getAppMetrics()`. If it dies (`child-process-gone`, reason `oom`), tell the user and restart with a smaller model or context, with backoff.
- **Lifecycle**: start the worker lazily on first use, stop it after an idle timeout to return memory, and shut it down on quit (app-lifecycle.md "Graceful Shutdown").
- Model files are large downloads: store them under `userData` (persistence.md), verify a checksum before loading, and never load models from paths the renderer supplies.

## Crash and Hang Handling

The old `crashed` events were removed in v29. Use:

```typescript
import { app } from 'electron';

app.on('render-process-gone', (_e, webContents, details) => {
  log.error('renderer gone', details.reason, details.exitCode);
  if (details.reason !== 'clean-exit' && !webContents.isDestroyed()) {
    webContents.reload(); // or show a "something went wrong" page
  }
});

app.on('child-process-gone', (_e, details) => {
  log.error('child gone', details.type, details.reason, details.name);
});

mainWindow.on('unresponsive', () => log.warn('renderer unresponsive'));
```

Pair with `crashReporter` or `@sentry/electron` (see debugging.md).

## Navigation History

Navigation methods moved off `webContents` in v32:

```typescript
const nav = win.webContents.navigationHistory;
if (nav.canGoBack()) nav.goBack();
if (nav.canGoForward()) nav.goForward();
nav.clear();
```

## Dropped Files: webUtils.getPathForFile

`File.path` was removed in v32. Resolve paths in the preload and pass only the string over IPC.

```typescript
// preload
import { contextBridge, webUtils } from 'electron';

contextBridge.exposeInMainWorld('files', {
  pathFor: (file: File): string => webUtils.getPathForFile(file),
});
```

Main must still validate the path it receives (see security.md).

## Memory Leak Prevention

Common leaks: IPC listeners registered per window and never removed, timers in main, references to closed windows, renderer subscriptions without unsubscribe.

```typescript
// src/main/resources.ts
import type { BrowserWindow } from 'electron';

export class ResourceScope {
  private disposers: Array<() => void> = [];

  add(dispose: () => void): void {
    this.disposers.push(dispose);
  }

  interval(fn: () => void, ms: number): void {
    const id = setInterval(fn, ms);
    this.add(() => clearInterval(id));
  }

  bindTo(win: BrowserWindow): void {
    win.once('closed', () => this.dispose());
  }

  dispose(): void {
    for (const d of this.disposers.splice(0).reverse()) d();
  }
}

// Usage: one scope per window
const scope = new ResourceScope();
scope.bindTo(win);
scope.interval(checkForUpdates, 60_000);

const onFocus = () => void syncNow(); // app-wide listener, removed with the window
app.on('browser-window-focus', onFocus);
scope.add(() => app.off('browser-window-focus', onFocus));
```

- Null out window references in `closed`; check `isDestroyed()` before using stored `webContents`.
- `WebContentsView` contents are not freed automatically; call `webContents.close()`.
- Prefer `ipcMain.handle` registered once at startup over per-window `ipcMain.on`.
- In the renderer, always call the unsubscribe returned by `window.api.on*` functions.
- Profile with DevTools heap snapshots in the renderer and `--inspect` for main.

# App Lifecycle

How the app starts, receives links and files, restores its windows, keeps several windows in sync and shuts down cleanly. Main owns all of it; renderers only get events through the IPC contract (typed-ipc.md).

Docs: https://www.electronjs.org/docs/latest/api/app

## Single Instance

Most desktop apps should run once per user. A second launch (double-clicked file, deep link on Windows/Linux, taskbar click) hands its argv to the running instance and exits.

```typescript
// src/main/main.ts (excerpt)
import { app } from 'electron';

const gotLock = app.requestSingleInstanceLock({ startedAt: Date.now() }); // optional additionalData

if (!gotLock) {
  app.quit(); // the first instance receives 'second-instance'; register nothing else here
} else {
  app.on('second-instance', (_event, argv, _workingDirectory, _additionalData) => {
    focusMainWindow();         // restore if minimized, then focus
    handleLaunchArgs(argv);    // file paths and deep links, see below
  });
  void app.whenReady().then(start); // registerIpc, migrations, createWindow
}
```

- Keep startup code inside the `else` branch (or a `start()` it calls). `app.quit()` is asynchronous; code after it still runs.
- `argv` from the second instance is untrusted input: anyone can launch the binary with arbitrary arguments. Parse it with the same validators as deep links.
- Chromium adds its own switches to `argv`; look for your values (`atlas://…`, absolute paths with your extension), never index by position.
- `additionalData` must be JSON-serializable; use it for small hints, not for payloads.

## Deep Links (Custom Protocol)

The deep-link scheme (`atlas://`) is distinct from the internal `app://` scheme that serves the renderer (security.md). native-integration.md shows the document registry and the `handleDeepLink` allowlist; this section covers how the link reaches main on each OS.

| OS | Registration | Delivery |
|-|-|-|
| macOS | `CFBundleURLTypes` in Info.plist via packaging config (`setAsDefaultProtocolClient` alone is not enough for a packaged app) | `open-url` event, also on cold start, can fire before `ready` |
| Windows | `app.setAsDefaultProtocolClient` at runtime, or the installer writes registry keys | cold start: `process.argv`; app running: `second-instance` argv |
| Linux | `.desktop` file with `MimeType=x-scheme-handler/atlas` (deb/rpm maker config) | same as Windows |

```typescript
// src/main/launch-args.ts
import { app } from 'electron';
import path from 'node:path';
import { handleDeepLink } from './deep-links';   // allowlist, see native-integration.md
import { openDocument } from './open-document';  // queues until the window has loaded

export function registerProtocol(): void {
  if (process.defaultApp) {
    // Dev: `electron .` — the OS must launch electron with the app path as first argument
    if (process.argv.length >= 2) {
      app.setAsDefaultProtocolClient('atlas', process.execPath, [path.resolve(process.argv[1])]);
    }
  } else {
    app.setAsDefaultProtocolClient('atlas');
  }
}

export function handleLaunchArgs(argv: string[]): void {
  for (const arg of argv) {
    if (arg.startsWith('atlas://')) handleDeepLink(arg);
    else if (path.isAbsolute(arg) && arg.toLowerCase().endsWith('.atlas')) openDocument(arg);
  }
}

// Register before 'ready': macOS delivers cold-start links and files this early
app.on('open-url', (event, url) => { event.preventDefault(); handleDeepLink(url); });
app.on('open-file', (event, filePath) => { event.preventDefault(); openDocument(filePath); });
```

Call `registerProtocol()` and `handleLaunchArgs(process.argv.slice(1))` in the first instance at startup.

**Dev-mode caveats.** Registering from a dev build overwrites the OS handler for everyone on that machine, and on macOS it points at the Electron binary in `node_modules`. Use a separate dev scheme (`atlas-dev://`) or skip registration in dev and test with the packaged app. On macOS, `open-url` only fires reliably for the packaged, registered bundle. Linux desktops need the `.desktop` file installed, so test there with a deb/rpm install.

**Validating deep-link input.** Treat a link like an IPC payload from an untrusted page:

- Parse with `new URL`; reject anything that throws or whose `protocol` is not `atlas:`.
- Switch on an allowlist of actions (`url.host`); unknown actions do nothing.
- Validate query parameters with zod (`z.string().uuid()` for ids, enums for modes); never accept paths, URLs to open or commands.
- Destructive or sensitive actions (delete, sign out, connect account) need an in-app confirmation; a link on a web page can trigger them without user intent.
- Queue links that arrive before the window loaded (the `pending` pattern from native-integration.md); deliver them via `emit`.

## Window State Persistence

Restore size, position and maximized state, but never place a window off-screen: monitors get unplugged, resolutions change, laptops undock.

```typescript
// src/main/window-state.ts
import { screen, type BrowserWindow, type Rectangle } from 'electron';
import { readJson, writeJsonAtomic } from './json-store'; // atomic writes, see persistence.md

type WindowState = { bounds: Partial<Rectangle>; isMaximized: boolean };
const FILE = 'window-state.json';
const DEFAULT: WindowState = { bounds: { width: 1200, height: 800 }, isMaximized: false };

function visible(b: Rectangle): boolean {
  // At least 100x50 px of the window must lie inside some display's work area
  return screen.getAllDisplays().some(({ workArea: a }) => {
    const w = Math.min(b.x + b.width, a.x + a.width) - Math.max(b.x, a.x);
    const h = Math.min(b.y + b.height, a.y + a.height) - Math.max(b.y, a.y);
    return w >= 100 && h >= 50;
  });
}

function clampToDisplay(b: Rectangle): Rectangle {
  const { workArea: a } = screen.getDisplayMatching(b);
  const width = Math.min(b.width, a.width);
  const height = Math.min(b.height, a.height);
  return {
    width, height,
    x: Math.min(Math.max(b.x, a.x), a.x + a.width - width),
    y: Math.min(Math.max(b.y, a.y), a.y + a.height - height),
  };
}

export function loadWindowState(): WindowState {
  const saved = readJson<WindowState>(FILE);
  const b = saved?.bounds;
  if (!saved || b?.x === undefined || b.y === undefined || !b.width || !b.height) return DEFAULT;
  const rect = b as Rectangle;
  if (!visible(rect)) return { ...saved, bounds: { width: rect.width, height: rect.height } }; // OS centers it
  return { ...saved, bounds: clampToDisplay(rect) };
}

export function trackWindowState(win: BrowserWindow): void {
  let timer: NodeJS.Timeout | undefined;
  const save = () => {
    if (win.isDestroyed() || win.isMinimized()) return;
    // getNormalBounds: the restored size even while maximized or fullscreen
    void writeJsonAtomic(FILE, { bounds: win.getNormalBounds(), isMaximized: win.isMaximized() });
  };
  const debounced = () => { clearTimeout(timer); timer = setTimeout(save, 500); };
  win.on('resize', debounced);
  win.on('move', debounced);
  win.on('close', () => { clearTimeout(timer); save(); });
}
```

- `screen` is only usable after `ready`; `loadWindowState()` runs inside `createWindow()`.
- Restore maximized state after construction (`win.maximize()`), as in process-architecture.md; pass the normal bounds to the constructor so un-maximizing lands somewhere sensible.
- Don't restore fullscreen on macOS by default; a window reopening into its own Space surprises users.
- For multiple windows, key the stored state by window role (`main`, `preferences`), not by window id.
- Listen to `screen` `display-removed` / `display-metrics-changed` if windows must follow a disconnected monitor while running.

## Platform Lifecycle Differences

| Situation | macOS | Windows / Linux |
|-|-|-|
| Last window closed | App stays alive (menu bar, Dock) | Quit |
| Dock / taskbar click with no windows | `activate` → create a window | n/a (app is not running) |
| System shutdown / logout | `before-quit` and `will-quit` fire | Windows: they do **not** fire; use the window's `session-end` event or persist continuously |

```typescript
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
```

Apps with a tray icon may also stay alive on Windows/Linux; make that explicit (a "keep running in tray" setting), not the accidental result of a hidden window.

## Graceful Shutdown

`before-quit` fires once per quit attempt before windows close; `will-quit` after all windows closed. Both run synchronously: to await cleanup, prevent the quit, clean up, then quit again.

```typescript
// src/main/shutdown.ts
import { app } from 'electron';

let cleanedUp = false;

app.on('before-quit', (event) => {
  if (cleanedUp) return;
  event.preventDefault();
  void cleanup().finally(() => {
    cleanedUp = true;
    app.quit();
  });
});

async function cleanup(): Promise<void> {
  const deadline = new Promise<void>((r) => setTimeout(r, 3_000)); // never hang the quit
  await Promise.race([
    Promise.allSettled([stopWorkers(), flushSettings(), closeDatabase()]),
    deadline,
  ]);
}

async function stopWorkers(): Promise<void> {
  // Ask each utilityProcess to finish (it closes its DB, flushes queues), then kill if it lingers
  await Promise.all(workers.map((w) => new Promise<void>((resolve) => {
    const kill = setTimeout(() => { w.kill(); resolve(); }, 2_000);
    w.once('exit', () => { clearTimeout(kill); resolve(); });
    w.postMessage({ type: 'shutdown' });
  })));
}
```

- Keep cleanup short: the OS kills apps that ignore shutdown. Write state as it changes; quit-time cleanup is a last flush, not the only save.
- `app.exit()` skips `before-quit`/`will-quit`; reserve it for fatal errors.
- `autoUpdater.quitAndInstall()` closes windows first and then emits `before-quit`, so the handler above still runs; test that the update still installs after the deferred quit (auto-update.md).
- In the worker, handle `{ type: 'shutdown' }` by closing resources and calling `process.exit(0)`.

## Multi-Window State Sync

Main is the single source of truth. Renderers request changes via `invoke`; main validates, applies, persists and broadcasts the new state to every window, including the one that asked. Renderers never talk to each other directly and never keep authoritative copies.

The channels `settings:get-all`, `settings:set` and `settings:changed` are part of the shared contract in typed-ipc.md.

```typescript
// src/main/settings.ts (the 'settings:set' handler calls this with the parsed, per-key typed change)
import { nativeTheme } from 'electron';
import type { SettingChange } from '../shared/ipc-contract';

export function applySetting(change: SettingChange): { ok: true } {
  settings.set(change.key, change.value);                            // persisted by the settings store
  if (change.key === 'theme') nativeTheme.themeSource = change.value; // native-integration.md
  if (change.key === 'language') applyLocale(change.value);           // menus + i18n:changed, accessibility-i18n.md
  broadcast('settings:changed', change);
  return { ok: true };
}

// src/main/broadcast.ts
import { BrowserWindow } from 'electron';
export function broadcast<C extends EventChannel>(channel: C, payload: EventPayload<C>): void {
  for (const win of BrowserWindow.getAllWindows()) emit(win.webContents, channel, payload);
}
```

- New windows call `settings:get-all` once on load, then follow `settings:changed`. That ordering avoids a race where an event arrives before the initial fetch: apply events with a version counter, or subscribe before fetching.
- For `BaseWindow` + `WebContentsView` layouts, broadcast to each view's `webContents`, not the window.
- High-frequency shared state (cursor positions, live collaboration) goes over a `MessagePort` per window brokered by main (process-architecture.md), with main still holding the merged state.

## Power and Network Events

```typescript
import { powerMonitor, net } from 'electron';

powerMonitor.on('suspend', () => syncEngine.pause());
powerMonitor.on('resume', () => syncEngine.resumeAfterSleep()); // timers drifted, sockets are dead
powerMonitor.on('lock-screen', () => lockSensitiveViews());      // e.g. hide decrypted content
powerMonitor.on('shutdown', (e) => { e.preventDefault(); void flushThenQuit(); }); // Linux/macOS
```

- After `resume`, re-establish connections and re-check tokens; don't trust a `setInterval` to have fired during sleep.
- Online state: `net.isOnline()` in main, `navigator.onLine` plus `online`/`offline` events in the renderer. Both only mean "has a network interface"; confirm reachability with a real request (with timeout) before deciding a server is up.
- Let main own connectivity for sync and push the result through the contract (e.g. a `network:status` event) so all windows agree.

## Checklist

- [ ] Single-instance lock; second-instance argv parsed, not indexed
- [ ] Deep links and file opens registered before `ready`, queued until the window loaded, validated with an action allowlist
- [ ] Separate dev scheme or no protocol registration in dev
- [ ] Window bounds restored only onto a visible display
- [ ] macOS `activate` / `window-all-closed` behaviour; Windows shutdown does not rely on `before-quit`
- [ ] Quit waits (with a deadline) for utility processes and the database to close
- [ ] Shared state lives in main and is broadcast; no renderer-to-renderer state

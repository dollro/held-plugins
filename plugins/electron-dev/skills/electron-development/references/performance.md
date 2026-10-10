# Performance Optimization

Source of truth: the official checklist at https://www.electronjs.org/docs/latest/tutorial/performance. Measure first, then fix the biggest item.

## Official Checklist

| # | Item | In practice |
|-|-|-|
| 1 | Carefully include modules | Check size and load cost of each dependency before adding it; prefer small, focused packages |
| 2 | Don't load and run code too soon | Lazy-import in main; defer work until it's needed |
| 3 | Don't block the main process | No sync I/O, no CPU-heavy loops, no `sendSync`; move work to `utilityProcess` |
| 4 | Don't block the renderer | Web Workers, `requestIdleCallback`, chunked work |
| 5 | Avoid unnecessary polyfills | Chromium and Node are current; target `esnext`/`chrome<N>` |
| 6 | Avoid unnecessary or blocking network requests | Bundle fonts, icons, CSS locally instead of fetching from a CDN |
| 7 | Bundle your code | One bundle per entry avoids the cost of `require()` resolving many files |
| 8 | Call `Menu.setApplicationMenu(null)` when you don't need the default menu | Do it before `ready` |

## Bundle Main and Preload

Forge's Vite plugin (default stack) bundles main, preload and renderer separately. Keep that: an unbundled `node_modules` tree costs thousands of file reads at startup.

```ts
// vite.main.config.mts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    target: 'node22',          // match the Node major bundled with your Electron (process.versions.node)
    sourcemap: true,
    rollupOptions: {
      external: ['better-sqlite3'], // native modules stay external
    },
  },
});
```

- Sandboxed preloads can't use ESM: emit CJS for preload.
- Set build targets to what your Electron actually bundles: `node<major>` for main/preload and `chrome<major>` for the renderer. Read them from `process.versions.node` / `process.versions.chrome` (or the release notes) and bump them with each Electron upgrade; this drops polyfills and down-leveling.

## Lazy Imports in Main

```ts
// src/main/main.ts
import { app, BrowserWindow, Menu } from 'electron';

Menu.setApplicationMenu(null); // if you build your own menu later or need none

let pdf: typeof import('./pdf-export') | undefined;
async function exportPdf(docId: string) {
  pdf ??= await import('./pdf-export'); // loaded on first use, not at startup
  return pdf.render(docId);
}
```

Rule: top-level `import` in main should only pull in what's needed to show the first window.

## Defer Window Creation Work

```ts
async function createMainWindow(): Promise<BrowserWindow> {
  const win = new BrowserWindow({
    show: false,                 // avoid a white flash
    backgroundColor: '#1e1e1e',  // match the app theme
    webPreferences: { preload: PRELOAD_PATH, sandbox: true, contextIsolation: true },
  });

  win.once('ready-to-show', () => win.show());
  await win.loadURL(APP_URL);
  return win;
}

app.whenReady().then(async () => {
  await createMainWindow();

  // Non-critical work after first paint
  setImmediate(() => {
    void import('./updater').then((m) => m.checkForUpdates());
    void import('./telemetry').then((m) => m.init());
  });
});
```

- Show the window on `ready-to-show`; set `backgroundColor` so any early paint matches.
- Don't open databases, scan folders or check updates before the first window loads unless the UI needs them.
- Render a skeleton UI fast; load data over IPC after mount.

## Never Block: IPC and Heavy Work

- Use `ipcRenderer.invoke` / `ipcMain.handle`. Never `sendSync`: it freezes the renderer until main replies, and main may be busy.
- Keep handlers short. Anything CPU-heavy (parsing, indexing, image processing, crypto, sync DB queries) goes into a `utilityProcess`:

```ts
// src/main/indexer.ts
import { utilityProcess, MessageChannelMain } from 'electron';
import path from 'node:path';

export function startIndexer() {
  const child = utilityProcess.fork(path.join(__dirname, 'indexer-worker.cjs'), [], {
    serviceName: 'atlas-indexer',
  });
  const { port1, port2 } = new MessageChannelMain();
  child.postMessage({ type: 'init' }, [port2]);
  return { child, port: port1 };
}
```

```ts
// src/main/indexer-worker.ts (bundled as its own entry)
process.parentPort.once('message', ({ ports }) => {
  const [port] = ports;
  port.on('message', ({ data }) => port.postMessage(buildIndex(data)));
  port.start();
});
```

- Hand the `MessagePort` to the renderer when it needs a direct stream, so large payloads don't pass through main.
- In the renderer, use Web Workers for CPU work and keep frames under ~16 ms.

## V8 Snapshots and Code Caching

- Electron already uses an embedded Node startup snapshot in main.
- The `LoadBrowserProcessSpecificV8Snapshot` fuse lets the browser process load a custom snapshot (`browser_v8_context_snapshot.bin`). Building custom snapshots is advanced (tools like electron-link); measure before investing.
- Electron is adding build-time V8 code caching for sandboxed renderers; check the release notes for its status before relying on it (see `sources.md` → Version notes).
- Large real-world wins come from bundling and moving to ESM (VS Code's ESM migration cut startup notably).

### electron-vite bytecode option

If you use electron-vite (https://electron-vite.org) instead of Forge's Vite plugin, `build.bytecode` compiles main and preload to V8 bytecode (`.jsc`). Trade-offs:

- Main and preload only, not renderer.
- Preload bytecode requires `sandbox: false`: a real security cost. Don't disable the sandbox just for this.
- Builds are per-architecture.
- It's mostly source obfuscation; startup gain is modest. Measure.

## Measuring

**CPU profile of main at startup:**

```bash
# Forge dev build
npx electron --cpu-prof --cpu-prof-dir=./profiles .vite/build/main.cjs
```

Open the `.cpuprofile` in Chrome DevTools > Performance (or VS Code). Look for large `require`/`import` chunks and sync work before `ready`.

**Renderer:** DevTools Performance panel, Lighthouse for initial load, Memory panel for heap snapshots.

**Chrome tracing (whole app, all processes):**

```bash
npx electron --trace-startup='*' --trace-startup-file=./startup-trace.json .vite/build/main.cjs
```

```ts
import { contentTracing } from 'electron';

await contentTracing.startRecording({ included_categories: ['*'] });
// ... reproduce the slow path ...
const tracePath = await contentTracing.stopRecording();
console.log('Trace written to', tracePath); // open in https://ui.perfetto.dev or chrome://tracing
```

`startRecording` takes a `TraceConfig` (`included_categories`, `excluded_categories`, `recording_mode`, `trace_buffer_size_in_kb`) or `TraceCategoriesAndOptions`; snake_case is correct. `--trace-startup` / `--trace-startup-file` are Chromium switches (exercised in Electron's own test suite, not listed on its command-line-switches page). Docs: https://www.electronjs.org/docs/latest/api/content-tracing.

**Startup timestamps:** log `performance.now()` at main entry, `ready`, `ready-to-show` and first meaningful render; track them in CI on a fixed machine.

## Memory

- Measure per process: `app.getAppMetrics()` returns CPU and memory for every Electron process.
- Each `BrowserWindow`/`WebContentsView` is a renderer process (often 50 to 150 MB). Reuse windows, hide instead of recreate when quick re-open matters, and destroy views you no longer need.
- Remove IPC and `webContents` listeners when windows close; unsubscribe functions returned from preload `on*` helpers in component unmount.
- Don't keep large buffers in main; stream files and pass `MessagePort`s or file paths instead of whole payloads.
- Cap caches (LRU) and clear `session` caches if they grow: `session.defaultSession.clearCache()`.
- Find leaks with DevTools heap snapshots (compare before/after repeating an action). Don't call `global.gc()` on a timer; it masks leaks and costs CPU.

```ts
import { app } from 'electron';

setInterval(() => {
  for (const m of app.getAppMetrics()) {
    console.log(m.type, m.pid, `${Math.round(m.memory.workingSetSize / 1024)} MB`);
  }
}, 60_000).unref();
```

(`workingSetSize` is in KB.)

## GPU Acceleration

```ts
import { app, dialog } from 'electron';

// Must run before 'ready'
if (settings.get('disableHardwareAcceleration')) {
  app.disableHardwareAcceleration();
}

app.whenReady().then(async () => {
  console.log('GPU feature status', app.getGPUFeatureStatus());
  console.log('GPU info', await app.getGPUInfo('basic'));
});

// 'gpu-process-crashed' was removed; use child-process-gone
app.on('child-process-gone', async (_event, details) => {
  if (details.type !== 'GPU' || details.reason === 'clean-exit') return;
  const { response } = await dialog.showMessageBox({
    type: 'error',
    message: 'The graphics process crashed. Disable hardware acceleration and restart?',
    buttons: ['Disable & Restart', 'Ignore'],
  });
  if (response === 0) {
    settings.set('disableHardwareAcceleration', true);
    app.relaunch();
    app.exit(0);
  }
});
```

- Chromium enables GPU rasterization by default on supported hardware. Only add switches like `enable-gpu-rasterization` after measuring a gain, and offer a user setting to turn acceleration off.
- `settings` above is your own persisted store.

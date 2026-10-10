# Debugging and Diagnostics

## Main Process

Docs: https://www.electronjs.org/docs/latest/tutorial/debugging-main-process

**Plain Electron flags:**

```bash
npx electron --inspect=9229 .vite/build/main.cjs      # attach anytime
npx electron --inspect-brk=9229 .vite/build/main.cjs  # pause on first line
```

Then open `chrome://inspect` in Chrome, "Configure..." the port if needed, and click **inspect** on the Electron target.

**With Forge** (https://www.electronforge.io/advanced/debugging):

```bash
npm run start -- --inspect-electron       # passes a bare --inspect → port 9229
npm run start -- --inspect-brk-electron   # same, paused on first line
```

Forge forwards a bare `--inspect` / `--inspect-brk`, so the debugger listens on Node's default port 9229. The Forge debugging page has long said 5858; trust what the terminal prints (`Debugger listening on ws://...`). To pin a port, run Electron directly with `--inspect=<port>` as above.

**VS Code** (`.vscode/launch.json`), using Forge's launcher script:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Electron Main",
      "runtimeExecutable": "${workspaceFolder}/node_modules/@electron-forge/cli/script/vscode.sh",
      "windows": {
        "runtimeExecutable": "${workspaceFolder}/node_modules/@electron-forge/cli/script/vscode.cmd"
      },
      "runtimeArgs": [],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
```

Enable `build.sourcemap` in the Vite main/preload configs so breakpoints map to TypeScript.

Release builds should have the `EnableNodeCliInspectArguments` fuse disabled, so `--inspect` won't work there. Debug production issues with logs and crash reports instead.

## Renderer and Preload

```ts
import { app, BrowserWindow } from 'electron';

if (!app.isPackaged) {
  win.webContents.openDevTools({ mode: 'detach' });
}
```

- Preload scripts show up in DevTools under Sources (the preload context). Set breakpoints there.
- `Ctrl+Shift+I` / `Alt+Cmd+I` toggles DevTools if the default menu is kept; with a custom menu add a `{ role: 'toggleDevTools' }` item in dev builds only.
- Framework DevTools extensions: load an unpacked extension with `session.defaultSession.extensions.loadExtension(path)` in dev only (older code uses `session.loadExtension`, deprecated in favour of `ses.extensions.*`). Electron supports only part of the Chrome extensions API.
- Forward renderer console to the terminal during dev:

```ts
win.webContents.on('console-message', ({ level, message, sourceId, lineNumber }) => {
  console.log(`[renderer:${level}] ${message} (${sourceId}:${lineNumber})`);
});
```

(The event is a single details object: `level` is a string `'info' | 'warning' | 'error' | 'debug'`. The old positional `level, message, line, sourceId` arguments are deprecated.)

## Process Crash Handlers

The old `crashed` / `gpu-process-crashed` events no longer exist (removed in v29). Use:

```ts
import { app, BrowserWindow } from 'electron';
import log from 'electron-log/main';

app.on('render-process-gone', (_event, webContents, details) => {
  log.error('Renderer gone', { url: webContents.getURL(), ...details });
  if (details.reason !== 'clean-exit') {
    const win = BrowserWindow.fromWebContents(webContents);
    win?.reload(); // or show a "something went wrong" page
  }
});

app.on('child-process-gone', (_event, details) => {
  // details.type: 'GPU' | 'Utility' | 'Pepper Plugin' | ...
  log.error('Child process gone', details);
});

// Unresponsive renderer (long task, infinite loop)
win.on('unresponsive', () => log.warn('Window unresponsive'));
win.on('responsive', () => log.info('Window responsive again'));

// Main process
process.on('uncaughtException', (err) => log.error('uncaughtException', err));
process.on('unhandledRejection', (reason) => log.error('unhandledRejection', reason));
```

For `utilityProcess` children also listen to `child.on('exit', code => ...)` and restart with backoff.

## Native Crash Reporting: crashReporter

Built-in Crashpad collects minidumps for all processes. Start it as early as possible in main:

```ts
import { crashReporter } from 'electron';

crashReporter.start({
  submitURL: 'https://crash.acme.example/submit',
  uploadToServer: true,
  globalExtra: { channel: 'stable' },
});
```

- Without a server, set `uploadToServer: false`; dumps stay in `app.getPath('crashDumps')`.
- Symbolication needs the matching Electron symbols (published per release) and your own native module symbols.
- If you use Sentry (below), don't also call `crashReporter.start` yourself; the SDK configures it.

## Error Monitoring: @sentry/electron

The SDK sets a minimum supported Electron version per major; check it against your Electron before upgrading either (last snapshot in `sources.md` → Version notes). Initialize separately in each process type; renderer events are routed through main. Docs: https://docs.sentry.io/platforms/javascript/guides/electron/

```ts
// src/main/main.ts (first import)
import * as Sentry from '@sentry/electron/main';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  release: `atlas@${app.getVersion()}`,
  environment: app.isPackaged ? 'production' : 'development',
});
```

```ts
// src/renderer/main.ts
import * as Sentry from '@sentry/electron/renderer';

Sentry.init({}); // DSN and release come from main
```

```ts
// src/workers/indexer-worker.ts (utilityProcess)
import * as Sentry from '@sentry/electron/utility';

Sentry.init({});
```

- Upload source maps in CI (Sentry Vite plugin or CLI) so stack traces map to TypeScript.
- Scrub PII (`beforeSend`) and give users an opt-out for telemetry.

## File Logs: electron-log

```ts
// src/main/log.ts
import log from 'electron-log/main';

log.initialize();               // enables renderer -> main log forwarding
log.transports.file.level = 'info';
log.transports.file.maxSize = 5 * 1024 * 1024; // rotate at 5 MB
log.errorHandler.startCatching(); // log uncaught errors

export default log;
```

```ts
// src/renderer/log.ts
import log from 'electron-log/renderer';
log.info('Renderer started');
```

- With sandbox and contextIsolation on, `log.initialize()` in main injects electron-log's preload into the default session and sessions created afterwards; renderer logs go to main over IPC. For a session created earlier, pass it: `log.initialize({ getSessions: () => [customSession] })`. Alternative: `import 'electron-log/preload'` in your own preload.
- Log structured context (window id, doc id), never secrets or document contents.

## Where Logs Live

`app.getPath('logs')` is the canonical directory. electron-log writes `main.log` there by default.

| OS | Default location |
|-|-|
| macOS | `~/Library/Logs/<app name>/` |
| Windows | `%USERPROFILE%\AppData\Roaming\<app name>\logs\` (= `%APPDATA%`) |
| Linux | `~/.config/<app name>/logs/` |

Add a "Show Logs" menu item or support command so users can send them:

```ts
import { app, shell } from 'electron';

shell.openPath(app.getPath('logs'));
```

## Other Tools

- `app.getAppMetrics()`: CPU and memory per process; `chrome://process-internals` and `chrome://gpu` can be opened in a dev `BrowserWindow`.
- `ELECTRON_ENABLE_LOGGING=1` prints Chromium internal logs to stderr.
- `ELECTRON_ENABLE_STACK_DUMPING=1` prints a stack trace on native crashes (dev).
- `contentTracing` and `--cpu-prof` for performance issues: see `performance.md`.

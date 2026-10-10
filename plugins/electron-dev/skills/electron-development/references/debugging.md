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

- Without a server or without consent, set `uploadToServer: false`; dumps stay in `app.getPath('crashDumps')`. See "Privacy and Telemetry Consent".
- Symbolication needs the matching Electron symbols (published per release) and your own native module symbols.
- If you use Sentry (below), don't also call `crashReporter.start` yourself; the SDK configures it.

## Error Monitoring: @sentry/electron

The SDK sets a minimum supported Electron version per major; check it against your Electron before upgrading either (last snapshot in `sources.md` → Version notes). Initialize separately in each process type. Renderer events reach Sentry through main's transport by default; whether main's `beforeSend` sees them is an open question (sources.md), so scrub in every process. Docs: https://docs.sentry.io/platforms/javascript/guides/electron/

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
- Gate sending on consent and scrub PII in `beforeSend`: see "Privacy and Telemetry Consent" below.

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

## Privacy and Telemetry Consent

Crash reports, error events and logs carry file paths, user names and fragments of what the user was doing. Treat them as personal data.

**Consent policy.** Decide per jurisdiction with whoever owns privacy: opt-in (nothing sent until the user agrees) is the safe default and required in many places (e.g. under GDPR for analytics); opt-out only where policy explicitly allows it. Keep crash reporting and usage analytics as separate choices, ask on first run, make both changeable in settings, and honour an admin policy (MDM profile, registry key) that forces them off.

Consent lives in main's settings and changes through the contract channel `telemetry:set-consent` (`window.api.setTelemetryConsent({ crashReports, usage })`, typed-ipc.md). Main applies it immediately:

```ts
// src/main/telemetry.ts (imported first in main.ts; replaces the plain Sentry.init above)
import * as Sentry from '@sentry/electron/main';
import { app } from 'electron';
import { settings } from './settings';

let consent = settings.get('telemetry') ?? { crashReports: false, usage: false }; // opt-in default

const USER_DIR = /(\/Users\/|\/home\/|[A-Za-z]:\\Users\\)[^/\\]+/gi; // /Users/<name>, /home/<name>, C:\Users\<name>
export const scrub = (v: unknown): unknown =>
  typeof v === 'string' ? v.replace(USER_DIR, '$1<user>')
  : Array.isArray(v) ? v.map(scrub)
  : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, scrub(x)]))
  : v;

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  release: `atlas@${app.getVersion()}`,
  sendDefaultPii: false,
  beforeSend: (event) => (consent.crashReports ? (scrub(event) as typeof event) : null), // gate + scrub
  beforeBreadcrumb: (crumb) => (crumb.category === 'console' ? null : (scrub(crumb) as typeof crumb)),
});

export function setTelemetryConsent(next: typeof consent): void {
  consent = next;
  settings.set('telemetry', next);
  // Without Sentry: crashReporter.start({ submitURL, uploadToServer: consent.crashReports }) at startup, then:
  // crashReporter.setUploadToServer(next.crashReports);
  if (next.usage) void import('./analytics').then((m) => m.startAnalytics()); // analytics code loads only after consent
  else stopAnalyticsIfLoaded();
}
```

- Give the renderer and utility `Sentry.init` calls a `beforeSend` that applies the same scrub, unless you have verified that their events pass through main's. Initialising the SDK early with a gate keeps early crashes capturable once consent exists; the alternative is to call `Sentry.init` only after consent. Either way nothing leaves the machine before the user agrees. Check that the SDK's native-crash (minidump) path honours the same gate; if not, disable that integration until consent.
- Minidumps contain process memory, so they can contain document contents. Upload them only with crash-report consent, and delete `app.getPath('crashDumps')` when the user revokes it.
- **Never log or report:** secrets and tokens, document contents, clipboard data, full IPC payloads (log channel name, outcome and duration only), full URLs with query strings. Log document ids, not paths.
- Redact in the logger too, so a forgotten call site cannot leak:

```ts
// src/main/log.ts (addition)
import { scrub } from './telemetry';
log.hooks.push((message) => ({ ...message, data: message.data.map(scrub) }));
```

- **Retention:** rotate by size (`maxSize`) and delete log files older than a fixed window (e.g. 14 days) at startup. State the window in the privacy notice.
- **User control:** a "Save Diagnostics…" command lets the user review and export logs (`dialog.showSaveDialog`, then zip the logs folder) and send them themselves; "Delete Diagnostics" clears the logs and crash dump folders. For data already sent, document how users request deletion from the error-monitoring vendor.

## Other Tools

- `app.getAppMetrics()`: CPU and memory per process; `chrome://process-internals` and `chrome://gpu` can be opened in a dev `BrowserWindow`.
- `ELECTRON_ENABLE_LOGGING=1` prints Chromium internal logs to stderr.
- `ELECTRON_ENABLE_STACK_DUMPING=1` prints a stack trace on native crashes (dev).
- `contentTracing` and `--cpu-prof` for performance issues: see `performance.md`.

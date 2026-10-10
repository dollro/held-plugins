# Security Implementation

Source of truth: the official checklist at https://www.electronjs.org/docs/latest/tutorial/security. Treat every item as a default; deviations need a written reason.

## Official Checklist (20 items)

| # | Rule | How |
|-|-|-|
| 1 | Only load secure content | `https:` / `wss:` for anything remote |
| 2 | No Node integration for remote content | `nodeIntegration: false` (default) |
| 3 | Context isolation | `contextIsolation: true` (default) |
| 4 | Process sandboxing | `sandbox: true` (default) |
| 5 | Handle permission requests | `session.setPermissionRequestHandler` |
| 6 | Don't disable `webSecurity` | leave default `true` |
| 7 | Define a CSP | response header (meta tag only as a fallback) |
| 8 | No `allowRunningInsecureContent` | leave default `false` |
| 9 | No experimental features | no `experimentalFeatures: true` |
| 10 | No `enableBlinkFeatures` | leave unset |
| 11 | `<webview>`: no `allowpopups` | prefer `WebContentsView` anyway |
| 12 | Verify `<webview>` options | `will-attach-webview` handler |
| 13 | Limit navigation | `will-navigate` + allowlist |
| 14 | Limit new windows | `setWindowOpenHandler` |
| 15 | No `shell.openExternal` with untrusted input | scheme + host allowlist |
| 16 | Use a current Electron | one of the latest 3 majors (8-week cadence) |
| 17 | Validate the sender of every IPC message | `event.senderFrame` origin allowlist |
| 18 | Avoid `file://` | custom protocol via `protocol.handle` |
| 19 | Check which fuses you can change | Forge `FusesPlugin` |
| 20 | Don't expose Electron APIs to untrusted content | narrow `contextBridge` functions only |

Note: `nodeIntegration: true` silently disables the sandbox for that renderer. `ipcRenderer` can no longer be passed over `contextBridge` (since v29) and must never be exposed wholesale.

## Secure BrowserWindow

```typescript
// src/main/window.ts
import { BrowserWindow } from 'electron';
import path from 'node:path';

export function createMainWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'), // bundled CJS
      contextIsolation: true,   // default, keep explicit
      sandbox: true,            // default, keep explicit
      nodeIntegration: false,   // default, keep explicit
      webSecurity: true,
      webviewTag: false,
      allowRunningInsecureContent: false,
    },
  });
  win.once('ready-to-show', () => win.show());
  return win;
}
```

The old `enableRemoteModule` option and the `remote` module no longer exist; do not reach for `@electron/remote` either.

## Content Security Policy

Deliver the CSP as a response header set by main, with one policy per mode. A header is enforced before any page script runs and supports every directive; a `<meta>` CSP ignores `frame-ancestors` (and `report-uri`, `sandbox`), so don't rely on a meta tag alone.

```typescript
// src/main/csp.ts
const RELEASE_CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "connect-src 'self' https://api.acme.example",
  "object-src 'none'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
].join('; ');

// Dev only: the Vite dev server serves the page and HMR talks over ws:
function devCsp(devUrl: string): string {
  const { host } = new URL(devUrl);
  return RELEASE_CSP
    .replace("script-src 'self'", "script-src 'self' 'unsafe-eval'")
    .replace("connect-src 'self'", `connect-src 'self' ws://${host}`);
}

export const CSP = MAIN_WINDOW_VITE_DEV_SERVER_URL
  ? devCsp(MAIN_WINDOW_VITE_DEV_SERVER_URL)
  : RELEASE_CSP;
```

Release: attach the header in the `protocol.handle('app', ...)` handler (see "Custom Protocol" below), so every app response carries it. Dev: the page comes from the Vite server, so inject it with `onHeadersReceived`, scoped to the dev origin:

```typescript
import { session } from 'electron';
import { CSP } from './csp';

if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
  const devOrigin = new URL(MAIN_WINDOW_VITE_DEV_SERVER_URL).origin; // http(s) origin: .origin is fine
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const isDevPage = new URL(details.url).origin === devOrigin;
    callback({
      responseHeaders: isDevPage
        ? { ...details.responseHeaders, 'Content-Security-Policy': [CSP] }
        : details.responseHeaders,
    });
  });
}
```

The dev policy (`'unsafe-eval'`, `ws:`) must never reach a packaged build; keying it on `MAIN_WINDOW_VITE_DEV_SERVER_URL` (undefined when packaged) guarantees that.

## App Origin Helpers

Node's WHATWG `URL` only computes a tuple origin for `http`, `https`, `ws`, `wss` and `ftp`, so `new URL('app://atlas/index.html').origin` is the string `'null'` and an origin comparison silently fails for every request. Compare parsed `protocol` + `host` for URLs, and use Chromium's origin (`event.senderFrame.origin`, the permission check's `requestingOrigin`), which serializes the privileged standard scheme as `app://atlas`.

```typescript
// src/main/security.ts
import type { IpcMainEvent, IpcMainInvokeEvent } from 'electron';

export const APP_ORIGIN = 'app://atlas'; // as Chromium serializes a standard custom scheme
// Forge's Vite plugin injects this global in dev; undefined in packaged builds. http(s), so .origin works.
const DEV_ORIGIN = MAIN_WINDOW_VITE_DEV_SERVER_URL
  ? new URL(MAIN_WINDOW_VITE_DEV_SERVER_URL).origin
  : null;

/** For URLs (navigation, permission requestingUrl): never compare new URL(x).origin for app: */
export function isAppUrl(raw: string): boolean {
  let url: URL;
  try { url = new URL(raw); } catch { return false; }
  if (url.protocol === 'app:' && url.host === 'atlas') return true;
  return DEV_ORIGIN !== null && url.origin === DEV_ORIGIN;
}

/** For origins Chromium already serialized (WebFrameMain.origin, requestingOrigin) */
export function isAppOrigin(origin: string): boolean {
  return origin === APP_ORIGIN || (DEV_ORIGIN !== null && origin === DEV_ORIGIN);
}
```

## Permissions

Deny by default; grant only what the app needs, only to your own origin.

```typescript
import { session } from 'electron';
import { isAppOrigin, isAppUrl } from './security';

const ALLOWED = new Set(['clipboard-sanitized-write', 'notifications']);

session.defaultSession.setPermissionRequestHandler((_wc, permission, callback, details) => {
  callback(isAppUrl(details.requestingUrl) && ALLOWED.has(permission));
});

session.defaultSession.setPermissionCheckHandler((_wc, permission, requestingOrigin) =>
  isAppOrigin(requestingOrigin) && ALLOWED.has(permission),
);
```

## Navigation and New Windows

```typescript
import { app, shell } from 'electron';
import { isAppUrl } from './security';

const EXTERNAL_ALLOW = new Set(['acme.example', 'docs.acme.example']);

// export from src/main/security.ts; menus and IPC handlers reuse it
export function openExternalSafe(raw: string): void {
  let url: URL;
  try { url = new URL(raw); } catch { return; }
  if (url.protocol === 'https:' && EXTERNAL_ALLOW.has(url.hostname)) {
    void shell.openExternal(url.toString());
  }
}

app.on('web-contents-created', (_event, contents) => {
  contents.on('will-navigate', (event, url) => {
    if (!isAppUrl(url)) event.preventDefault();
  });

  contents.setWindowOpenHandler(({ url }) => {
    openExternalSafe(url);       // hand off allowlisted links to the OS browser
    return { action: 'deny' };   // never let content spawn Electron windows
  });

  contents.on('will-attach-webview', (event) => event.preventDefault()); // no <webview>
});
```

Never pass renderer-supplied strings to `shell.openExternal` or `shell.openPath` without parsing and allowlisting; `file:`, `smb:` and custom schemes can execute code.

## IPC Sender Validation

Every `ipcMain.handle` / `ipcMain.on` must check where the message came from. See typed-ipc.md for wiring this into a typed contract with zod payload validation.

```typescript
// src/main/security.ts (continued)
export function assertTrustedSender(event: IpcMainInvokeEvent | IpcMainEvent): void {
  // senderFrame is null if the frame navigated away or was destroyed before the message arrived
  const origin = event.senderFrame?.origin;
  if (!origin || !isAppOrigin(origin)) {
    throw new Error('IPC from untrusted sender');
  }
}
```

Use `senderFrame.origin` (`WebFrameMain.origin`), not `new URL(senderFrame.url).origin`: the latter is `'null'` for `app://` (see "App Origin Helpers").

Validate payloads too: normalize paths and confirm they resolve inside an allowed root (`path.relative(root, p)` must not start with `..`), cap sizes, reject unexpected shapes.

## Custom Protocol Instead of file://

`file://` pages get extra privileges and share one origin. Serve the bundled renderer from a privileged custom scheme.

```typescript
import { app, net, protocol } from 'electron';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { CSP } from './csp';

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } },
]);

const RENDERER_ROOT = path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}`);

app.whenReady().then(() => {
  protocol.handle('app', async (request) => {
    const { host, pathname } = new URL(request.url);
    if (host !== 'atlas') return new Response('Not found', { status: 404 });
    const target = path.join(RENDERER_ROOT, decodeURIComponent(pathname));
    const rel = path.relative(RENDERER_ROOT, target);
    if (rel.startsWith('..') || path.isAbsolute(rel)) {
      return new Response('Forbidden', { status: 403 });
    }
    const file = await net.fetch(pathToFileURL(target).toString());
    const headers = new Headers(file.headers);
    headers.set('Content-Security-Policy', CSP); // release policy, see "Content Security Policy"
    return new Response(file.body, { status: file.status, headers });
  });
  // win.loadURL('app://atlas/index.html')
});
```

`registerSchemesAsPrivileged` must run before `ready`; keep it at module top level of main.

## Fuses (Forge FusesPlugin)

Fuses are flipped in the binary at package time. Forge's Vite + TypeScript template ships this plugin; recommended settings (the same block as in build-config.md):

```typescript
// forge.config.mts
import { FusesPlugin } from '@electron-forge/plugin-fuses';
import { FuseV1Options, FuseVersion } from '@electron/fuses';

// Set only for E2E builds (see testing.md); release builds never set it.
const isTestBuild = process.env.ATLAS_TEST_BUILD === '1';

export default {
  // ...
  plugins: [
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true, // irreversible once shipped
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: isTestBuild, // Playwright needs this
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
      [FuseV1Options.GrantFileProtocolExtraPrivileges]: false,
    }),
  ],
};
```

- Disabling `EnableNodeCliInspectArguments` breaks Playwright's `_electron.launch()`. Run E2E against a separate test build packaged with `ATLAS_TEST_BUILD=1` (as above) or the unpackaged app; release builds keep it off.
- electron-builder: set the same fuses via its `electronFuses` config (camelCase keys, e.g. `enableNodeCliInspectArguments`); it flips them before signing. See build-config.md.
- With `RunAsNode` off, `child_process.fork` / `ELECTRON_RUN_AS_NODE` stop working; use `utilityProcess.fork` (see process-architecture.md).
- `LoadBrowserProcessSpecificV8Snapshot` exists for custom main-process snapshots; leave off unless you build one.

Docs: https://www.electronjs.org/docs/latest/tutorial/fuses

## ASAR Integrity

With `EnableEmbeddedAsarIntegrityValidation` + `OnlyLoadAppFromAsar`, Electron verifies `app.asar` against a hash embedded in the binary at startup, so a tampered archive refuses to load.

- Supported on macOS and Windows; Linux is not documented.
- Forge / `@electron/packager` and electron-builder all embed the hash automatically when packaging an ASAR.
- Combine with code signing; integrity without a signature only raises the bar.

Docs: https://www.electronjs.org/docs/latest/tutorial/asar-integrity

## Secrets with safeStorage

`safeStorage` encrypts with the OS keychain (macOS Keychain, Windows DPAPI, Linux secret store). Store ciphertext in `userData`; never hard-code an encryption key in the app.

```typescript
// src/main/secrets.ts (main process only)
import { app, safeStorage } from 'electron';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const file = () => path.join(app.getPath('userData'), 'secrets.json');

async function load(): Promise<Record<string, string>> {
  try { return JSON.parse(await readFile(file(), 'utf8')); } catch { return {}; }
}

export async function setSecret(key: string, value: string): Promise<void> {
  if (!safeStorage.isEncryptionAvailable()) throw new Error('OS encryption unavailable');
  const all = await load();
  all[key] = safeStorage.encryptString(value).toString('base64');
  await writeFile(file(), JSON.stringify(all), { mode: 0o600 });
}

export async function getSecret(key: string): Promise<string | null> {
  const enc = (await load())[key];
  return enc ? safeStorage.decryptString(Buffer.from(enc, 'base64')) : null;
}
```

- Call only after `app.whenReady()`.
- Current Electron also offers async `safeStorage` methods that do not block the main thread; prefer them when available (check the [safeStorage API](https://www.electronjs.org/docs/latest/api/safe-storage) for names and platform notes).
- On Linux, `safeStorage.getSelectedStorageBackend()` returning `'basic_text'` means no real keyring; refuse to store or warn the user rather than silently falling back to plaintext.
- Never send decrypted secrets to the renderer; perform the authenticated call in main and return results.

## Certificate Verification

`session.setCertificateVerifyProc` lets you override TLS verification (e.g. pinning for a high-risk API or a private CA). It is easy to get wrong and breaks on certificate rotation; use it only for a concrete threat model, and always fall back to Chromium's result (`callback(-3)`) for hosts you do not pin.

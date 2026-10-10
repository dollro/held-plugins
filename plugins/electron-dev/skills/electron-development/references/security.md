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
| 7 | Define a CSP | meta tag or response header |
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

Prefer a meta tag in `index.html` (works for custom protocols and the Vite dev server), plus a header for remote content.

```html
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
           img-src 'self' data:; connect-src 'self' https://api.acme.example;
           object-src 'none'; base-uri 'self'; frame-ancestors 'none'">
```

```typescript
import { session } from 'electron';

session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': ["default-src 'self'; script-src 'self'; object-src 'none'"],
    },
  });
});
```

During development Vite's HMR needs `ws:` in `connect-src` and may need `'unsafe-eval'`; never ship those.

## Permissions

Deny by default; grant only what the app needs, only to your own origin.

```typescript
import { session } from 'electron';

const APP_ORIGIN = 'app://atlas';
const ALLOWED = new Set(['clipboard-sanitized-write', 'notifications']);

session.defaultSession.setPermissionRequestHandler((wc, permission, callback, details) => {
  const origin = new URL(details.requestingUrl).origin;
  callback(origin === APP_ORIGIN && ALLOWED.has(permission));
});

session.defaultSession.setPermissionCheckHandler((_wc, permission, requestingOrigin) =>
  requestingOrigin === APP_ORIGIN && ALLOWED.has(permission),
);
```

## Navigation and New Windows

```typescript
import { app, shell } from 'electron';

const EXTERNAL_ALLOW = new Set(['acme.example', 'docs.acme.example']);

function openExternalSafe(raw: string): void {
  const url = new URL(raw);
  if (url.protocol === 'https:' && EXTERNAL_ALLOW.has(url.hostname)) {
    void shell.openExternal(url.toString());
  }
}

app.on('web-contents-created', (_event, contents) => {
  contents.on('will-navigate', (event, url) => {
    if (new URL(url).origin !== APP_ORIGIN) event.preventDefault();
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
import type { IpcMainInvokeEvent } from 'electron';

const TRUSTED_ORIGINS = new Set([
  'app://atlas',
  // Forge Vite plugin injects this global in dev; undefined in packaged builds
  ...(MAIN_WINDOW_VITE_DEV_SERVER_URL ? [new URL(MAIN_WINDOW_VITE_DEV_SERVER_URL).origin] : []),
]);

export function assertTrustedSender(event: IpcMainInvokeEvent): void {
  const frame = event.senderFrame;
  if (!frame || !TRUSTED_ORIGINS.has(new URL(frame.url).origin)) {
    throw new Error('IPC from untrusted sender');
  }
}
```

Validate payloads too: normalize paths and confirm they resolve inside an allowed root (`path.relative(root, p)` must not start with `..`), cap sizes, reject unexpected shapes.

## Custom Protocol Instead of file://

`file://` pages get extra privileges and share one origin. Serve the bundled renderer from a privileged custom scheme.

```typescript
import { app, net, protocol } from 'electron';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } },
]);

const RENDERER_ROOT = path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}`);

app.whenReady().then(() => {
  protocol.handle('app', (request) => {
    const { pathname } = new URL(request.url);
    const target = path.join(RENDERER_ROOT, decodeURIComponent(pathname));
    const rel = path.relative(RENDERER_ROOT, target);
    if (rel.startsWith('..') || path.isAbsolute(rel)) {
      return new Response('Forbidden', { status: 403 });
    }
    return net.fetch(pathToFileURL(target).toString());
  });
  // win.loadURL('app://atlas/index.html')
});
```

`registerSchemesAsPrivileged` must run before `ready`. In ESM main, keep it at module top level.

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

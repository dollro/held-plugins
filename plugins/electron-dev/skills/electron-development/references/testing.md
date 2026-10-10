# Testing Electron Apps

Spectron is dead (deprecated 2022). Don't use it or copy examples that do. Current options are listed in the official guide: https://www.electronjs.org/docs/latest/tutorial/automated-testing

## Test Pyramid

| Layer | Tool | What it covers | Speed |
|-|-|-|-|
| Unit | Vitest (Node env) | Shared logic, main-process services, IPC handler functions, contract validation | ms |
| Component | Vitest + jsdom/happy-dom, or Vitest browser mode | Renderer UI with `window.api` (preload API) mocked | ms to s |
| E2E | Playwright `_electron` or `@wdio/electron-service` | Real app: main + preload + renderer, IPC, windows, menus | s per test |

Aim for most tests at the bottom. Keep E2E to critical journeys (launch, open file, save, update prompt). Structure code so the bottom layers need no Electron runtime:

```
src/
  shared/ipc-contract.ts     # channel names + types + zod schemas
  main/handlers/*.ts         # pure-ish handler functions, no ipcMain inside
  main/ipc.ts                # wires handlers to ipcMain.handle
  main/main.ts
  preload/preload.ts         # distinct entry names: Vite names bundles after the entry file
  renderer/
```

## Unit Tests: IPC Handlers

Write handlers as plain functions that take the `IpcMainInvokeEvent` and validated args. Register them in one place. Then test the function directly with a fake event; no Electron needed. The sender check is `assertTrustedSender` from security.md (it reads `event.senderFrame?.origin`); the schema comes from the shared contract.

```ts
// src/main/handlers/documents.ts
import type { IpcMainInvokeEvent } from 'electron';
import { invokeContract, type Res } from '../../shared/ipc-contract';
import { assertTrustedSender } from '../security';

type Repo = { get(id: string): Promise<Res<'document:read'>> }; // throws on unknown id

export function makeReadDocument(repo: Repo) {
  return async (event: IpcMainInvokeEvent, raw: unknown) => {
    assertTrustedSender(event);
    const { id } = invokeContract['document:read'].request.parse(raw);
    return repo.get(id);
  };
}
```

```ts
// src/main/handlers/documents.test.ts
import { describe, expect, it, vi } from 'vitest';
import type { IpcMainInvokeEvent } from 'electron';
import { makeReadDocument } from './documents';

// Chromium's serialized origin, as WebFrameMain.origin reports it
const fakeEvent = (origin: string | null) =>
  ({ senderFrame: origin === null ? null : { origin } }) as unknown as IpcMainInvokeEvent;

describe('readDocument', () => {
  const doc = { name: 'notes.md', content: '# hello', mtimeMs: 0 };
  const repo = { get: vi.fn().mockResolvedValue(doc) };
  const handler = makeReadDocument(repo);
  const id = '3f1c8a52-6a3e-4d2b-9a57-0c4b8e2f1d11';

  it('returns the document for a trusted sender', async () => {
    await expect(handler(fakeEvent('app://atlas'), { id })).resolves.toEqual(doc);
  });

  it.each(['https://evil.example', 'null', 'file://', null])('rejects sender %s', async (origin) => {
    await expect(handler(fakeEvent(origin), { id })).rejects.toThrow('untrusted');
  });

  it('rejects malformed args', async () => {
    await expect(handler(fakeEvent('app://atlas'), { id: 42 })).rejects.toThrow();
  });
});
```

`MAIN_WINDOW_VITE_DEV_SERVER_URL` is a Forge build-time global; define it for tests (`define` in the Vitest config, or `vi.stubGlobal`) so `security.ts` loads outside the Forge build.

Notes:
- Run main/shared tests with `environment: 'node'`. Don't import `electron` at runtime in handler modules (type imports only), or mock it with `vi.mock('electron', () => ({ app: { getPath: vi.fn(() => '/tmp/atlas') } }))`.
- Inject dependencies (repo, fs, clock) so handlers stay testable.
- Test the sender check and schema validation explicitly: these are security controls (checklist item 17).

```ts
// vitest.config.ts (workspace-style projects)
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    projects: [
      { test: { name: 'main', include: ['src/{main,shared}/**/*.test.ts'], environment: 'node' } },
      { test: { name: 'renderer', include: ['src/renderer/**/*.test.ts'], environment: 'happy-dom' } },
    ],
  },
});
```

## Renderer Component Tests

Framework-agnostic: use the testing library for your UI framework (Vue Test Utils, Testing Library for React/Svelte, etc.). The Electron-specific part is only the preload bridge. Stub it on `window` so components never touch real IPC:

```ts
// src/renderer/test/setup.ts
import { vi } from 'vitest';
import type { AtlasApi } from '../../shared/ipc-contract';

const unsubscribe = () => {};

const api: AtlasApi = {
  readDocument: vi.fn(async () => ({ name: 'notes.md', content: '# hello', mtimeMs: 0 })),
  startDocumentDrag: vi.fn(async () => {}),
  setSetting: vi.fn(async () => ({ ok: true as const })),
  getSettings: vi.fn(async () => ({ theme: 'system', language: 'en' }) as const),
  getLocale: vi.fn(async () => ({ locale: 'en', dir: 'ltr', formatLocale: 'en-US' }) as const),
  setTelemetryConsent: vi.fn(async () => {}),
  appVersion: vi.fn(async () => '0.0.0-test'),
  showContextMenu: vi.fn(async () => {}),
  connectIndexer: vi.fn(async () => {}),
  restartToUpdate: vi.fn(async () => {}),
  onUpdateReady: vi.fn(() => unsubscribe),
  onSyncProgress: vi.fn(() => unsubscribe),
  onMenuCommand: vi.fn(() => unsubscribe),
  onDocumentOpened: vi.fn(() => unsubscribe),
  onDocumentAction: vi.fn(() => unsubscribe),
  onSettingsChanged: vi.fn(() => unsubscribe),
  onThemeChanged: vi.fn(() => unsubscribe),
  onLocaleChanged: vi.fn(() => unsubscribe),
};
Object.defineProperty(window, 'api', { value: api, writable: true });
```

`AtlasApi` is exported from `src/shared/ipc-contract.ts` (typed-ipc.md) and the preload checks its bridge with `satisfies AtlasApi`, so a new channel fails to compile here until the stub covers it.

## E2E with Playwright

Playwright's Electron support has long been marked **experimental**; check its status and minimum Electron version in the docs before relying on it. Docs: https://playwright.dev/docs/api/class-electron

```ts
// e2e/app.spec.ts
import { test, expect, _electron as electron, type ElectronApplication } from '@playwright/test';

let app: ElectronApplication;

test.beforeAll(async () => {
  app = await electron.launch({
    // dev/unpackaged build: point at the bundled main entry
    args: ['.vite/build/main.cjs'],
    // packaged build instead (Forge names output after productName): executablePath: 'out/Atlas-linux-x64/Atlas'
    env: { ...process.env, NODE_ENV: 'test' },
  });
});

test.afterAll(async () => {
  await app.close();
});

test('opens a file via the native dialog', async () => {
  // Stub the dialog in the MAIN process; native dialogs can't be driven by Playwright
  await app.evaluate(async ({ dialog }, filePath) => {
    dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filePath] });
  }, '/tmp/fixtures/sample.md');

  const window = await app.firstWindow();
  await window.getByRole('button', { name: 'Open' }).click();
  await expect(window.getByRole('heading', { name: 'sample' })).toBeVisible();
});

test('reports the app version from main', async () => {
  const version = await app.evaluate(({ app }) => app.getVersion());
  expect(version).toMatch(/^\d+\.\d+\.\d+/);
});
```

- `firstWindow()` waits for the first `BrowserWindow`; use `app.waitForEvent('window')` for later ones.
- `app.evaluate(fn)` runs `fn` in the main process with the `electron` module as first argument. Use it to stub `dialog`, `shell.openExternal`, `autoUpdater` and to read state.
- Prefer testing the packaged build in CI before release (catches ASAR, path and native-module issues); use the dev build for fast local runs.

### Fuse gotcha

Playwright attaches to the main process via Node's inspector. If the `EnableNodeCliInspectArguments` fuse is disabled (recommended for release builds), `electron.launch` fails.

Fix: produce a dedicated test build with that fuse turned on via the `ATLAS_TEST_BUILD` switch, and keep it off in release builds. This is the same FusesPlugin block as in build-config.md and security.md:

```ts
// forge.config.mts (excerpt)
import { FusesPlugin } from '@electron-forge/plugin-fuses';
import { FuseV1Options, FuseVersion } from '@electron/fuses';

// Set only for E2E builds; release builds never set it.
const isTestBuild = process.env.ATLAS_TEST_BUILD === '1';

export default {
  plugins: [
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true, // irreversible once shipped
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: isTestBuild, // on only for E2E builds
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
      [FuseV1Options.GrantFileProtocolExtraPrivileges]: false,
    }),
  ],
};
```

With electron-builder, override `electronFuses.enableNodeCliInspectArguments` from a JS config reading the same variable (see build-config.md).

Never ship the E2E artifact. Name it distinctly and keep it out of the publish step.

## Alternative: WebdriverIO Electron Service

`@wdio/electron-service` drives the app via WebDriver, downloads a matching Chromedriver automatically, detects Forge and electron-builder output, and can **mock Electron APIs** in main. Docs: https://webdriver.io/docs/desktop-testing/electron

```ts
// wdio.conf.ts (excerpt)
export const config: WebdriverIO.Config = {
  services: ['electron'],
  capabilities: [{ browserName: 'electron' }],
  specs: ['./e2e/**/*.e2e.ts'],
};
```

```ts
// e2e/open.e2e.ts
import { browser, $, expect } from '@wdio/globals';

it('opens a file', async () => {
  const showOpenDialog = await browser.electron.mock('dialog', 'showOpenDialog');
  await showOpenDialog.mockResolvedValue({ canceled: false, filePaths: ['/tmp/fixtures/sample.md'] });

  await $('button=Open').click();
  await expect(showOpenDialog).toHaveBeenCalled();
});
```

Choose Playwright if the team already uses it for web; choose WDIO if built-in API mocking and automatic binary detection matter more.

## CI Notes

- **Linux:** Electron needs a display. Wrap E2E runs in `xvfb-run`:
  ```bash
  xvfb-run --auto-servernum -- npx playwright test
  ```
- **macOS/Windows runners** have a display; no wrapper needed.
- Build first (`ATLAS_TEST_BUILD=1 npx electron-forge package`), then run E2E against `out/`.
- The Electron binary is downloaded on first run, not at install; prefetch it with `npx install-electron` and cache it (see build-config.md).
- Run unit and component tests on every push; run E2E on PRs to main and before release, on all three OSes if you ship all three.
- Upload Playwright traces (`trace: 'retain-on-failure'`) and screenshots as CI artifacts.
- Use a throwaway `userData` per run (e.g. an env var such as `ATLAS_USER_DATA` that main reads and passes to `app.setPath('userData', ...)` before `ready`) so tests don't share state.

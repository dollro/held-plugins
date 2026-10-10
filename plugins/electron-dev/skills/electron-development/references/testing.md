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

Write handlers as plain functions that take the `IpcMainInvokeEvent` and validated args. Register them in one place. Then test the function directly with a fake event; no Electron needed.

```ts
// src/main/handlers/files.ts
import type { IpcMainInvokeEvent } from 'electron';
import { z } from 'zod';

const ALLOWED_ORIGINS = new Set(['app://atlas']);
const ReadArgs = z.object({ id: z.string().uuid() });

export function assertTrustedSender(event: IpcMainInvokeEvent): void {
  const url = event.senderFrame?.url;
  if (!url || !ALLOWED_ORIGINS.has(new URL(url).origin)) {
    throw new Error('Untrusted IPC sender');
  }
}

export function makeReadDocument(repo: { get(id: string): Promise<string> }) {
  return async (event: IpcMainInvokeEvent, raw: unknown) => {
    assertTrustedSender(event);
    const { id } = ReadArgs.parse(raw);
    return repo.get(id);
  };
}
```

```ts
// src/main/handlers/files.test.ts
import { describe, expect, it, vi } from 'vitest';
import type { IpcMainInvokeEvent } from 'electron';
import { makeReadDocument } from './files';

const fakeEvent = (url: string) =>
  ({ senderFrame: { url } }) as unknown as IpcMainInvokeEvent;

describe('readDocument', () => {
  const repo = { get: vi.fn().mockResolvedValue('# hello') };
  const handler = makeReadDocument(repo);
  const id = '3f1c8a52-6a3e-4d2b-9a57-0c4b8e2f1d11';

  it('returns content for a trusted sender', async () => {
    await expect(handler(fakeEvent('app://atlas/index.html'), { id })).resolves.toBe('# hello');
  });

  it('rejects untrusted origins', async () => {
    await expect(handler(fakeEvent('https://evil.example'), { id })).rejects.toThrow('Untrusted');
  });

  it('rejects malformed args', async () => {
    await expect(handler(fakeEvent('app://atlas/'), { id: 42 })).rejects.toThrow();
  });
});
```

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

const api: AtlasApi = {
  readDocument: vi.fn().mockResolvedValue('# hello'),
  onUpdateAvailable: vi.fn(() => () => {}),
};
Object.defineProperty(window, 'api', { value: api, writable: true });
```

Typing the stub against the same `AtlasApi` interface the preload implements keeps tests and contract in sync.

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
    // packaged build instead: executablePath: 'out/atlas-linux-x64/atlas'
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

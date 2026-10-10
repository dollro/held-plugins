# Typed IPC

One shared contract file drives the preload bridge, the main handlers and the renderer types. Main validates every payload at runtime (zod) and every sender (origin allowlist). The renderer never sees `ipcRenderer`.

## Why Hand-Rolled

- Typed-IPC libraries (e.g. `electron-trpc`, `@electron-toolkit/typed-ipc`) come and go, and several have stalled or lag behind their peer dependencies. Before adopting one, check its release activity and peer ranges (`sources.md` → Version notes has the last snapshot); otherwise default to the pattern below.
- The pattern below is about 100 lines, has no runtime dependency except zod, and follows the official IPC guidance: `invoke`/`handle` for requests, never `sendSync`, expose narrow functions, never pass the `IpcRendererEvent` to page code.

Docs: https://www.electronjs.org/docs/latest/tutorial/ipc

## Layout

```
src/
  shared/ipc-contract.ts   ← channel names, zod schemas, request/response types, AtlasApi
  main/ipc.ts              ← registers handlers from the contract
  preload/preload.ts       ← builds window.api, checked against AtlasApi (distinct name: Vite names bundles after the entry file)
  renderer/env.d.ts        ← declares window.api: AtlasApi
```

`shared/` must only import `zod` and types: it is bundled into main, preload and renderer.

## Contract

```typescript
// src/shared/ipc-contract.ts
import { z } from 'zod';
import { UI_LOCALES } from './locales'; // pure data, see accessibility-i18n.md

const DocumentId = z.string().uuid(); // main owns the id → path mapping; the renderer never sends paths
export const ThemePref = z.enum(['system', 'light', 'dark']);
export const UiLocale = z.enum(UI_LOCALES);

/** One schema per setting key: the value is typed and validated by its key, so handlers never re-parse. */
const SettingChange = z.discriminatedUnion('key', [
  z.object({ key: z.literal('theme'), value: ThemePref }),
  z.object({ key: z.literal('language'), value: UiLocale }),
]);
const Settings = z.object({ theme: ThemePref, language: UiLocale });
const LocaleInfo = z.object({ locale: UiLocale, dir: z.enum(['ltr', 'rtl']), formatLocale: z.string().max(35) });
const TelemetryConsent = z.object({ crashReports: z.boolean(), usage: z.boolean() });

/** renderer → main, request/response via invoke/handle */
export const invokeContract = {
  'document:read': {
    request: z.object({ id: DocumentId }),
    response: z.object({ name: z.string(), content: z.string(), mtimeMs: z.number() }),
  },
  'document:start-drag': { request: z.object({ id: DocumentId }), response: z.void() },
  'settings:set': { request: SettingChange, response: z.object({ ok: z.literal(true) }) },
  'settings:get-all': { request: z.void(), response: Settings },
  'i18n:get': { request: z.void(), response: LocaleInfo },
  'telemetry:set-consent': { request: TelemetryConsent, response: z.void() },
  'app:version': { request: z.void(), response: z.string() },
  'context-menu:show': {
    request: z.discriminatedUnion('kind', [
      z.object({ kind: z.literal('text-selection') }),
      z.object({ kind: z.literal('document'), id: DocumentId }),
    ]),
    response: z.void(),
  },
  'indexer:connect': { request: z.void(), response: z.void() }, // port arrives on portChannels.indexer
  'update:restart': { request: z.void(), response: z.void() },
} as const;

/** main → renderer, fire-and-forget events */
export const eventContract = {
  'update:ready': z.object({ version: z.string() }), // downloaded, restart to install
  'sync:progress': z.object({ done: z.number(), total: z.number() }),
  'menu:command': z.enum(['new', 'save', 'preferences']),
  'document:opened': z.object({ id: DocumentId, name: z.string() }),
  'document:action': z.object({ action: z.enum(['open', 'delete']), id: DocumentId }),
  'settings:changed': SettingChange, // broadcast to every window
  'theme:changed': z.object({ dark: z.boolean(), highContrast: z.boolean() }),
  'i18n:changed': LocaleInfo,
} as const;

/** MessagePort handoff (process-architecture.md): the only messages sent outside emit(), because ports need postMessage. */
export const portChannels = { indexer: 'indexer:port' } as const;
export type PortChannel = (typeof portChannels)[keyof typeof portChannels]; // preload checks its literal against this

export type SettingChange = z.output<typeof SettingChange>;
export type InvokeContract = typeof invokeContract;
export type InvokeChannel = keyof InvokeContract;
export type Req<C extends InvokeChannel> = z.input<InvokeContract[C]['request']>;
export type Res<C extends InvokeChannel> = z.output<InvokeContract[C]['response']>;

export type EventChannel = keyof typeof eventContract;
export type EventPayload<C extends EventChannel> = z.output<(typeof eventContract)[C]>;

type Invoke<C extends InvokeChannel> = (req: Req<C>) => Promise<Res<C>>; // Req void → call with no argument
type Subscribe<C extends EventChannel> = (cb: (payload: EventPayload<C>) => void) => () => void;

/** The window.api surface. Lives here so preload, renderer and tests share one type. */
export interface AtlasApi {
  readDocument: Invoke<'document:read'>;
  startDocumentDrag: Invoke<'document:start-drag'>;
  setSetting: Invoke<'settings:set'>;
  getSettings: Invoke<'settings:get-all'>;
  getLocale: Invoke<'i18n:get'>;
  setTelemetryConsent: Invoke<'telemetry:set-consent'>;
  appVersion: Invoke<'app:version'>;
  showContextMenu: Invoke<'context-menu:show'>;
  connectIndexer: Invoke<'indexer:connect'>;
  restartToUpdate: Invoke<'update:restart'>;
  onUpdateReady: Subscribe<'update:ready'>;
  onSyncProgress: Subscribe<'sync:progress'>;
  onMenuCommand: Subscribe<'menu:command'>;
  onDocumentOpened: Subscribe<'document:opened'>;
  onDocumentAction: Subscribe<'document:action'>;
  onSettingsChanged: Subscribe<'settings:changed'>;
  onThemeChanged: Subscribe<'theme:changed'>;
  onLocaleChanged: Subscribe<'i18n:changed'>;
}
```

Naming: `domain:action`. Keep channels coarse-grained and intention-revealing (`document:read`, not `fs:call`); never a generic "run this" channel. Files are addressed by an id that main issued (see native-integration.md); the renderer never hands main a filesystem path.

## Main Handlers

```typescript
// src/main/ipc.ts
import { app, ipcMain, type IpcMainInvokeEvent, type WebContents } from 'electron';
import {
  invokeContract, eventContract,
  type InvokeChannel, type Req, type Res, type EventChannel, type EventPayload,
} from '../shared/ipc-contract';
import { assertTrustedSender } from './security';
import { readDocument, startDocumentDrag } from './documents'; // id → path registry owned by main
import { applySetting, settings } from './settings';           // see app-lifecycle.md
import { currentLocaleInfo } from './locale';                  // see accessibility-i18n.md
import { setTelemetryConsent } from './telemetry';             // see debugging.md
import { showContextMenu } from './context-menu';              // see native-integration.md
import { connectIndexer } from './indexer';                    // see process-architecture.md
import { restartToUpdate } from './updater';                   // see auto-update.md

type Handler<C extends InvokeChannel> = (req: Req<C>, event: IpcMainInvokeEvent) => Promise<Res<C>> | Res<C>;
type Handlers = { [C in InvokeChannel]: Handler<C> };

const handlers: Handlers = {
  'document:read': ({ id }) => readDocument(id), // unknown id → throws
  'document:start-drag': ({ id }, event) => startDocumentDrag(id, event.sender), // native-integration.md
  'settings:set': (change) => applySetting(change), // persists, applies, broadcasts settings:changed
  'settings:get-all': () => settings.getAll(),
  'i18n:get': () => currentLocaleInfo(),
  'telemetry:set-consent': (consent) => setTelemetryConsent(consent),
  'app:version': () => app.getVersion(),
  'context-menu:show': (req, event) => showContextMenu(req, event.sender),
  'indexer:connect': (_req, event) => connectIndexer(event.sender),
  'update:restart': () => restartToUpdate(),
};

export function registerIpc(): void {
  for (const channel of Object.keys(invokeContract) as InvokeChannel[]) {
    const { request } = invokeContract[channel];
    ipcMain.handle(channel, async (event, raw: unknown) => {
      assertTrustedSender(event);              // origin allowlist on event.senderFrame
      const parsed = request.safeParse(raw);
      if (!parsed.success) throw new Error(`Invalid payload for ${channel}`);
      const handler = handlers[channel] as (req: unknown, e: IpcMainInvokeEvent) => unknown;
      return handler(parsed.data, event);
    });
  }
}

export function emit<C extends EventChannel>(target: WebContents, channel: C, payload: EventPayload<C>): void {
  if (target.isDestroyed()) return;
  target.send(channel, eventContract[channel].parse(payload));
}
```

- `Handlers` being a mapped type means the compiler fails if a channel in the contract has no handler.
- Setting values are typed per key (`SettingChange` is a discriminated union): handlers narrow on `key` and get a validated `value`; never re-parse it.
- Errors thrown in handlers reach the renderer as a rejected promise with only the message (Electron serializes it); don't put secrets or stack traces in messages. Return a discriminated `{ ok: false, code }` result if the UI needs structured errors.
- `assertTrustedSender` is defined in security.md.

## Preload Bridge

```typescript
// src/preload/preload.ts (bundled to CJS, sandboxed)
import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron';
import type { AtlasApi, InvokeChannel, Req, Res, EventChannel, EventPayload } from '../shared/ipc-contract';

function invoke<C extends InvokeChannel>(channel: C) {
  return (req: Req<C>): Promise<Res<C>> => ipcRenderer.invoke(channel, req);
}

function subscribe<C extends EventChannel>(channel: C) {
  return (cb: (payload: EventPayload<C>) => void): (() => void) => {
    // Wrap: never hand the IpcRendererEvent (and event.sender) to page code
    const listener = (_e: IpcRendererEvent, payload: EventPayload<C>) => cb(payload);
    ipcRenderer.on(channel, listener);
    return () => { ipcRenderer.removeListener(channel, listener); };
  };
}

const api = {
  readDocument: invoke('document:read'),
  startDocumentDrag: invoke('document:start-drag'),
  setSetting: invoke('settings:set'),
  getSettings: invoke('settings:get-all'),
  getLocale: invoke('i18n:get'),
  setTelemetryConsent: invoke('telemetry:set-consent'),
  appVersion: invoke('app:version'), // Req is void, so callable with no argument
  showContextMenu: invoke('context-menu:show'),
  connectIndexer: invoke('indexer:connect'),
  restartToUpdate: invoke('update:restart'),
  onUpdateReady: subscribe('update:ready'),
  onSyncProgress: subscribe('sync:progress'),
  onMenuCommand: subscribe('menu:command'),
  onDocumentOpened: subscribe('document:opened'),
  onDocumentAction: subscribe('document:action'),
  onSettingsChanged: subscribe('settings:changed'),
  onThemeChanged: subscribe('theme:changed'),
  onLocaleChanged: subscribe('i18n:changed'),
} satisfies AtlasApi; // compile error if the bridge and the shared type drift

contextBridge.exposeInMainWorld('api', api);
```

- Import only types from the contract in the preload (`import type`), so zod is not pulled into the sandboxed bundle unless you want client-side validation.
- Expose one function per capability. Never expose `ipcRenderer`, `invoke(channel, ...)` with a free-form channel, or `removeAllListeners`.
- `ipcRenderer` itself can no longer cross `contextBridge` (since v29); values crossing the bridge are copied (structured clone), so functions and class instances lose their prototype.

## Renderer Typing

```typescript
// src/renderer/env.d.ts
import type { AtlasApi } from '../shared/ipc-contract';

declare global {
  interface Window {
    api: AtlasApi;
  }
}

export {};
```

```typescript
// src/renderer/editor.ts
const offOpened = window.api.onDocumentOpened(async ({ id }) => {
  const { name, content } = await window.api.readDocument({ id });
  showDocument(name, content);
});
const offProgress = window.api.onSyncProgress(({ done, total }) => setProgress(done / total));
// on teardown
offOpened();
offProgress();
```

`AtlasApi` lives in `src/shared/` so the renderer and its tests import it without reaching into the preload source.

## Main → Renderer Events

```typescript
// anywhere in main
emit(mainWindow.webContents, 'update:ready', { version: '2.4.0' });
```

For broadcast to all windows, iterate `BrowserWindow.getAllWindows()`. For high-frequency streams (progress ticks, logs), throttle in main or move to a `MessagePort` (see process-architecture.md).

## Testing the Contract

- Unit-test handlers directly (`handlers['document:read']({ id }, fakeEvent)`) with Vitest; no Electron needed.
- Test schemas: invalid payloads must be rejected (`request.safeParse(bad).success === false`).
- Test `assertTrustedSender` with fake `senderFrame.origin` values (`'https://evil.example'`, `'null'`, `'file://'`) and with `senderFrame: null`.
- E2E (Playwright) covers the real bridge; see testing.md.

## Checklist

- [ ] Every channel lives in `src/shared/ipc-contract.ts`
- [ ] Every handler validates sender and payload before doing work
- [ ] Preload exposes named functions only, checked with `satisfies AtlasApi` from `src/shared/`
- [ ] Subscriptions return an unsubscribe and wrap the listener
- [ ] No `sendSync`, no `ipcRenderer` exposure, no generic pass-through channel

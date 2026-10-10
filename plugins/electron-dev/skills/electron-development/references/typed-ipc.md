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

/** renderer → main, request/response via invoke/handle */
const DocumentId = z.string().uuid(); // main owns the id → path mapping; the renderer never sends paths

export const invokeContract = {
  'document:read': {
    request: z.object({ id: DocumentId }),
    response: z.object({ name: z.string(), content: z.string(), mtimeMs: z.number() }),
  },
  'settings:set': {
    request: z.object({ key: z.enum(['theme', 'language']), value: z.string().max(64) }),
    response: z.object({ ok: z.literal(true) }),
  },
  'app:version': {
    request: z.void(),
    response: z.string(),
  },
  'context-menu:show': {
    request: z.discriminatedUnion('kind', [
      z.object({ kind: z.literal('text-selection') }),
      z.object({ kind: z.literal('document'), id: DocumentId }),
    ]),
    response: z.void(),
  },
  'update:restart': {
    request: z.void(),
    response: z.void(),
  },
} as const;

/** main → renderer, fire-and-forget events */
export const eventContract = {
  'update:ready': z.object({ version: z.string() }), // downloaded, restart to install
  'sync:progress': z.object({ done: z.number(), total: z.number() }),
  'menu:command': z.enum(['new', 'save', 'preferences']),
  'document:opened': z.object({ id: DocumentId, name: z.string() }),
  'document:action': z.object({ action: z.enum(['open', 'delete']), id: DocumentId }),
} as const;

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
  setSetting: Invoke<'settings:set'>;
  appVersion: Invoke<'app:version'>;
  showContextMenu: Invoke<'context-menu:show'>;
  restartToUpdate: Invoke<'update:restart'>;
  onUpdateReady: Subscribe<'update:ready'>;
  onSyncProgress: Subscribe<'sync:progress'>;
  onMenuCommand: Subscribe<'menu:command'>;
  onDocumentOpened: Subscribe<'document:opened'>;
  onDocumentAction: Subscribe<'document:action'>;
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
import { readDocument } from './documents';        // id → path registry owned by main
import { showContextMenu } from './context-menu';  // see native-integration.md
import { restartToUpdate } from './updater';       // see auto-update.md

type Handler<C extends InvokeChannel> = (req: Req<C>, event: IpcMainInvokeEvent) => Promise<Res<C>> | Res<C>;
type Handlers = { [C in InvokeChannel]: Handler<C> };

const handlers: Handlers = {
  'document:read': ({ id }) => readDocument(id), // unknown id → throws
  'settings:set': async ({ key, value }) => { settings.set(key, value); return { ok: true }; },
  'app:version': () => app.getVersion(),
  'context-menu:show': (req, event) => showContextMenu(req, event.sender),
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
  setSetting: invoke('settings:set'),
  appVersion: invoke('app:version'), // Req is void, so callable with no argument
  showContextMenu: invoke('context-menu:show'),
  restartToUpdate: invoke('update:restart'),
  onUpdateReady: subscribe('update:ready'),
  onSyncProgress: subscribe('sync:progress'),
  onMenuCommand: subscribe('menu:command'),
  onDocumentOpened: subscribe('document:opened'),
  onDocumentAction: subscribe('document:action'),
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

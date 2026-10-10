# Typed IPC

One shared contract file drives the preload bridge, the main handlers and the renderer types. Main validates every payload at runtime (zod) and every sender (origin allowlist). The renderer never sees `ipcRenderer`.

## Why Hand-Rolled

- Typed-IPC libraries (e.g. `electron-trpc`, `@electron-toolkit/typed-ipc`) come and go, and several have stalled or lag behind their peer dependencies. Before adopting one, check its release activity and peer ranges (`sources.md` → Version notes has the last snapshot); otherwise default to the pattern below.
- The pattern below is about 100 lines, has no runtime dependency except zod, and follows the official IPC guidance: `invoke`/`handle` for requests, never `sendSync`, expose narrow functions, never pass the `IpcRendererEvent` to page code.

Docs: https://www.electronjs.org/docs/latest/tutorial/ipc

## Layout

```
src/
  shared/ipc-contract.ts   ← channel names, zod schemas, request/response types
  main/ipc.ts              ← registers handlers from the contract
  preload/preload.ts       ← builds window.api from the contract (distinct name: Vite names bundles after the entry file)
  renderer/env.d.ts        ← declares window.api
```

`shared/` must only import `zod` and types: it is bundled into main, preload and renderer.

## Contract

```typescript
// src/shared/ipc-contract.ts
import { z } from 'zod';

/** renderer → main, request/response via invoke/handle */
export const invokeContract = {
  'file:read': {
    request: z.object({ path: z.string().min(1).max(4096) }),
    response: z.object({ content: z.string(), mtimeMs: z.number() }),
  },
  'settings:set': {
    request: z.object({ key: z.enum(['theme', 'language']), value: z.string().max(64) }),
    response: z.object({ ok: z.literal(true) }),
  },
  'app:version': {
    request: z.void(),
    response: z.string(),
  },
} as const;

/** main → renderer, fire-and-forget events */
export const eventContract = {
  'update:available': z.object({ version: z.string() }),
  'sync:progress': z.object({ done: z.number(), total: z.number() }),
} as const;

export type InvokeContract = typeof invokeContract;
export type InvokeChannel = keyof InvokeContract;
export type Req<C extends InvokeChannel> = z.input<InvokeContract[C]['request']>;
export type Res<C extends InvokeChannel> = z.output<InvokeContract[C]['response']>;

export type EventChannel = keyof typeof eventContract;
export type EventPayload<C extends EventChannel> = z.output<(typeof eventContract)[C]>;
```

Naming: `domain:action`. Keep channels coarse-grained and intention-revealing (`file:read`, not `fs:call`); never a generic "run this" channel.

## Main Handlers

```typescript
// src/main/ipc.ts
import { app, ipcMain, type IpcMainInvokeEvent, type WebContents } from 'electron';
import {
  invokeContract, eventContract,
  type InvokeChannel, type Req, type Res, type EventChannel, type EventPayload,
} from '../shared/ipc-contract';
import { assertTrustedSender } from './security';

type Handler<C extends InvokeChannel> = (req: Req<C>, event: IpcMainInvokeEvent) => Promise<Res<C>> | Res<C>;
type Handlers = { [C in InvokeChannel]: Handler<C> };

const handlers: Handlers = {
  'file:read': async ({ path }) => readAllowedFile(path), // path checked against allowed roots
  'settings:set': async ({ key, value }) => { settings.set(key, value); return { ok: true }; },
  'app:version': () => app.getVersion(),
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
import type { InvokeChannel, Req, Res, EventChannel, EventPayload } from '../shared/ipc-contract';

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
  readFile: invoke('file:read'),
  setSetting: invoke('settings:set'),
  appVersion: invoke('app:version'), // Req is void, so callable with no argument
  onUpdateAvailable: subscribe('update:available'),
  onSyncProgress: subscribe('sync:progress'),
} as const;

export type AtlasApi = typeof api;

contextBridge.exposeInMainWorld('api', api);
```

- Import only types from the contract in the preload (`import type`), so zod is not pulled into the sandboxed bundle unless you want client-side validation.
- Expose one function per capability. Never expose `ipcRenderer`, `invoke(channel, ...)` with a free-form channel, or `removeAllListeners`.
- `ipcRenderer` itself can no longer cross `contextBridge` (since v29); values crossing the bridge are copied (structured clone), so functions and class instances lose their prototype.

## Renderer Typing

```typescript
// src/renderer/env.d.ts
import type { AtlasApi } from '../preload/preload';

declare global {
  interface Window {
    api: AtlasApi;
  }
}

export {};
```

```typescript
// src/renderer/settings.ts
const { content } = await window.api.readFile({ path: selectedPath });
const off = window.api.onSyncProgress(({ done, total }) => setProgress(done / total));
// on teardown
off();
```

If the renderer tsconfig cannot reach the preload source, export `AtlasApi` from `src/shared/` instead and type the preload object against it with `satisfies AtlasApi`.

## Main → Renderer Events

```typescript
// anywhere in main
emit(mainWindow.webContents, 'update:available', { version: '2.4.0' });
```

For broadcast to all windows, iterate `BrowserWindow.getAllWindows()`. For high-frequency streams (progress ticks, logs), throttle in main or move to a `MessagePort` (see process-architecture.md).

## Testing the Contract

- Unit-test handlers directly (`handlers['file:read']({ path }, fakeEvent)`) with Vitest; no Electron needed.
- Test schemas: invalid payloads must be rejected (`request.safeParse(bad).success === false`).
- Test `assertTrustedSender` with fake `senderFrame.url` values (`https://evil.example`, `file:///...`).
- E2E (Playwright) covers the real bridge; see testing.md.

## Checklist

- [ ] Every channel lives in `src/shared/ipc-contract.ts`
- [ ] Every handler validates sender and payload before doing work
- [ ] Preload exposes named functions only, typed from the contract
- [ ] Subscriptions return an unsubscribe and wrap the listener
- [ ] No `sendSync`, no `ipcRenderer` exposure, no generic pass-through channel

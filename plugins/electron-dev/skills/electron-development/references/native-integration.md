# Native OS Integration

## System Menu Bar

Menu clicks run in main. Commands the UI must handle go to the renderer as the contract event `menu:command`; anything touching the file system (Open…) stays in main.

```typescript
// src/main/menu.ts
import { app, Menu, type BrowserWindow, type MenuItemConstructorOptions } from 'electron';
import type { EventPayload } from '../shared/ipc-contract';
import { emit } from './ipc';
import { pickDocument } from './open-document';
import { openExternalSafe } from './security'; // allowlisted shell.openExternal, see security.md

export function buildAppMenu(win: BrowserWindow): void {
  const isMac = process.platform === 'darwin';
  const command = (cmd: EventPayload<'menu:command'>) => () => emit(win.webContents, 'menu:command', cmd);

  const sep = { type: 'separator' } as const;
  const devItems: MenuItemConstructorOptions[] = app.isPackaged ? [] : [sep, { role: 'reload' }, { role: 'toggleDevTools' }];

  const template: MenuItemConstructorOptions[] = [
    ...(isMac ? [{ label: app.name, submenu: [
      { role: 'about' }, sep, { label: 'Settings…', accelerator: 'Cmd+,', click: command('preferences') },
      sep, { role: 'services' }, sep, { role: 'hide' }, { role: 'hideOthers' }, { role: 'unhide' }, sep, { role: 'quit' },
    ] } satisfies MenuItemConstructorOptions] : []),
    { label: 'File', submenu: [
      { label: 'New', accelerator: 'CmdOrCtrl+N', click: command('new') },
      { label: 'Open…', accelerator: 'CmdOrCtrl+O', click: () => void pickDocument() },
      sep, { label: 'Save', accelerator: 'CmdOrCtrl+S', click: command('save') },
      sep, isMac ? { role: 'close' } : { role: 'quit' },
    ] },
    { role: 'editMenu' },
    { label: 'View', submenu: [
      { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }, sep, { role: 'togglefullscreen' }, ...devItems,
    ] },
    { role: 'windowMenu' },
    { role: 'help', submenu: [
      { label: 'Documentation', click: () => openExternalSafe('https://docs.acme.example/atlas') },
      { label: 'Report an Issue', click: () => openExternalSafe('https://acme.example/atlas/support') },
    ] },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}
```

- `editMenu` / `windowMenu` roles give platform-correct standard submenus; spell out a submenu only when you add items. Labels shown in English here come from main's translator in a localized app (accessibility-i18n.md).
- Add "Check for Updates…" to the app menu (macOS) or Help (Windows/Linux) when the updater supports it (auto-update.md).

## Keyboard Shortcuts

| Layer | Fires when | Use for |
|-|-|-|
| Menu `accelerator` | App focused | Every app command; discoverable and shown in the menu. The default |
| `before-input-event` on `webContents` | Before the page and the menu see the key | Blocking or remapping keys |
| `globalShortcut` | Any app focused, system-wide | One or two opt-in, user-rebindable actions (quick capture) |

```typescript
// src/main/shortcuts.ts
export function registerShortcuts(win: BrowserWindow, quickCapture: string | null): boolean {
  win.webContents.on('before-input-event', (event, input) => { // no reload in packaged builds
    if (app.isPackaged && input.type === 'keyDown' && (input.control || input.meta) && input.key.toLowerCase() === 'r') event.preventDefault();
  });
  if (!quickCapture) return true; // global shortcut is opt-in, off by default
  const ok = globalShortcut.register(quickCapture, () => { win.show(); win.focus(); emit(win.webContents, 'menu:command', 'new'); });
  if (!ok) log.warn('Global shortcut unavailable', { quickCapture }); // taken elsewhere: tell the user, offer rebinding
  return ok;
}
app.on('will-quit', () => globalShortcut.unregisterAll());
```

- `globalShortcut` works only after `ready`. `register` returns `false` when another app owns the combination; the OS does not say which.
- On Wayland, global shortcuts go through the desktop portal: the desktop name must resolve to the app's `.desktop` file, or some GNOME versions silently deny the bind (sources.md). GNOME may also ask the user to consent on first bind; treat a `false` from `register` as normal.
- Avoid combinations screen readers and the OS reserve (Ctrl+Option on macOS, Insert/CapsLock combos on Windows); see accessibility-i18n.md.

## Context Menus

The renderer asks for a menu through the contract channel `context-menu:show` (typed-ipc.md); `registerIpc()` has already run `assertTrustedSender` and the zod schema (a discriminated union: `text-selection`, or `document` with an id). Main builds the menu and resolves any file path itself from the id; a path never comes from the renderer.

```typescript
// src/main/context-menu.ts
import { BrowserWindow, Menu, shell, type MenuItemConstructorOptions, type WebContents } from 'electron';
import type { Req } from '../shared/ipc-contract';
import { documentPath } from './documents';
import { emit } from './ipc';

function templateFor(req: Req<'context-menu:show'>, sender: WebContents): MenuItemConstructorOptions[] {
  if (req.kind === 'text-selection') return [{ role: 'copy' }, { role: 'cut' }, { role: 'paste' }];

  const filePath = documentPath(req.id); // throws for ids main never issued → invoke rejects
  const act = (action: 'open' | 'delete') => () => emit(sender, 'document:action', { action, id: req.id });
  return [
    { label: 'Open', click: act('open') },
    { label: 'Delete…', click: act('delete') }, // renderer confirms, then calls a delete channel
    { type: 'separator' },
    {
      label: process.platform === 'darwin' ? 'Show in Finder' : 'Show in Folder',
      click: () => shell.showItemInFolder(filePath),
    },
  ];
}

export function showContextMenu(req: Req<'context-menu:show'>, sender: WebContents): void {
  const window = BrowserWindow.fromWebContents(sender) ?? undefined;
  Menu.buildFromTemplate(templateFor(req, sender)).popup({ window });
}
```

```typescript
// src/renderer/context-menu.ts
document.addEventListener('contextmenu', (event) => {
  const target = event.target instanceof Element ? event.target : null;
  if (target?.closest('input, textarea, [contenteditable]')) return; // main's spellchecker menu
  const id = target?.closest<HTMLElement>('[data-document-id]')?.dataset.documentId;
  if (window.getSelection()?.toString()) {
    event.preventDefault();
    void window.api.showContextMenu({ kind: 'text-selection' });
  } else if (id) {
    event.preventDefault();
    void window.api.showContextMenu({ kind: 'document', id });
  }
});

const off = window.api.onDocumentAction(({ action, id }) =>
  action === 'open' ? openDocumentView(id) : confirmDelete(id),
);
```

### Spellchecker menu for editable fields

Electron shows no context menu by default. Editable fields get theirs from main via the `webContents` `context-menu` event, with no renderer round trip; the renderer listener above skips `input, textarea, [contenteditable]` so it does not `preventDefault` there.

```typescript
// src/main/context-menu.ts (continued)
export function attachEditableMenu(win: BrowserWindow): void {
  win.webContents.on('context-menu', (_event, params) => {
    if (!params.isEditable) return;
    const wc = win.webContents;
    const fixes: MenuItemConstructorOptions[] = params.dictionarySuggestions
      .map((s) => ({ label: s, click: () => wc.replaceMisspelling(s) }));
    if (params.misspelledWord) {
      fixes.push({ label: t('menu.addToDictionary'), click: () => wc.session.addWordToSpellCheckerDictionary(params.misspelledWord) });
    }
    Menu.buildFromTemplate([...fixes, ...(fixes.length ? [{ type: 'separator' } as const] : []),
      { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }]).popup({ window: win });
  });
}
```

`t()` is main's translator; spellchecker languages and localized labels are in accessibility-i18n.md.

## Opening Documents and Deep Links

Every path that main opens (Open… dialog, Finder/Explorer double-click, second instance) goes through one function. It registers the path in main's document registry and sends the renderer only an id and a display name; `document:read` and the context menu resolve the id back in main.

```typescript
// src/main/documents.ts — id → path registry, owned by main
import { randomUUID } from 'node:crypto';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';

const byId = new Map<string, string>(); // only paths main chose: dialog results, OS open events

export function registerDocument(filePath: string): { id: string; name: string } {
  const id = randomUUID();
  byId.set(id, path.resolve(filePath));
  return { id, name: path.basename(filePath) };
}

export function documentPath(id: string): string {
  const p = byId.get(id);
  if (!p) throw new Error('Unknown document');
  return p;
}

export async function readDocument(id: string) {
  const p = documentPath(id);
  const [content, { mtimeMs }] = await Promise.all([readFile(p, 'utf8'), stat(p)]);
  return { name: path.basename(p), content, mtimeMs };
}
```

```typescript
// src/main/open-document.ts
import { app, dialog, type BrowserWindow } from 'electron';
import { registerDocument } from './documents';
import { emit } from './ipc';

let target: BrowserWindow | null = null;
const pending: string[] = []; // paths that arrive before the window has loaded (macOS open-file fires early)

export function setDocumentTarget(win: BrowserWindow): void {
  win.webContents.once('did-finish-load', () => {
    target = win;
    for (const p of pending.splice(0)) openDocument(p);
  });
  win.once('closed', () => { target = null; });
}

export function openDocument(filePath: string): void {
  if (!target) { pending.push(filePath); return; }
  emit(target.webContents, 'document:opened', registerDocument(filePath));
  app.addRecentDocument(filePath); // macOS Dock menu / File > Open Recent role, Windows Jump List
  if (target.isMinimized()) target.restore();
  target.focus();
}

export async function pickDocument(): Promise<void> {
  if (!target) return;
  const { canceled, filePaths } = await dialog.showOpenDialog(target, {
    properties: ['openFile'],
    filters: [{ name: 'Atlas Documents', extensions: ['atlas', 'md'] }],
  });
  if (!canceled && filePaths[0]) openDocument(filePaths[0]);
}
```

```typescript
// src/main/main.ts (excerpt)
import path from 'node:path';
import { openDocument } from './open-document';

const docFromArgv = (argv: string[]) =>
  argv.find((a) => path.isAbsolute(a) && a.toLowerCase().endsWith('.atlas'));
const linkFromArgv = (argv: string[]) => argv.find((a) => a.startsWith('atlas://'));

// macOS: Finder double-click, drop on Dock icon (can fire before 'ready')
app.on('open-file', (event, filePath) => { event.preventDefault(); openDocument(filePath); });
// macOS: deep link
app.on('open-url', (event, url) => { event.preventDefault(); handleDeepLink(url); });

// Windows/Linux: paths and deep links arrive as argv, on first launch or in a second instance
function routeArgv(argv: string[]): void {
  const doc = docFromArgv(argv), link = linkFromArgv(argv);
  if (doc) openDocument(doc); // queued until the window has loaded
  if (link) handleDeepLink(link);
}
app.on('second-instance', (_event, argv) => routeArgv(argv));
routeArgv(process.argv);

app.setAsDefaultProtocolClient('atlas');

// Deep links are untrusted input, like renderer messages: allowlist actions, validate params
function handleDeepLink(raw: string): void {
  let url: URL;
  try { url = new URL(raw); } catch { return; }
  if (url.protocol !== 'atlas:') return;
  if (url.host === 'settings') { /* emit(win.webContents, 'menu:command', 'preferences') */ }
  // any other action: ignore, never pass to shell or fs
}
```

Call `setDocumentTarget(mainWindow)` where the window is created (process-architecture.md), next to `buildAppMenu(mainWindow)`. The deep-link scheme (`atlas://`) is separate from the internal `app://` scheme that serves the renderer.

Registration is packaging config; check the current docs for exact keys:

- Forge: `packagerConfig.protocols` (macOS URL schemes); file types on macOS via `packagerConfig.extendInfo` (`CFBundleDocumentTypes`); Linux via the deb/rpm makers' `mimeType`. On Windows, `app.setAsDefaultProtocolClient` registers the URL scheme at runtime; Squirrel.Windows registers no file types, so write those registry keys on `--squirrel-install` or use another Windows maker.
- electron-builder: top-level `fileAssociations` (`ext: atlas`, `name: Atlas Document`, `role: Editor`) and `protocols` (`name: Atlas`, `schemes: [atlas]`); NSIS registers both on Windows.

## System Tray

```typescript
// src/main/tray.ts
import { app, Menu, nativeImage, Tray, type BrowserWindow } from 'electron';
import path from 'node:path';
import { emit } from './ipc';

// Packaged: copied to resources/ via packagerConfig.extraResource; dev: repo assets/ (main runs from .vite/build)
const ASSETS = app.isPackaged ? path.join(process.resourcesPath, 'assets') : path.join(__dirname, '../../assets');
export const assetPath = (name: string) => path.join(ASSETS, name);
type TrayState = 'idle' | 'syncing' | 'error';

let tray: Tray | null = null; // module scope: a garbage-collected Tray vanishes from the menu bar

export function createTray(win: BrowserWindow): void {
  const show = () => { win.show(); win.focus(); };
  tray = new Tray(iconFor('idle'));
  tray.setToolTip('Atlas');
  tray.on('click', show); // Windows; macOS opens the menu, Linux (AppIndicator) may not emit clicks
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open Atlas', click: show },
    { label: 'Settings…', click: () => { show(); emit(win.webContents, 'menu:command', 'preferences'); } },
    { type: 'separator' }, { role: 'quit' },
  ]));
}

export function setTrayState(state: TrayState): void {
  tray?.setImage(iconFor(state));
  tray?.setToolTip(`Atlas: ${state}`);
}

function iconFor(state: TrayState) {
  // macOS: names ending in "Template" are tinted for light/dark menu bars
  const name = process.platform === 'darwin' ? `tray-${state}Template.png` : `tray-${state}.png`;
  return nativeImage.createFromPath(assetPath(name));
}
```

- Put every tray action in the context menu; click events are not reliable on all Linux desktops.
- To change menu items (e.g. a status line), build a new menu and call `setContextMenu` again.

## Native Notifications

On macOS, current Electron only shows notifications from a code-signed app; unsigned dev builds will not show them (see `code-signing.md`). Renderers can also use the web `Notification` API.

```typescript
// src/main/notify.ts
import { Notification, type BrowserWindow } from 'electron';

const live = new Set<Notification>(); // keep a reference, or click handlers can be lost to GC

export function notify(win: BrowserWindow, title: string, body: string): void {
  if (!Notification.isSupported()) return;
  const n = new Notification({ title, body });
  live.add(n);
  n.on('click', () => { win.show(); win.focus(); });
  n.on('close', () => live.delete(n));
  n.show();
}
```

- Platform-specific options (`actions`, `urgency`, `hasReply`, `toastXml`, …) differ per OS; check the [Notification API](https://www.electronjs.org/docs/latest/api/notification) before using them.
- Keep notification text free of secrets; it can appear on the lock screen.

## Clipboard and Dropped Files

- Renderers have no `clipboard` module any more (deprecated, then removed). Use the web Clipboard API there (`navigator.clipboard.readText()`, `writeText()`, `ClipboardItem`), gated by the permission handler in security.md.
- In main, the `clipboard` module remains, but its read/write methods are asynchronous in current Electron: `await` them (e.g. `await clipboard.readText()`) and don't rely on older synchronous examples. Check the [clipboard API](https://www.electronjs.org/docs/latest/api/clipboard) for your version.
- `File.path` no longer exists (removed in v32). Resolve a dropped/selected file's path in the preload with `webUtils.getPathForFile(file)` (see process-architecture.md).

## Dark Mode and Theming

The renderer styles itself with `@media (prefers-color-scheme: dark)`; no IPC needed. Main owns the user's choice and sets `nativeTheme.themeSource`, which drives that media query in every renderer and the native UI (menus, dialogs, title bar).

```typescript
// src/main/theme.ts
// The choice arrives typed via settings:set (ThemePref in the contract); applySetting sets nativeTheme.themeSource.

export function watchTheme(): void { // after 'ready'
  nativeTheme.on('updated', () => {
    const state = { dark: nativeTheme.shouldUseDarkColors, highContrast: nativeTheme.shouldUseHighContrastColors };
    for (const win of BrowserWindow.getAllWindows()) emit(win.webContents, 'theme:changed', state); // contract event
  });
}
```

On `updated`, also repaint native pieces CSS cannot reach: `win.setTitleBarOverlay` colors, non-template tray icons. Set the window `backgroundColor` to the theme background to avoid a white flash before first paint.

## Window Customization

```typescript
// src/main/window.ts (excerpt)
const win = new BrowserWindow({
  titleBarStyle: 'hidden', // keeps native window controls; frame: false removes them too
  ...(process.platform === 'darwin'
    ? { trafficLightPosition: { x: 14, y: 12 } }
    : { titleBarOverlay: { color: '#00000000', symbolColor: '#1f2937', height: 36 } }), // Windows Controls Overlay
  webPreferences: { /* hardened, see security.md */ },
});
```

```css
/* src/renderer/titlebar.css: env() keeps content clear of native controls, wherever they sit (RTL, user settings) */
.titlebar { position: fixed; top: 0; left: env(titlebar-area-x, 0); width: env(titlebar-area-width, 100%);
  height: env(titlebar-area-height, 36px); app-region: drag; -webkit-app-region: drag; }
.titlebar :is(button, input, a, [role='button']) { app-region: no-drag; -webkit-app-region: no-drag; }
```

- Drag regions swallow mouse events: mark every interactive element in them `no-drag`. On Windows a right-click there opens the system menu.
- Prefer `titleBarStyle: 'hidden'` to `frame: false`: native controls keep snap layouts, accessibility and the platform look. Frameless windows must rebuild minimize/maximize/close as keyboard-accessible buttons backed by contract channels.

## Taskbar, Dock and Badges

```typescript
// src/main/attention.ts
export function showSyncProgress(win: BrowserWindow, done: number, total: number, failed = false): void {
  win.setProgressBar(total ? done / total : -1, { mode: failed ? 'error' : 'normal' }); // < 0 removes; mode: Windows
}

export function showUnread(win: BrowserWindow, count: number): void {
  if (process.platform === 'win32') {
    win.setOverlayIcon(count ? nativeImage.createFromPath(assetPath('badge-dot.png')) : null, count ? `${count} unread` : '');
  } else {
    app.setBadgeCount(count); // macOS (needs notification permission); Linux docks with LauncherEntry support
  }
}
```

- Call these from main, which already knows the state. If a count originates in the renderer, add an invoke channel such as `badge:set` with `z.object({ count: z.number().int().min(0).max(9999) })`.
- The overlay description is what screen readers announce. On Linux the badge belongs to the `.desktop` file, so the desktop name must match it.

## Jump Lists and Recent Documents

`app.addRecentDocument(path)` (in `openDocument` above) feeds the macOS Dock menu and Open Recent, and the Windows Jump List (the app must be registered for the file type). Offer `app.clearRecentDocuments()` as "Clear Recent".

```typescript
// src/main/jump-list.ts (Windows; set on every launch, the exe path changes with updates)
if (process.platform === 'win32') {
  app.setUserTasks([{ program: process.execPath, arguments: '--new-document', iconPath: process.execPath, iconIndex: 0,
    title: t('jumpList.newDocument'), description: t('jumpList.newDocumentHint') }]);
}
```

Task arguments return via `process.argv` or `second-instance`; parse them with the deep-link allowlist. `app.setJumpList(categories)` adds custom categories; check its result string (`'ok'` or an error code).

## Dragging Files Out

The renderer starts a native drag by document id; main resolves the path. `startDrag` must run while the HTML drag starts, with a non-empty icon.

```typescript
// src/main/documents.ts (handler for the contract channel 'document:start-drag')
export function startDocumentDrag(id: string, sender: WebContents): void {
  sender.startDrag({ file: documentPath(id), icon: nativeImage.createFromPath(assetPath('drag-file.png')) });
}

// src/renderer/document-list.ts
list.addEventListener('dragstart', (event) => {
  const id = (event.target as HTMLElement).closest<HTMLElement>('[data-document-id]')?.dataset.documentId;
  if (!id) return;
  event.preventDefault();
  void window.api.startDocumentDrag({ id });
});
```

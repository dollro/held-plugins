# Auto-Update System

Updates need **signed builds** (macOS Squirrel.Mac refuses unsigned apps; see `code-signing.md`). Overview: [electronjs.org updates](https://www.electronjs.org/docs/latest/tutorial/updates).

## Choosing an Updater

| Setup | Use when | Mechanism |
|-|-|-|
| `update-electron-app` + update.electronjs.org | Forge, **public** GitHub repo, releases published on GitHub | Free hosted feed over GitHub Releases; built-in `autoUpdater` (Squirrel.Mac / Squirrel.Windows) |
| `update-electron-app` + static storage | Forge, private repo or own hosting (S3, R2, CDN) | Forge publishers (e.g. S3) upload artifacts plus update manifests; client polls a base URL |
| `electron-updater` | electron-builder | `latest*.yml` feeds on GitHub/S3/generic; NSIS, DMG/zip, AppImage; staged rollouts, channels |
| Store (Mac App Store, Microsoft Store, Snap) | Store distribution | Store handles updates; disable in-app updater |

Linux: the built-in `autoUpdater` does not support Linux. Use distro packages/repos, or electron-updater with AppImage.

Keep electron-updater on the same release line as electron-builder, and read both changelogs before a major bump (current lines in `sources.md` → Version notes).

## Squirrel.Windows Startup Events

Squirrel.Windows launches the app with `--squirrel-install`, `--squirrel-updated`, `--squirrel-uninstall` and `--squirrel-firstrun`. The app must create/remove shortcuts and quit immediately for the first three. Forge's Vite + TypeScript template already does this at the top of main:

```ts
// src/main/main.ts — must run before anything else
import { app } from 'electron';
import started from 'electron-squirrel-startup';

if (started) app.quit();
```

- Do **not** check for updates on `--squirrel-firstrun`: Squirrel still holds a lock on the install directory. Delay the first check (e.g. 30 s) or skip it on that run.
- NSIS builds (electron-builder) do not use these events; drop `electron-squirrel-startup` there.

## Forge: update-electron-app

Public GitHub repo via update.electronjs.org:

```ts
// src/main/updater.ts
import { updateElectronApp, UpdateSourceType } from 'update-electron-app';
import log from 'electron-log/main';

export function initUpdates(): void {
  updateElectronApp({
    updateSource: {
      type: UpdateSourceType.ElectronPublicUpdateService,
      repo: 'acme/atlas',
    },
    updateInterval: '1 hour', // minimum 5 minutes
    notifyUser: true,         // built-in "restart now / later" dialog
    logger: log,
  });
}
```

Static storage (private hosting):

```ts
updateElectronApp({
  updateSource: {
    type: UpdateSourceType.StaticStorage,
    baseUrl: `https://updates.acme.example/atlas/${process.platform}/${process.arch}`,
  },
});
```

- Pair with a Forge publisher that writes the manifests (e.g. `@electron-forge/publisher-s3`); macOS needs the `MakerZIP` artifact, Windows the Squirrel `RELEASES` + `.nupkg`.
- `update-electron-app` is a no-op in development (`!app.isPackaged`) and on Linux.
- For custom UX, set `notifyUser: false` and supply `onNotifyUser`, or use the built-in `autoUpdater` directly with the same feed URL.

## electron-builder: electron-updater

```ts
// src/main/updater.ts (ESM; electron-updater is CJS)
import electronUpdater from 'electron-updater';
import { BrowserWindow } from 'electron';
import log from 'electron-log/main';

const { autoUpdater } = electronUpdater;

export function initUpdates(win: BrowserWindow): void {
  autoUpdater.logger = log;
  autoUpdater.autoDownload = true;          // download in background
  autoUpdater.autoInstallOnAppQuit = true;  // install on next quit if user ignores prompt
  autoUpdater.allowDowngrade = false;       // default; never roll users back silently

  autoUpdater.on('update-downloaded', (info) => {
    win.webContents.send('update:ready', { version: info.version });
  });
  autoUpdater.on('error', (err) => log.error('update failed', err));

  void autoUpdater.checkForUpdates();
  setInterval(() => void autoUpdater.checkForUpdates(), 4 * 60 * 60 * 1000);
}
```

Publishing is configured in `electron-builder.yml` (`publish:`), see `build-config.md`. electron-updater verifies the Windows publisher name of a downloaded update against the signing config, so keep the publisher name in your Windows signing settings in sync with the certificate subject (its config key moves between releases; check the electron-builder docs).

Channels: set `channel: beta` in builder config and `autoUpdater.channel = 'beta'` (or `allowPrerelease`) for opt-in beta users.

Differential updates: electron-builder generates blockmaps so clients download only changed blocks; check the electron-builder auto-update docs for which targets support it (NSIS and AppImage are the reliable ones). Do not promise bandwidth savings on macOS.

## Update UX

1. **Check on start** (after the window is shown, delayed a few seconds) and on an **interval** (1–6 h). Skip in dev and on Squirrel first run.
2. **Download silently** in the background. Never block startup on the network.
3. **Notify** when ready: an in-app banner (via IPC to the renderer) or a native dialog. Show the version and a release-notes link.
4. **Restart on consent** only. Offer "Restart now" and "Later"; on "Later", install on next quit.
5. Let users **check manually** from the app menu ("Check for Updates…").
6. Before `quitAndInstall()`, let windows save state; unsaved work must never be lost to an update.

Narrow IPC surface (preload):

```ts
// src/preload/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('updates', {
  onReady: (cb: (v: { version: string }) => void) => {
    const listener = (_e: Electron.IpcRendererEvent, v: { version: string }) => cb(v);
    ipcRenderer.on('update:ready', listener);
    return () => ipcRenderer.removeListener('update:ready', listener);
  },
  restart: () => ipcRenderer.invoke('update:restart'),
});
```

```ts
// main: validate sender, then install
ipcMain.handle('update:restart', (event) => {
  if (!isTrustedSender(event.senderFrame)) return;
  autoUpdater.quitAndInstall();
});
```

## Rollout and Rollback Safety

There is no client-side rollback in Squirrel or electron-updater. Safety comes from release process and server-side controls.

- **Never auto-downgrade.** Keep `allowDowngrade = false`. Fix forward: ship `x.y.z+1` with the revert.
- **Draft, then publish.** Release as a draft, smoke-test signed artifacts on each OS, then publish. Update feeds only see published releases.
- **Staged rollouts** (electron-updater): add `stagingPercentage` to `latest.yml` / `latest-mac.yml` after upload and raise it gradually (10 → 50 → 100). Set it to `0` to halt a bad rollout for users not yet updated ([electron.build auto-update](https://www.electron.build/docs/features/auto-update)).

  ```yaml
  # latest.yml (edited after publish)
  version: 1.4.0
  stagingPercentage: 10
  ```

- **Staged rollouts** (update.electronjs.org): not supported; use prereleases for a beta cohort, then publish stable.
- **Kill switch**: fetch a small signed remote config at startup (e.g. `{ "updatesEnabled": false, "minVersion": "1.3.2" }`) and stop checking or show a "please reinstall" notice. Fail open to the current behaviour if the config is unreachable.
- **Pull a bad release**: unpublish it (GitHub) or restore the previous manifest (static storage) so no new clients pick it up, then ship the fix as a higher version.
- **Crash signal**: report crashes with the app version (crashReporter / `@sentry/electron`) and watch the new version's crash rate before widening the rollout.
- **Migrations**: make data/schema migrations backward-tolerant for one version, since a user may install a fix-forward build over a half-migrated state.

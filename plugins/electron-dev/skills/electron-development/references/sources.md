# Sources

Check these before relying on a snippet in this skill. Last reviewed 2026-10-10.

## Versions and changes

| What | Where |
|-|-|
| Release schedule, current stable, end-of-life dates | https://releases.electronjs.org/schedule |
| Support policy (latest 3 majors, 8-week cadence) | https://www.electronjs.org/docs/latest/tutorial/electron-timelines |
| Breaking changes per major | https://www.electronjs.org/docs/latest/breaking-changes |
| Release notes and individual PRs | https://releases.electronjs.org |
| Forge releases | https://github.com/electron/forge/releases |
| electron-builder / electron-updater releases | https://github.com/electron-userland/electron-builder/releases |
| electron-vite changelog | https://github.com/alex8088/electron-vite/blob/master/CHANGELOG.md |

Check installed versions with `npm view electron version`, `npm view @electron-forge/cli version` and the project lockfile.

## Core docs

| Topic | Where |
|-|-|
| Security checklist | https://www.electronjs.org/docs/latest/tutorial/security |
| Fuses | https://www.electronjs.org/docs/latest/tutorial/fuses |
| ASAR integrity | https://www.electronjs.org/docs/latest/tutorial/asar-integrity |
| IPC | https://www.electronjs.org/docs/latest/tutorial/ipc |
| ESM | https://www.electronjs.org/docs/latest/tutorial/esm |
| utilityProcess | https://www.electronjs.org/docs/latest/api/utility-process |
| Performance | https://www.electronjs.org/docs/latest/tutorial/performance |
| Debugging main | https://www.electronjs.org/docs/latest/tutorial/debugging-main-process |
| Automated testing | https://www.electronjs.org/docs/latest/tutorial/automated-testing |
| Code signing | https://www.electronjs.org/docs/latest/tutorial/code-signing |
| Updates | https://www.electronjs.org/docs/latest/tutorial/updates |
| Native modules | https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules |

## Tooling docs

| Tool | Where |
|-|-|
| Electron Forge | https://www.electronforge.io |
| Forge Vite plugin | https://www.electronforge.io/config/plugins/vite |
| electron-builder | https://www.electron.build |
| electron-builder Windows signing | https://www.electron.build/docs/features/code-signing/code-signing-win |
| electron-updater | https://www.electron.build/docs/features/auto-update |
| electron-vite | https://electron-vite.org |
| Playwright Electron | https://playwright.dev/docs/api/class-electron |
| WebdriverIO Electron service | https://webdriver.io/docs/desktop-testing/electron |
| Sentry for Electron | https://docs.sentry.io/platforms/javascript/guides/electron/ |

## Version notes (as of 2026-10-10)

The other references describe patterns without version pins. Every time-sensitive fact lives here, so refreshing the skill means re-checking this section against the links above.

### Electron

- Latest stable: Electron 44 (Chromium 152, Node 24). Electron 45 due 2026-10-20, which ends support for 42. New major every 8 weeks; latest 3 majors supported.
- Build targets for Electron 44: `node24` (main/preload), `chrome152` (renderer); see performance.md.
- Migration hints kept in the references: sandbox default (v20), `ipcRenderer` cannot cross `contextBridge` (v29), `crashed` / `gpu-process-crashed` removed (v29), `BrowserView` deprecated (v30), `File.path` removed and navigation moved to `webContents.navigationHistory` (v32), ESM main supported (v28), embedded ASAR integrity on macOS (v16) and Windows (v30).
- v40 deprecated and v44 removed the renderer `clipboard` module.
- v44: main-process `clipboard` read/write methods return Promises; `safeStorage` gained async methods.
- v42: the `electron` package no longer downloads its binary on `postinstall`; it downloads on first `electron` run or via `npx install-electron`. `ELECTRON_SKIP_BINARY_DOWNLOAD` is gone. Since v42, macOS notifications require a code-signed app.
- `webPreferences.webviewTag` defaults to `false`; the docs discourage `<webview>` (use `WebContentsView` or an iframe).
- Lifecycle: `powerMonitor` `shutdown` fires only on Linux and macOS. On Windows, `before-quit` and `will-quit` do not fire on system shutdown or logout. `autoUpdater.quitAndInstall()` closes all windows first and then emits `before-quit`.
- `net.isOnline()` is available in main.
- `autoUpdater` supports MSIX (direct package links and JSON feeds); the Electron major that added it is not confirmed (open question).
- `nativeTheme.prefersReducedTransparency` exists, and Chromium supports the `prefers-reduced-transparency` media feature.
- `globalShortcut` on Wayland goes through the desktop portal (GlobalShortcuts); the app's desktop name must resolve to its `.desktop` file. GNOME 50.0/50.1 silently deny binds otherwise.
- `app.getSystemLocale()` and `app.getPreferredSystemLanguages()` are available (after `ready`).
- A build-time V8 code cache for sandboxed renderers (reported ~35% faster cold start) was only seen in a release PR (https://releases.electronjs.org/pr/51703); not confirmed as shipped.

### Electron Forge (v8.0.1, verified against source)

- ESM-only, Node >= 22.12; templates use `moduleResolution: "bundler"` and oxlint/oxfmt. `PublisherGithub` renamed `PublisherGitHub`.
- No `vite-typescript` template any more: `npx create-electron-app@latest <name> --template=vite --typescript`. Config files are `.mts`; main bundled as CommonJS (`.vite/build/main.cjs`, `preload.cjs`); template already includes `FusesPlugin` and `electron-squirrel-startup`. `MAIN_WINDOW_VITE_*` globals and `target: 'main' | 'preload'` confirmed.
- Vite plugin runs on Vite 8 (rolldown) and is still labelled experimental (since Forge 7.5). `concurrent` option since 7.9.
- Vite plugin packaging: `resolveForgeConfig` sets `packagerConfig.ignore` to keep only `/.vite` (unless you set `ignore` yourself), and `packageAfterCopy` copies no dependencies. Before 7.5.0 the plugin copied `dependencies` into the build; 7.5.0 removed that (electron/forge PR #3583). Fix tracked in https://github.com/electron/forge/issues/3738 (milestone 8.0.0, still open in 8.0.1); related #3934 (auto-unpack-natives does nothing under Vite), #4045. The Vite plugin docs still only say native modules "mostly work out of the box" when externalized.
- `electron-forge publish` is a deprecated alias of the new `release` command.
- `--inspect-electron` passes a bare `--inspect` (port 9229); the Forge debugging docs still say 5858.
- Automatic ASAR integrity since Forge 7.4 / `@electron/packager` 18.3.1.
- `@electron-forge/maker-msix` since Forge 7.10: experimental, Windows-only, needs the Windows SDK on the build machine.

### electron-builder / electron-updater / electron-vite

- Current lines: electron-builder 26.17.0, electron-updater 6.8.10 (7.x in alpha), electron-vite 5.x (6 beta on Vite 8).
- `electronFuses` config with camelCase keys, applied before signing. Embedded ASAR integrity supported on macOS and Windows.
- `win.azureSignOptions` is not beta in the 26.x line. The next major (27, alpha) moves Azure signing to `win.sign` with `type: "azure"` (beta) and has electron-updater 7.x verify `win.sign.publisherName`.
- 27 also moves the macOS signing options into `sign` objects (`mac.sign`, `mas.sign`, `masDev.sign`) and ships `electron-builder migrate-schema` to rewrite configs. The references show the flat 26.x keys; run the migration when moving to 27.
- 27 alpha notes also state that an EV certificate no longer bypasses SmartScreen reputation.

### Other tools

- Azure Trusted Signing is renamed Azure Artifact Signing (Microsoft Learn redirects).
- `@electron/osx-sign` v2, `@electron/notarize` v3 (notarytool only; `altool` removed).
- update-electron-app 3.3.0.
- `@sentry/electron` 8 requires Electron 35+.
- electron-log 5 (`electron-log/main`, `/renderer`, `/preload` entry points).
- `@wdio/electron-service` v10. Playwright `_electron` still experimental, needs Electron 21+.
- better-sqlite3: `db.backup()` is asynchronous (returns a Promise); the rest of the API is synchronous.
- Typed-IPC libraries: `electron-trpc` 0.7.1 (Dec 2024, tRPC v10 only) and `@electron-toolkit/typed-ipc` (Nov 2024) had no releases since late 2024.

### Platforms

- Ubuntu (23.10 onwards) restricts unprivileged user namespaces through AppArmor; without an AppArmor profile for the app, Chromium's sandbox fails to start. Ship a profile with deb/rpm packages instead of disabling the sandbox.

## Open questions at last review

- Whether `node:sqlite` is usable inside Electron's main process.
- Which electron-updater targets support differential updates beyond NSIS and AppImage (the references only promise those two).
- Exact names of the async `safeStorage` methods and whether all platforms support them.
- Whether the renderer V8 code cache (release PR above) has shipped.
- When electron-builder 27 goes stable and whether `win.azureSignOptions` keeps working as an alias.
- Which Electron major added MSIX support to `autoUpdater`.
- Whether deferring `before-quit` (flush, then quit) is safe with each updater's `quitAndInstall` (Electron's `autoUpdater`, electron-updater, update-electron-app).
- Whether `@axe-core/playwright` works reliably on the page returned by Playwright's Electron `firstWindow()`.
- Whether `@sentry/electron` renderer events and native minidumps pass through main's `beforeSend` (the references scrub in each process until confirmed).
- The Forge macOS signing guide's name for the MAS installer certificate; Apple and Electron call it "Mac Installer Distribution".
- Whether the Forge Vite template restarts main automatically on main-process changes, or only on typing `rs`.
- Whether Forge's native rebuild runs on modules copied in `packageAfterCopy`, and whether a future Forge release restores dependency packaging for Vite externals (issue #3738).

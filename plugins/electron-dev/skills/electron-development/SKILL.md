---
name: electron-development
description: "Standards and guardrails for building secure, fast cross-platform desktop apps with Electron on a reference stack: Electron Forge + Vite + TypeScript, sandboxed renderers, typed IPC contracts, utilityProcess for heavy work, fuses and ASAR integrity, code signing and notarization, auto-updates, Playwright/Vitest tests. Principles stay stable across releases; version-specific APIs are checked against the official docs at build time. Use when creating or reviewing Electron apps, BrowserWindow/WebContentsView, preload scripts, IPC, contextBridge, native menus/tray/notifications, packaging, signing, notarization, auto-update, app lifecycle, deep links, single instance, window state, local data/SQLite, Mac App Store, MSIX, Flatpak, accessibility, localisation, Electron performance, crash reporting or Electron testing. Triggers: electron, desktop app, BrowserWindow, IPC, preload, contextBridge, electron-forge, electron-builder, electron-vite, utilityProcess, fuses, notarize, deep link, single instance, tray, menu, Mac App Store, MSIX, SQLite."
---

# Electron Development

Standards for Electron apps that are secure by default, start fast and ship signed updates on all three platforms.

This file holds the **principles and guardrails**. They are written to outlast individual releases. The `references/` hold short, idiomatic patterns; they name APIs, not package versions. Electron ships a new major every few weeks, so **the official docs win over every snippet here**. Time-sensitive facts (current majors, tool status) live in one dated place: the "Version notes" in `references/sources.md`.

## Before writing Electron code

1. **Know the reference stack.** Each piece has a clear role:

   | Component | Role |
   |-|-|
   | Electron (a supported major) | Runtime. Only the newest few majors get security fixes |
   | Electron Forge | Official tooling: scaffold, package, make, sign, publish |
   | Vite (via Forge's Vite plugin) | Bundles main, preload and renderer |
   | TypeScript, strict, `moduleResolution: bundler` | All processes plus `src/shared` |
   | Vitest / Playwright | Unit tests / E2E against the built app |
   | update-electron-app or electron-updater | Auto-update |

   **Alternative stack:** electron-vite + electron-builder (+ electron-updater). Community-maintained, not official. Choose it when the project already uses it or needs electron-builder targets Forge lacks (see `references/build-config.md`).
2. **Check what is current.** Look up the latest stable Electron major and the project's lockfile. If the project is behind a supported major, or a new major shipped since the "Version notes" date, read the breaking-changes page for every major in between and flag the gap to the person you are working with.
3. **Verify the API you are about to use** against the docs listed in `references/sources.md`. Use a docs MCP server such as context7 when available, or read the installed `electron.d.ts`. Snippets here show the pattern, not a guaranteed signature.
4. **Read the reference for the part you build** (table below). Do not read all of them upfront.

| Read | When you build or review |
|-|-|
| `references/security.md` | webPreferences, CSP, navigation, permissions, IPC sender checks, custom protocols, fuses, ASAR integrity, secrets |
| `references/process-architecture.md` | Main/preload/renderer roles, ESM rules, BaseWindow + WebContentsView, embedding web content, utilityProcess, MessagePorts, streaming (e.g. local AI), crash recovery, memory |
| `references/typed-ipc.md` | The shared IPC contract (every channel the references use), per-key typed settings, typed preload bridge, validated main handlers, main→renderer events, MessagePort handoff names |
| `references/app-lifecycle.md` | Single instance, deep links, open-file, window state restore, macOS vs Windows/Linux quit, multi-window sync, power and online state |
| `references/persistence.md` | Where data lives, settings vs SQLite vs IndexedDB, migrations, backups, corruption, export and deletion |
| `references/native-integration.md` | Menus, context menus, tray, notifications, file associations, theming, custom title bars, shortcuts, progress, badges, jump lists, recent documents |
| `references/accessibility-i18n.md` | Keyboard and screen-reader access, OS accessibility settings, locale detection, localised native UI, RTL, spellchecker |
| `references/build-config.md` | Forge + Vite project layout, `forge.config.mts`, makers, native modules, dev loop, supply chain, Electron upgrade playbook, CI; electron-builder alternative |
| `references/code-signing.md` | macOS hardened runtime and notarization, Windows HSM / Azure Artifact Signing, Linux |
| `references/distribution.md` | Direct download vs stores, universal/arm64 builds, Mac App Store, MSIX and Microsoft Store, Windows on ARM, AppImage/deb/rpm/Flatpak/Snap |
| `references/auto-update.md` | Choosing an updater, update UX, staged rollouts, rollback safety |
| `references/performance.md` | Startup, bundling, lazy loading, snapshots, profiling, memory, GPU |
| `references/testing.md` | Vitest units, IPC handler tests, Playwright and WebdriverIO E2E, fuse gotcha, CI |
| `references/debugging.md` | Inspecting main, DevTools, process-gone events, crashReporter, Sentry, logging, telemetry consent and PII scrubbing |
| `references/sources.md` | Official docs, release notes, dated version notes, open questions |

## Non-negotiable guardrails

1. **Renderers are untrusted.** `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false`, `webSecurity: true`. Never turn these off to make something work; move the work to main or a utilityProcess instead.
2. **The preload exposes functions, not capabilities.** One narrow function per operation via `contextBridge`. Never expose `ipcRenderer`, `require`, `shell` or raw Node APIs.
3. **Every IPC handler validates its sender and its payload.** Check `event.senderFrame` origin against an allowlist, then validate arguments at runtime (zod or equivalent). Types alone are not validation.
4. **Async IPC only.** `invoke`/`handle` for request/response, `send` for events. No `sendSync`.
5. **No `file://` for app content.** Serve the bundled renderer via a custom protocol (`protocol.handle`) in production.
6. **Lock navigation.** Handle `will-navigate` and `setWindowOpenHandler`; open external links only through an allowlisted `shell.openExternal`.
7. **Ship with fuses set.** RunAsNode, NODE_OPTIONS, `--inspect` arguments and extra `file://` privileges off. ASAR integrity validation and only-load-from-ASAR on. Cookie encryption on.
8. **Main stays responsive.** No blocking I/O or CPU work on the main process. Heavy or crash-prone work runs in a `utilityProcess`.
9. **Releases are signed.** macOS notarized, Windows signed with an HSM-backed certificate. Unsigned macOS builds cannot auto-update or show notifications.
10. **Stay on a supported major.** Plan Electron upgrades as routine maintenance, not a project; falling out of the support window means shipping known Chromium vulnerabilities.

## Default project shape

```
src/
  main/main.ts        # app lifecycle, windows, IPC handlers, menus, updater
  preload/preload.ts  # contextBridge bridge, bundled to CJS (sandboxed preloads cannot load ESM)
  renderer/           # UI framework of choice, talks only to window.api
  shared/             # IPC contract types, pure logic shared by all processes
  workers/            # utilityProcess entry points
forge.config.mts
```

Name entry files after their role, not `index.ts`: the bundler names outputs after the entry file, so two `index.ts` entries collide.

Scaffold with Forge's `create-electron-app` using its Vite + TypeScript template (check `references/sources.md` for the current flags), then apply the guardrails above. Review the generated fuse settings against guardrail 7, and add CSP, navigation locks and the IPC contract yourself; no template covers them.

## Choosing Electron honestly

Electron's strengths are the same Chromium on every OS, Node in the main process and mature packaging and update tooling. The costs are larger installers and memory use. If the person you are working with puts binary size or idle memory above rendering consistency and is fine with Rust, Tauri is the usual alternative; say so rather than force Electron.

## Checklist before handing back

- [ ] webPreferences hardened; CSP set; navigation and window-open locked
- [ ] Every IPC channel in the shared contract, with sender and payload validation in main
- [ ] No deprecated APIs (`BrowserView`, `File.path`, renderer `clipboard`, `crashed` events, `webContents.goBack` etc.)
- [ ] Heavy work off the main process
- [ ] Fuses and ASAR integrity configured; signing and notarization wired for release builds
- [ ] Tests: Vitest for handlers and shared logic, Playwright smoke test against a build
- [ ] Crash and error reporting initialised after consent, in main, renderer and utility processes
- [ ] Single instance, deep links and window state handled; user data under `userData` with migrations
- [ ] Keyboard access, OS accessibility settings and locale respected; native UI localised
- [ ] Anything that deviates from this skill is named, with the reason

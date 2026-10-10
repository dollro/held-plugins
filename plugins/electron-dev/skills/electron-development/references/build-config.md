# Build Configuration

Default stack: **a supported Electron major + Electron Forge + Vite + TypeScript**. Forge is the official packaging and publishing tool ([forge-overview](https://www.electronjs.org/docs/latest/tutorial/forge-overview)). electron-builder + electron-vite is the documented alternative (last section). Current majors, tool statuses and template details are collected in `sources.md` → Version notes.

Signing details live in `code-signing.md`; update wiring in `auto-update.md`.

## Scaffold

```bash
npx create-electron-app@latest atlas --template=vite --typescript
# optional: --package-manager=pnpm
```

What the Forge Vite + TypeScript template gives you (check the [Forge releases](https://github.com/electron/forge/releases) before major bumps):

- Config as ES modules: `forge.config.mts`, `vite.main.config.mts`, `vite.preload.config.mts`, `vite.renderer.config.mts`.
- Main and preload bundled to CommonJS (`.vite/build/main.cjs`, `preload.cjs`), so `__dirname` works in main.
- `FusesPlugin` already wired in; tighten its options as below.
- Squirrel startup handling via `electron-squirrel-startup` at the top of main.
- The Vite plugin may still be labelled experimental; read release notes before bumping Forge or Vite.

## Project Layout

```
atlas/
  forge.config.mts
  vite.main.config.mts
  vite.preload.config.mts
  vite.renderer.config.mts
  build/                     # icons, entitlements.plist
  src/
    main/                    # main process: app lifecycle, windows, IPC handlers
      main.ts
    preload/                 # contextBridge only; bundled to CJS (sandboxed)
      preload.ts
    renderer/                # UI (any framework), no Node access
      index.html
      main.ts
    shared/                  # types + IPC contract shared by all three
      ipc-contract.ts
    workers/                 # utilityProcess entry points, each its own build entry
      indexer-worker.ts
```

The template generates flat `src/main.ts`, `src/preload.ts`, `src/renderer.ts`; move them into folders and update the `entry` paths below. Keep the entry file names distinct: Vite names each bundle after its entry file, so two `index.ts` entries would collide in `.vite/build/`. Sandboxed preloads cannot use ESM, so the preload Vite config must emit CJS.

## forge.config.mts

```ts
import type { ForgeConfig } from '@electron-forge/shared-types';
import { MakerSquirrel } from '@electron-forge/maker-squirrel';
import { MakerDMG } from '@electron-forge/maker-dmg';
import { MakerZIP } from '@electron-forge/maker-zip';
import { MakerDeb } from '@electron-forge/maker-deb';
import { MakerRpm } from '@electron-forge/maker-rpm';
import { VitePlugin } from '@electron-forge/plugin-vite';
import { FusesPlugin } from '@electron-forge/plugin-fuses';
import { PublisherGitHub } from '@electron-forge/publisher-github';
import { FuseV1Options, FuseVersion } from '@electron/fuses';

// Set only for E2E builds (see testing.md); release builds never set it.
const isTestBuild = process.env.ATLAS_TEST_BUILD === '1';

const config: ForgeConfig = {
  packagerConfig: {
    name: 'Atlas',
    appBundleId: 'com.acme.atlas',
    icon: 'build/icon', // .icns / .ico picked per platform
    asar: true,
    // osxSign / osxNotarize / windowsSign: see code-signing.md
  },
  rebuildConfig: {}, // @electron/rebuild runs automatically for native modules
  makers: [
    new MakerSquirrel({ name: 'atlas' }),          // Windows
    new MakerDMG({ format: 'ULFO' }),              // macOS installer
    new MakerZIP({}, ['darwin']),                  // macOS zip (needed for auto-update)
    new MakerDeb({ options: { maintainer: 'Acme', homepage: 'https://acme.example' } }),
    new MakerRpm({}),
  ],
  publishers: [
    new PublisherGitHub({
      repository: { owner: 'acme', name: 'atlas' },
      draft: true,
      prerelease: false,
    }),
  ],
  plugins: [
    new VitePlugin({
      build: [
        { entry: 'src/main/main.ts', config: 'vite.main.config.mts', target: 'main' },
        { entry: 'src/preload/preload.ts', config: 'vite.preload.config.mts', target: 'preload' },
        // utilityProcess entry: emitted next to main.cjs as indexer-worker.cjs
        { entry: 'src/workers/indexer-worker.ts', config: 'vite.main.config.mts', target: 'main' },
      ],
      renderer: [{ name: 'main_window', config: 'vite.renderer.config.mts' }],
    }),
    // Fuses are flipped at package time; see security.md
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: isTestBuild, // Playwright needs it
      [FuseV1Options.GrantFileProtocolExtraPrivileges]: false,
      [FuseV1Options.EnableCookieEncryption]: true, // irreversible once shipped
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
    }),
  ],
};

export default config;
```

Notes:

- The renderer `name` (`main_window`) produces the `MAIN_WINDOW_VITE_DEV_SERVER_URL` / `MAIN_WINDOW_VITE_NAME` globals used in `main` to load the page.
- Forge embeds the ASAR integrity hash automatically on macOS and Windows; Linux is not documented ([asar-integrity](https://www.electronjs.org/docs/latest/tutorial/asar-integrity)).
- `EnableNodeCliInspectArguments: false` breaks Playwright's Electron launcher. The `ATLAS_TEST_BUILD=1` switch above turns it on for E2E builds only; never ship such a build.
- With `RunAsNode` off, spawn Node work via `utilityProcess.fork`, not `child_process.fork` with `ELECTRON_RUN_AS_NODE`.
- Use the VitePlugin `concurrent` option to cap parallel builds if CI runs out of memory.
- Which makers to list depends on the distribution targets (MAS, MSIX, MSI, Flatpak, Snap); see `distribution.md`.

## Dev Loop

`npm start` (`electron-forge start`) runs a Vite dev server for each renderer and Vite watch builds for main and preload.

| Change in | What happens |
|-|-|
| Renderer | Vite HMR; state survives unless the module cannot be hot-replaced |
| Preload | Rebuilt; the template's Vite config reloads open windows (preloads only run on page load) |
| Main / workers | Rebuilt; the template's Vite config restarts the app. If yours does not, type `rs` in the terminal running `start` |
| `forge.config.mts`, Vite configs | Stop and rerun `start` |

- Load the renderer from `MAIN_WINDOW_VITE_DEV_SERVER_URL` when it is defined, otherwise from the packaged files via your custom protocol. Never ship code paths that load the dev server URL in a packaged app (`app.isPackaged` guard).
- Debug main with `electron-forge start --inspect-electron` and attach Chrome DevTools or the editor debugger (`debugging.md`). The fuse that blocks `--inspect` only applies to packaged builds.
- **Source maps**: `build.sourcemap: true` in the main and preload Vite configs during development. For releases use `'hidden'` maps: upload them to the crash reporter (`debugging.md`) and keep them out of the ASAR. Main-process stack traces need source maps enabled in Node (`process.setSourceMapsEnabled(true)` early in main), since the `NODE_OPTIONS` fuse is off.
- Renderer state lost on main restart is normal; persist what developers need (window bounds, current route) the same way production does.

### Monorepos

```
acme/
  package.json            # workspaces: ["apps/*", "packages/*"]
  apps/atlas/             # the Electron app: forge.config.mts, src/main, src/preload, src/renderer
  packages/ipc-contract/  # channel names, zod schemas, types (see typed-ipc.md)
  packages/ui/            # renderer components shared with a web app
```

- The **IPC contract package** is the main reason for a monorepo: main, preload and renderer (and a web client) import the same channel map and schemas. Keep it free of Electron and Node imports so the renderer bundle can use it.
- Let Vite bundle workspace packages from source (point their `exports` at `.ts` files or use a Vite `resolve.alias`); do not mark them `external`, or the packaged app will look for them in `node_modules`.
- Electron, Forge and native modules must resolve from the app package. With pnpm use `node-linker=hoisted` (see Package Managers); with npm/Yarn workspaces, check that hoisting to the root does not hide native modules from `@electron/rebuild` and the packager. Verify with `asar list` (below) after every dependency change.
- Keep `electron` in the app package's own `devDependencies`, so each app in the repo can sit on its own major.

## Native Modules

Forge runs `@electron/rebuild` automatically during `start`, `package` and `make` ([native modules](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)). No `postinstall` rebuild script is needed.

Mark native modules external so Vite does not try to bundle `.node` binaries ([Vite plugin docs](https://www.electronforge.io/config/plugins/vite)):

```ts
// vite.main.config.mts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      external: ['better-sqlite3', 'serialport'],
    },
  },
});
```

**Externals are not packaged automatically.** The Forge Vite plugin sets the packager's `ignore` so that only the `.vite/` build output reaches the app; `node_modules` is dropped, and `dependencies` alone does not change that (history and issue links in `sources.md` → Version notes). An external module therefore needs its own packaging step, or the packaged app fails with `Cannot find module`. Copy each external and its production dependencies into the build in `packageAfterCopy`:

```ts
// forge.config.mts (excerpt)
import { cp, readFile } from 'node:fs/promises';
import path from 'node:path';

const NATIVE_EXTERNALS = ['better-sqlite3']; // same list as rollupOptions.external

async function copyWithDeps(name: string, buildPath: string, seen: Set<string>): Promise<void> {
  if (seen.has(name)) return;
  seen.add(name);
  const from = path.resolve('node_modules', name); // hoisted layout (pnpm: node-linker=hoisted)
  await cp(from, path.join(buildPath, 'node_modules', name), { recursive: true });
  const pkg = JSON.parse(await readFile(path.join(from, 'package.json'), 'utf8'));
  for (const dep of Object.keys(pkg.dependencies ?? {})) await copyWithDeps(dep, buildPath, seen);
}

// in the ForgeConfig object
hooks: {
  packageAfterCopy: async (_config, buildPath) => {
    const seen = new Set<string>();
    for (const name of NATIVE_EXTERNALS) await copyWithDeps(name, buildPath, seen);
  },
},
```

- Keep externals in `dependencies` (not `devDependencies`) so they are installed for production and the hook finds them.
- Alternatives seen in the Forge issue threads: a custom `packagerConfig.ignore` that also keeps `/node_modules` (simple, but ships the whole tree including dev tooling), or `npm install <externals>` in `packageAfterPrune`. Prefer the explicit copy.
- The auto-unpack-natives plugin only unpacks `.node` files that are already in the build; it does not copy modules.
- After every dependency change, check the packaged app: `npx @electron/asar list` (below) must show the module and its dependencies, its `.node` file must be unpacked, and the app must load it on each OS and arch (the binary must be built for Electron's ABI; confirm the copied module was rebuilt, see the open question in sources.md).
- Prefer Node-API modules that ship prebuilt binaries; they avoid compiler toolchains in CI and survive Electron upgrades without a rebuild.
- Build per arch: a native module compiled for x64 will not load in an arm64 app.

## Package Managers

| Manager | Notes |
|-|-|
| npm | Works out of the box. |
| pnpm | Requires `node-linker=hoisted` in `.npmrc`. |
| Yarn | Berry with Plug'n'Play is unsupported; use `nodeLinker: node-modules`. |

```ini
# .npmrc (pnpm)
node-linker=hoisted
```

The `electron` npm package no longer downloads its binary on `postinstall`; it fetches it on the first `electron` run, or explicitly via `npx install-electron` ([breaking changes](https://www.electronjs.org/docs/latest/breaking-changes)). Consequences for CI:

- `ELECTRON_SKIP_BINARY_DOWNLOAD` is gone, and `npm ci --ignore-scripts` no longer skips anything Electron-related. Old CI scripts that relied on either can be cleaned up.
- Add an explicit prefetch step (`npx install-electron`) after `npm ci` so the download happens once, visibly, before tests and packaging.
- Cache the Electron download cache (`~/.cache/electron`, `~/Library/Caches/electron`, `%LOCALAPPDATA%\electron\Cache`) between CI runs.

## CI Matrix (GitHub Actions)

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  make:
    strategy:
      matrix:
        os: [macos-latest, windows-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    permissions:
      contents: write # PublisherGitHub creates/updates the draft release
    steps:
      # Pin every action to its current major (vN) or, stricter, a full commit SHA; look the major up on the action's releases page
      - uses: actions/checkout@vN
      - uses: actions/setup-node@vN
        with:
          node-version: lts/*   # must satisfy Forge's engines.node
          cache: npm
      - uses: actions/cache@vN
        with:
          path: |
            ~/.cache/electron
            ~/Library/Caches/electron
            ~\AppData\Local\electron\Cache
          key: electron-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
      - run: npm ci
      - run: npx install-electron   # prefetch the Electron binary (cached above)
      - run: npm run lint && npm test
      - name: Release
        run: npx electron-forge release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # macOS signing + notarization (see code-signing.md)
          APPLE_SIGNING_CERT_P12: ${{ secrets.APPLE_SIGNING_CERT_P12 }}
          APPLE_SIGNING_CERT_PASSWORD: ${{ secrets.APPLE_SIGNING_CERT_PASSWORD }}
          APPLE_API_KEY_P8: ${{ secrets.APPLE_API_KEY_P8 }}
          APPLE_API_KEY_ID: ${{ secrets.APPLE_API_KEY_ID }}
          APPLE_API_ISSUER: ${{ secrets.APPLE_API_ISSUER }}
          # Windows Azure Artifact Signing
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
```

- `@vN` is a placeholder: replace it with each action's current major, or with a commit SHA if your supply-chain policy requires it.
- Build each OS on its own runner; cross-compiling signed installers is not practical. Arch choices (universal, Windows arm64) and store jobs: `distribution.md`.
- Add a macOS step that imports the `.p12` into a temporary keychain and writes the `.p8` key to disk before `release` (`code-signing.md`).
- `electron-forge release` is the publishing command (`publish` is a deprecated alias in current Forge); use whichever your installed Forge documents.
- Publish as a **draft**, smoke-test the artifacts, then publish. Update clients only see published releases. Run unsigned `make` on pull requests; sign only on tags.

## Supply Chain and Dependency Hygiene

An Electron app ships its whole `dependencies` tree with full OS privileges in main. Treat dependencies as code you ship.

- **Commit the lockfile** and install with `npm ci` (`pnpm install --frozen-lockfile`, `yarn install --immutable`) in CI, so builds use exactly the reviewed tree.
- **Automate updates and audits**: Dependabot or Renovate for npm packages and GitHub Actions; `npm audit --omit=dev` (or the tool's equivalent) as a CI step that fails on high severity in runtime deps. Group Electron, Forge and Vite updates so they move together.
- **Keep main's dependencies few.** Every package in main and preload runs with Node access. Prefer Node and Electron built-ins; a small utility is often better copied than installed. Renderer-only packages belong in `devDependencies`, because Vite bundles them.
- **Avoid install scripts.** Prefer packages without `postinstall`; consider `ignore-scripts=true` in `.npmrc` with an explicit allowlist of packages whose scripts you run (pnpm's `onlyBuiltDependencies`, or a targeted `npm rebuild <pkg>`). Electron itself no longer needs one.
- **Verify what you ship.** List the ASAR after `package` and check for stray files (`.env`, source maps, test fixtures, dev tools):

```bash
npx @electron/asar list out/Atlas-darwin-arm64/Atlas.app/Contents/Resources/app.asar | less
```

- **Licence notices**: the packaged app already contains Electron's `LICENSE` and `LICENSES.chromium.html` next to the executable; keep them. For your own dependencies, generate a third-party licences file at build time (a licence-collector Rollup/Vite plugin or a licence-checker CLI over production deps) and show it from an About or Licences window. Fail the build on licences your policy forbids.
- **Pin the toolchain**: `engines` plus a `.nvmrc`/`.node-version`, and `packageManager` in `package.json` so CI and developers use the same package manager version.

## Upgrading Electron

Only the newest few majors receive security fixes, and a new major ships every couple of months (current numbers: `sources.md` → Version notes). Upgrade on a fixed cadence, not when forced.

1. **Read the breaking changes** for every major between the current and target version ([breaking-changes](https://www.electronjs.org/docs/latest/breaking-changes)), plus the release notes for the Chromium and Node bumps.
2. **One major at a time.** Bump, fix, test, commit; then the next. Skipping majors hides which change broke what.
3. **Upgrade the toolchain with it**: Forge (or electron-builder), `@electron/fuses`, `@electron/rebuild`, Playwright. Check whether the Node version Electron embeds raises the syntax or API level your main bundle may target (Vite `build.target`).
4. **Rebuild native modules** (`start`/`package` do it) and confirm each module loads in a packaged build on every OS and arch.
5. **Run deprecation checks**: launch with `--trace-deprecation` (or set `process.traceDeprecation = true` in dev) and log `process.on('warning', ...)` in main. Clear every warning before the next major removes the API.
6. **Check fuses**: new majors add fuses or change defaults. Compare the `FuseV1Options` list against your config and set new ones explicitly (`security.md`).
7. **Run the full E2E suite** against a packaged, signed build, including update-from-previous-version (`testing.md`, `auto-update.md`).
8. **Roll out in stages**: internal/beta channel first, then a percentage rollout where your updater supports it; watch crash rates per version before going to 100 %.

## Alternative: electron-builder + electron-vite

electron-builder and electron-vite are a mature community stack ([electron.build](https://www.electron.build), [electron-vite.org](https://electron-vite.org)).

Choose it when you need NSIS installers, AppImage or Snap (`distribution.md`), or **electron-updater** features: staged rollouts (`stagingPercentage`), generic/S3 providers, channels.

Not a reason: electron-vite's V8 bytecode option (`build.bytecode`). It requires `sandbox: false` for the preload, which this skill's guardrails forbid; don't enable it.

Stay on Forge when you want the officially maintained toolchain and first-party fuses/signing packages. Both tools embed the ASAR integrity hash on macOS and Windows.

```bash
npm create @quick-start/electron@latest atlas -- --template vue-ts
```

electron-vite uses `src/main`, `src/preload`, `src/renderer` and `electron.vite.config.ts` with one section per target.

```yaml
# electron-builder.yml
appId: com.acme.atlas
productName: Atlas
directories:
  buildResources: build
  output: release/${version}
files:
  - out/**/*            # electron-vite output
asarUnpack:
  - '**/*.node'
mac:
  category: public.app-category.productivity
  hardenedRuntime: true
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  notarize: true        # uses APPLE_API_KEY / APPLE_API_KEY_ID / APPLE_API_ISSUER
  target: [dmg, zip]
electronFuses:          # camelCase keys; applied before signing (see security.md)
  runAsNode: false
  enableNodeOptionsEnvironmentVariable: false
  enableNodeCliInspectArguments: false
  grantFileProtocolExtraPrivileges: false
  enableCookieEncryption: true
  enableEmbeddedAsarIntegrityValidation: true
  onlyLoadAppFromAsar: true
win:
  target: [nsis]
  azureSignOptions:     # Artifact Signing; see code-signing.md
    publisherName: Acme Inc
    endpoint: https://weu.codesigning.azure.net
    codeSigningAccountName: acme-signing
    certificateProfileName: atlas-public
linux:
  target: [AppImage, deb, rpm]
  category: Utility
nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
publish:
  provider: github
  owner: acme
  repo: atlas
  releaseType: draft
```

- Native modules: electron-builder rebuilds via `@electron/rebuild` (`npmRebuild: true` default); keep them external in `electron.vite.config.ts`.
- Fuses: prefer the `electronFuses` config above (flipped before signing, so signatures stay valid). For an E2E build, override `enableNodeCliInspectArguments` from a JS config (`electron-builder.config.js`) reading `ATLAS_TEST_BUILD`, matching the Forge setup. An `afterPack` hook with `@electron/fuses` is the fallback for fuses the config does not expose.
- CI: same matrix; run `npx electron-builder --publish always`. Mac certificate via `CSC_LINK` / `CSC_KEY_PASSWORD`.
- Newer electron-builder majors restructure the config (signing options move into `mac.sign` / `win.sign` objects). Before crossing a major, run `electron-builder migrate-schema` and diff the result.

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

- External modules must remain in `dependencies` (not `devDependencies`) so they are packaged.
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
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*   # must satisfy Forge's engines.node
          cache: npm
      - uses: actions/cache@v4
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

- Build each OS on its own runner; cross-compiling signed installers is not practical.
- For both macOS archs, either run `macos-latest` (arm64) plus an Intel runner, or pass `--arch=universal`.
- Add a macOS step that imports the `.p12` into a temporary keychain and writes the `.p8` key to disk before `release` (see `code-signing.md`).
- `electron-forge release` is the publishing command; `electron-forge publish` is a deprecated alias in current Forge. Use whichever your installed Forge documents.
- Publish as a **draft** release, smoke-test the artifacts, then publish the release. Update clients only see published releases.
- Run unsigned `npx electron-forge make` on pull requests; sign only on tags.

## Alternative: electron-builder + electron-vite

electron-builder and electron-vite are a mature community stack ([electron.build](https://www.electron.build), [electron-vite.org](https://electron-vite.org)).

Choose it when you need:

- **NSIS installers** (custom install dir, per-machine installs) instead of Squirrel.Windows.
- **AppImage** or Snap on Linux.
- **electron-updater** features: staged rollouts (`stagingPercentage`), generic/S3 providers, channels.
- **V8 bytecode** protection of main/preload via electron-vite `build.bytecode` (requires `sandbox: false` for that preload and per-arch builds).

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

# Code Signing

Unsigned apps are blocked by Gatekeeper, flagged by SmartScreen and cannot auto-update on macOS. In current Electron, **macOS notifications also require a code-signed app** ([breaking changes](https://www.electronjs.org/docs/latest/breaking-changes)). Sign every build that leaves CI.

Overview: [electronjs.org code-signing](https://www.electronjs.org/docs/latest/tutorial/code-signing).

## Summary

| Platform | Required | Tooling | Credential |
|-|-|-|-|
| macOS | Yes (Gatekeeper, updates, notifications) | `@electron/osx-sign` + `@electron/notarize` (notarytool) | Developer ID Application cert + App Store Connect API key |
| Windows | Strongly recommended (SmartScreen) | `@electron/windows-sign` (Forge) / `win.azureSignOptions` (electron-builder) | Key in HSM or cloud HSM, e.g. Azure Artifact Signing |
| Linux | No | Optional repo/package signing (GPG) | GPG key |

## macOS

Requirements:

- **Developer ID Application** certificate (Apple Developer Program).
- **Hardened runtime** enabled (Forge's `osxSign` defaults handle this).
- **Entitlements**: Electron's JIT needs a minimal set.
- **Notarization** via `notarytool` (Apple retired `altool`; don't copy examples that use it). Auth options are Apple ID + app-specific password, App Store Connect API key, or a keychain profile. Prefer the **API key** for CI.

```xml
<!-- build/entitlements.mac.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-jit</key><true/>
  <!-- add only what you need, e.g.: -->
  <!-- <key>com.apple.security.device.camera</key><true/> -->
</dict>
</plist>
```

Avoid `com.apple.security.cs.disable-library-validation` and `allow-unsigned-executable-memory` unless a native module demands it.

### Forge

```ts
// forge.config.mts (packagerConfig excerpt)
packagerConfig: {
  appBundleId: 'com.acme.atlas',
  osxSign: {
    optionsForFile: () => ({ entitlements: 'build/entitlements.mac.plist' }),
  }, // object must exist (even {}) for signing to run
  osxNotarize: {
    appleApiKey: process.env.APPLE_API_KEY!,       // path to AuthKey_XXXX.p8
    appleApiKeyId: process.env.APPLE_API_KEY_ID!,
    appleApiIssuer: process.env.APPLE_API_ISSUER!,
  },
},
```

Source: [Forge macOS signing](https://www.electronforge.io/guides/code-signing/code-signing-macos). Guard `osxSign`/`osxNotarize` behind an env check so local unsigned `make` still works.

### electron-builder

```yaml
mac:
  hardenedRuntime: true
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  notarize: true
```

Certificate via `CSC_LINK` (base64 .p12) + `CSC_KEY_PASSWORD`; notarization reads `APPLE_API_KEY`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER`.

### CI keychain (Forge)

```yaml
- name: Prepare macOS signing
  if: runner.os == 'macOS'
  env:
    P12: ${{ secrets.APPLE_SIGNING_CERT_P12 }}
    P12_PASSWORD: ${{ secrets.APPLE_SIGNING_CERT_PASSWORD }}
    API_KEY_P8: ${{ secrets.APPLE_API_KEY_P8 }}
  run: |
    KEYCHAIN=$RUNNER_TEMP/build.keychain-db
    echo "$P12" | base64 --decode > $RUNNER_TEMP/cert.p12
    security create-keychain -p "" "$KEYCHAIN"
    security set-keychain-settings -lut 21600 "$KEYCHAIN"
    security unlock-keychain -p "" "$KEYCHAIN"
    security import $RUNNER_TEMP/cert.p12 -k "$KEYCHAIN" -P "$P12_PASSWORD" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: -k "" "$KEYCHAIN"
    security list-keychains -d user -s "$KEYCHAIN" $(security list-keychains -d user | tr -d '"')
    echo "$API_KEY_P8" > $RUNNER_TEMP/AuthKey.p8
    echo "APPLE_API_KEY=$RUNNER_TEMP/AuthKey.p8" >> $GITHUB_ENV
```

Verify locally or in CI:

```bash
codesign --verify --deep --strict --verbose=2 out/Atlas-darwin-arm64/Atlas.app
spctl --assess --type execute --verbose out/Atlas-darwin-arm64/Atlas.app
xcrun stapler validate out/make/Atlas.dmg
```

## Windows

Rules that changed the landscape:

- OV and EV certificate private keys must live on a **FIPS 140-2 Level 2 HSM or a cloud HSM**. Exportable `.pfx` files for new certificates are no longer issued, so "cert file in a secret" CI setups are legacy.
- **Azure Artifact Signing** (formerly Azure Trusted Signing) is the cheapest cloud option and is supported by both toolchains.
- **SmartScreen**: an EV certificate no longer bypasses SmartScreen reputation. New apps show warnings until reputation accrues from downloads; plan for it at launch.

### Forge + Azure Artifact Signing

Forge signs through `@electron/windows-sign` using `signtool` with the Azure dlib ([Forge Windows signing](https://www.electronforge.io/guides/code-signing/code-signing-windows)):

```ts
// windowsSign.ts
import type { WindowsSignOptions } from '@electron/packager';

export const windowsSign: WindowsSignOptions = {
  ...(process.env.SIGNTOOL_PATH ? { signToolPath: process.env.SIGNTOOL_PATH } : {}),
  signWithParams: `/v /dlib ${process.env.AZURE_CODE_SIGNING_DLIB} /dmdf ${process.env.AZURE_METADATA_JSON}`,
  timestampServer: 'http://timestamp.acs.microsoft.com',
  hashes: ['sha256'] as WindowsSignOptions['hashes'],
};
```

```ts
// forge.config.mts
import { windowsSign } from './windowsSign.js';

packagerConfig: { windowsSign },          // signs app binaries
makers: [new MakerSquirrel({ windowsSign })], // signs Setup.exe (types may need @ts-expect-error)
```

`AZURE_METADATA_JSON` points to a file with `Endpoint`, `CodeSigningAccountName`, `CertificateProfileName`. Authentication uses `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` (service principal). Paths must not contain spaces.

### electron-builder + Azure Artifact Signing

```yaml
win:
  azureSignOptions:
    publisherName: Acme Inc     # must match the certificate subject CN
    endpoint: https://weu.codesigning.azure.net
    codeSigningAccountName: acme-signing
    certificateProfileName: atlas-public
```

Same `AZURE_*` env vars. `win.azureSignOptions` is the stable key in the current electron-builder line. The Windows signing config is being reshaped (Azure moving under `win.sign` with a `type` field); when you upgrade electron-builder across a major, check its [releases](https://github.com/electron-userland/electron-builder/releases) and migrate the block (snapshot in `sources.md` → Version notes). Keep `publisherName` matching the certificate subject: electron-updater checks it when verifying downloaded Windows updates.

Other HSM vendors (DigiCert KeyLocker, SSL.com eSigner, etc.) work via a custom `signWithParams` (Forge) or a custom `win.sign` script (electron-builder).

Verify:

```powershell
Get-AuthenticodeSignature .\out\make\squirrel.windows\x64\AtlasSetup.exe
```

## Linux

- No OS-level signing requirement; AppImage, deb and rpm install unsigned.
- If you host an **apt/yum repository**, sign the repository metadata (and optionally rpm packages) with a GPG key and publish the public key.
- Publish SHA-256 checksums with each release for direct downloads.

## Secrets Checklist

| Secret | Used by |
|-|-|
| `APPLE_SIGNING_CERT_P12`, `APPLE_SIGNING_CERT_PASSWORD` | macOS Developer ID cert (or `CSC_LINK`/`CSC_KEY_PASSWORD` for electron-builder) |
| `APPLE_API_KEY_P8`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER` | Notarization via notarytool |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` | Azure Artifact Signing |

- Scope secrets to a protected `release` environment that only runs on tags.
- Rotate the API key and service principal secret on a schedule; never commit `.p8`, `.p12` or `.env` signing files.

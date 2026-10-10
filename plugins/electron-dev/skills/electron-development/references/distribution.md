# Distribution Targets

Pick targets per platform before writing packaging config: each target fixes the installer format, the update path, the signing identity and what the app may do at runtime. Packaging config lives in `build-config.md`, signing in `code-signing.md`, updater wiring in `auto-update.md`.

## Decision table

| Target | Choose when | Update path | Signing | Runtime limits |
|-|-|-|-|-|
| macOS DMG + ZIP (Developer ID) | Default for direct download | Built-in `autoUpdater` (Squirrel.Mac, needs the ZIP) or electron-updater | Developer ID Application, notarized | None beyond hardened runtime |
| Mac App Store (MAS) | Store discovery, managed licensing, enterprise via Apple Business Manager | Store only; in-app updater disabled | Apple Distribution + Mac Installer Distribution, provisioning profile | App Sandbox; `crashReporter`/`autoUpdater` unavailable |
| Windows Squirrel (Forge default) | Simple per-user installs, no admin rights | Built-in `autoUpdater` (Squirrel.Windows), update-electron-app | Authenticode (HSM-backed) | Per-user only |
| Windows NSIS (electron-builder) | Custom install dir, per-machine, installer UI | electron-updater | Authenticode | None |
| Windows MSI (WiX) | IT-managed deployment (Intune, GPO, SCCM) | Usually IT-pushed; in-app update optional | Authenticode | None |
| Windows MSIX (direct) | Clean install/uninstall, package identity APIs | Built-in `autoUpdater` MSIX path, or App Installer file | Trusted cert matching the manifest Publisher | Packaged-app virtualisation |
| Microsoft Store (MSIX) | Store discovery, Store-managed updates | Store only | Store re-signs | Same as MSIX |
| Linux AppImage | One-file download, any distro | electron-updater | Optional (checksums, GPG) | No desktop integration without help; SUID sandbox unavailable |
| Linux deb / rpm | Debian/Ubuntu and Fedora/RHEL users, apt/yum repos | Distro package manager / your repo | GPG-signed repo metadata | None |
| Flatpak (Flathub) | Broad distro reach, sandboxed install | Flatpak / Flathub | Flathub signs | Flatpak sandbox; portals for files |
| Snap (Snap Store) | Ubuntu-centric audience | snapd, automatic | Store signs | Strict confinement; interfaces (plugs) |

Rules of thumb:

- **Start with direct download** on all three platforms (DMG+ZIP, Squirrel or NSIS, AppImage + deb). Add stores when there is a concrete reason (discovery, enterprise procurement, sandbox requirement).
- **One update path per installed copy.** Store builds never run an in-app updater; direct builds never assume a store. Gate the updater at runtime (see below).
- **Each store build is its own CI job** with its own signing identity and config; do not try to re-sign a direct build into a store build.

```ts
// main/updater.ts: never self-update a store-managed copy
const storeManaged = process.mas || process.windowsStore || !!process.env.SNAP || !!process.env.FLATPAK_ID;
if (app.isPackaged && !storeManaged) startUpdater(); // see auto-update.md
```

`process.mas` is true in the MAS build of Electron; `process.windowsStore` is true when running as an AppX/MSIX package. Note that a sideloaded MSIX also sets `process.windowsStore`; if you ship direct MSIX with the built-in updater, pass a build-time flag instead.

## macOS

### Universal vs per-arch

| Option | Pros | Cons |
|-|-|-|
| Per-arch (`arm64`, `x64`) | Half the download size; simpler native-module builds | Two artifacts, two update feeds (or arch-aware feed), users can pick wrong one |
| Universal | One download that runs everywhere; simplest update story | Roughly double the size; every native binary must be merged |

- Forge: `electron-forge make --arch=universal` (uses `@electron/universal`). electron-builder: `mac.target: [{ target: dmg, arch: universal }]`.
- Native modules in a universal build must exist for both archs before merging. Binaries that are already universal or arch-specific by design go in `osxUniversal.x64ArchFiles` (Forge/packager) or `mac.x64ArchFiles` (electron-builder) so the merge step skips them.
- ASAR contents that differ between archs (e.g. a bundled native module) need the merge tool's ASAR handling (`mergeASARs`); keep JS identical across archs so the merge is trivial.
- Intel Macs are a shrinking share; check your telemetry before dropping `x64`, and keep it as long as the supported Electron major ships it.

### Mac App Store (MAS)

The MAS build is a separate Electron flavour (`platform: mas`) that avoids private APIs and runs under the App Sandbox ([MAS submission guide](https://www.electronjs.org/docs/latest/tutorial/mac-app-store-submission-guide)).

What you need:

- **Certificates**: *Apple Distribution* (signs the app), *Mac Installer Distribution* (signs the `.pkg` you upload), *Apple Development* for local sandbox testing. Developer ID is not used.
- **Provisioning profile**: a Mac App Store distribution profile for the bundle ID, embedded as `Contents/embedded.provisionprofile` (osx-sign does this via `provisioningProfile`). A development profile plus registered test Macs for local runs.
- **`ElectronTeamID`** in `Info.plist` (osx-sign derives it from the certificate; set it via `extendInfo` if that fails).
- **Two entitlement files**: parent and inherit.

```xml
<!-- build/entitlements.mas.plist (app bundle) -->
<dict>
  <key>com.apple.security.app-sandbox</key><true/>
  <key>com.apple.security.application-groups</key>
  <array><string>TEAMID.com.acme.atlas</string></array>
  <key>com.apple.security.network.client</key><true/>
  <key>com.apple.security.files.user-selected.read-write</key><true/>
  <key>com.apple.security.files.bookmarks.app-scope</key><true/>
</dict>
```

```xml
<!-- build/entitlements.mas.inherit.plist (helpers, frameworks, .node files) -->
<dict>
  <key>com.apple.security.app-sandbox</key><true/>
  <key>com.apple.security.inherit</key><true/>
</dict>
```

Add only the entitlements the app uses (camera, microphone, `network.server`, printing); App Review rejects unexplained ones.

Forge (package and make with `--platform=mas`; the packager reads `osxSign` as usual):

```ts
// forge.config.mts (excerpt): MAS job only
const isMas = process.env.ATLAS_TARGET === 'mas';

packagerConfig: {
  appBundleId: 'com.acme.atlas',
  ...(isMas && {
    osxSign: {
      identity: 'Apple Distribution: Acme Inc (TEAMID)',
      provisioningProfile: 'build/Atlas_AppStore.provisionprofile',
      optionsForFile: (file) => ({
        entitlements: file.endsWith('Atlas.app')
          ? 'build/entitlements.mas.plist'
          : 'build/entitlements.mas.inherit.plist',
      }),
    },
  }),
},
makers: [
  // @electron-forge/maker-pkg; identity = the Mac Installer Distribution cert
  new MakerPKG({ identity: '3rd Party Mac Developer Installer: Acme Inc (TEAMID)' }, ['mas']),
],
```

```bash
ATLAS_TARGET=mas npx electron-forge make --platform=mas --arch=universal
```

The installer identity's display name depends on when the certificate was created (*Mac Installer Distribution* certificates may still be named "3rd Party Mac Developer Installer" in the keychain); copy the exact name from `security find-identity -v`.

electron-builder: targets `mas` (the `.pkg` for upload) and `mas-dev` (development-signed, for local sandbox runs), configured under `mas` / `masDev` with `entitlements`, `entitlementsInherit` and `provisioningProfile` ([electron.build MAS](https://www.electron.build/docs/mas/)). Newer electron-builder majors move these keys into a `sign` object; `electron-builder migrate-schema` rewrites old configs.

Upload the `.pkg` with Apple's Transporter app (or Apple's current command-line upload tool). No notarization step: notarytool is for Developer ID builds; App Review covers MAS.

What breaks or changes under MAS:

| Area | Under MAS |
|-|-|
| Auto-update | `autoUpdater` is not available; the Store updates the app. Remove update UI. |
| Crash reporting | `crashReporter` is not available; use App Store Connect crash logs or an in-process reporter that uploads over HTTPS |
| Native modules | Must ship inside the bundle, signed with the inherit entitlements; no downloading or compiling code at runtime |
| Child processes | Inherit the sandbox; executables outside the bundle cannot be spawned |
| File access | Only files the user picked (dialogs, drag-and-drop) plus the app container; persist access with security-scoped bookmarks |
| Login items, helpers | Need their own signed helper app and entitlements |
| Fuses, ASAR integrity | Still apply; set before signing like any build |

Security-scoped bookmarks keep access to a user-picked file across launches:

```ts
// main: ask for a bookmark with the selection (MAS only)
const { filePaths, bookmarks } = await dialog.showOpenDialog(win, {
  properties: ['openFile'],
  securityScopedBookmarks: true,
});
store.set('lastProject', { path: filePaths[0], bookmark: bookmarks?.[0] }); // base64 bookmark

// later launch: re-open the scope before touching the file, close it after
const { path, bookmark } = store.get('lastProject');
const stopAccess = app.startAccessingSecurityScopedResource(bookmark);
try { await readProject(path); } finally { stopAccess(); }
```

Test the MAS build locally with an Apple Development identity and development profile before submitting; sandbox violations show up in Console.app as `Sandbox: deny` lines.

## Windows

### Installer formats

| Format | Install scope | Admin needed | Update | Notes |
|-|-|-|-|-|
| Squirrel.Windows (Forge `MakerSquirrel`) | Per-user (`%LocalAppData%`) | No | Built-in `autoUpdater` | Handle `--squirrel-*` events (`auto-update.md`); IT dislikes per-user installs |
| NSIS (electron-builder) | Per-user or per-machine (`perMachine`, `oneClick: false`) | Only for per-machine | electron-updater | Most flexible installer UI |
| MSI (Forge `MakerWix`, electron-builder `msi`) | Per-machine capable | Yes for per-machine | IT-pushed | What enterprise deployment tools expect |
| MSIX (Forge `MakerMSIX`, electron-builder `appx`) | Per-user, OS-managed | No | Built-in `autoUpdater` MSIX path, App Installer, or Store | Clean uninstall, package identity |

- **Per-machine installs** cannot self-update without elevation. Either accept a UAC prompt on update, or leave updates to IT and disable the in-app updater for that build.
- Ship one Windows format per channel. Installing both Squirrel and MSIX copies gives users two apps with separate data folders.

### MSIX and the Microsoft Store

- **Package identity**: `Name` and `Publisher` in the manifest. The `Publisher` must equal the signing certificate's subject. For the Store, Partner Center reserves the name and assigns the Publisher string; copy both into the maker config.
- **Store submission**: upload the MSIX; the Store re-signs it and delivers updates. Do not run any in-app updater.
- **Direct (sideloaded) MSIX**: must be signed with a certificate the machine trusts, and updates come from the built-in `autoUpdater` (current Electron detects MSIX and uses its MSIX updater) or an `.appinstaller` file. See `code-signing.md`.
- **Packaged-app behaviour**: writes to `AppData` and `HKCU` are virtualised per package and removed on uninstall; the install directory is read-only. Never write next to the executable.
- **Login items** under MSIX use a `StartupTask` manifest extension, not the registry; test `app.setLoginItemSettings` on the packaged build.
- The Store also accepts unpackaged Win32 installers (MSI/EXE). Then the Store only links to your installer and the app keeps its own updater.
- Forge `MakerMSIX` builds only on Windows with the Windows SDK installed and may still be marked experimental ([Forge MSIX maker](https://www.electronforge.io/config/makers/msix)).

```ts
// forge.config.mts (excerpt)
new MakerMSIX({
  manifestVariables: { publisher: 'CN=Acme Inc, O=Acme Inc, C=US' }, // must match cert subject
  windowsSignOptions: windowsSign, // see code-signing.md
}),
```

### Windows on ARM

- Electron ships `win32-arm64` builds. Build with `--arch=arm64` (Forge) or `--arm64` (electron-builder); x64 builds run under emulation but slower and with higher battery use.
- Every native module needs an arm64 binary. Prefer Node-API modules with arm64 prebuilds; otherwise build on an arm64 runner (cross-compiling native modules from x64 is fragile).
- Squirrel and NSIS need one installer per arch (or an NSIS multi-arch installer); MSIX can bundle archs. Make sure the update feed serves the right arch.

## Linux

| Format | Sandboxing | Updates | Desktop integration | Watch out for |
|-|-|-|-|-|
| AppImage | None beyond Chromium's | electron-updater | Manual (AppImageLauncher or first-run `.desktop` install) | Needs FUSE on the host; SUID sandbox cannot work (mounted `nosuid`) |
| deb / rpm | None beyond Chromium's | apt/dnf from your signed repo | Installed `.desktop`, icons, MIME types | One package per distro family; maintain a repo |
| Flatpak | Flatpak sandbox, portals for files and notifications | Flathub / `flatpak update` | Exported `.desktop` and icons | Uses the Electron BaseApp and zypak to run Chromium's sandbox inside Flatpak; file access via portals |
| Snap | Strict confinement, interfaces | snapd, automatic | Generated `.desktop` | Request interfaces (`home`, `network`, `audio-playback`); classic confinement needs Store approval |

Chromium sandbox on Linux:

- Chromium's sandbox uses unprivileged user namespaces, falling back to the SUID helper `chrome-sandbox`, which must be owned by root with mode `4755`. deb/rpm makers set this in their post-install step; verify with `ls -l /opt/Atlas/chrome-sandbox`.
- Some distros restrict unprivileged user namespaces (Ubuntu does this through AppArmor). The symptom is a startup crash mentioning the SUID sandbox helper. Fix it by shipping an AppArmor profile that allows `userns` for the app binary (deb) or relying on the store sandbox (Snap, Flatpak); **never** ship `--no-sandbox` as the fix.

`.desktop` file (deb/rpm makers generate one from config; for AppImage the integration tool installs it):

```ini
# /usr/share/applications/com.acme.atlas.desktop
[Desktop Entry]
Type=Application
Name=Atlas
Comment=Plan and track Atlas projects
Exec=/opt/Atlas/atlas %U
Icon=com.acme.atlas
Terminal=false
Categories=Office;ProjectManagement;
MimeType=x-scheme-handler/atlas;application/x-atlas-project;
StartupWMClass=Atlas
```

- `StartupWMClass` must match the window class (usually the app `name`), or docks show a second, generic icon.
- `MimeType=x-scheme-handler/atlas` registers the `atlas://` protocol (see `native-integration.md`).
- Use the reverse-DNS app ID (`com.acme.atlas`) for the `.desktop` name, icons and Flatpak ID so they line up.

## Update path per target

| Target | Updater | Details |
|-|-|-|
| macOS DMG/ZIP | `autoUpdater` (Squirrel.Mac) or electron-updater | `auto-update.md` |
| MAS | App Store | Disable in-app updater (`process.mas`) |
| Squirrel.Windows | `autoUpdater` / update-electron-app | `auto-update.md` |
| NSIS | electron-updater | `auto-update.md` |
| MSI | IT deployment | Disable or make opt-in |
| MSIX direct | `autoUpdater` MSIX path or App Installer | Check the autoUpdater API page for the installed major |
| Microsoft Store | Store | Disable in-app updater |
| AppImage | electron-updater | `auto-update.md` |
| deb / rpm | Package manager + your repo | No in-app updater; optionally notify only |
| Flatpak / Snap | Flatpak / snapd | Disable in-app updater |

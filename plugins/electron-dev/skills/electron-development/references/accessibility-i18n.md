# Accessibility and Internationalization

The renderer is a web page: web accessibility and i18n practice apply unchanged. What Electron adds is the native layer (menus, dialogs, notifications, tray, title bar), which main builds, and OS settings that main can read and the renderer may not see.

## Accessibility in the Renderer

- **Semantic HTML first.** `<button>`, `<a href>`, `<nav>`, `<main>`, `<dialog>`, `<label for>`, headings in order. ARIA only fills gaps native elements leave (`aria-live` for sync status, `aria-expanded` on disclosure buttons); a `div` with `role="button"` needs focus and key handling you would otherwise get for free.
- **Every feature works from the keyboard.** Tab order follows reading order, no positive `tabindex`, roving tabindex inside lists, toolbars and trees, Escape closes popups. Drag-and-drop and hover-only actions need a keyboard alternative (a menu item or context menu entry).
- **Visible focus.** Style `:focus-visible`; never `outline: none` without a replacement. Focus rings must meet contrast in light, dark and high-contrast themes.
- **Manage focus on view changes.** Opening a dialog moves focus into it and traps it (`<dialog>.showModal()` does both); closing returns focus to the trigger. After route changes, move focus to the new view's heading and announce it.
- **Custom title bars** (native-integration.md): drag regions are not reachable by keyboard, so nothing important may live only there. Prefer native window controls (`titleBarStyle: 'hidden'` with overlay) over self-drawn ones.
- **Zoom and text size.** Keep the `resetZoom`/`zoomIn`/`zoomOut` menu roles, size text in `rem`, and test at 200% zoom.

## Native Menus and Shortcuts

- Every command reachable in the UI is also in the application menu, with an accelerator where it is frequent. Menus are the platform's accessible command surface: screen readers read them and macOS lets users search them (Help menu).
- Context menu entries mirror actions available elsewhere; a context menu must not be the only way to reach something, because it needs a pointer or the Menu key.
- Don't bind accelerators that assistive technology reserves: VoiceOver (Ctrl+Option), NVDA/JAWS (Insert or CapsLock combinations), Orca (Insert/CapsLock), and the OS's own shortcuts.
- Native controls are accessible out of the box; a notification, tray tooltip or overlay icon description is what a screen reader announces, so write it as text, not only as an icon.

## Respect OS Settings

Chromium exposes most OS preferences as CSS media features; the renderer uses those directly.

```css
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
@media (prefers-contrast: more) { :root { --border: CanvasText; } }
@media (forced-colors: active) { .icon { forced-color-adjust: auto; } .chip { border: 1px solid CanvasText; } }
```

Main reads the same settings from `nativeTheme` for native pieces and for anything CSS cannot see:

| Property | Meaning | Platforms |
|-|-|-|
| `shouldUseHighContrastColors` | High contrast requested | macOS, Windows |
| `inForcedColorsMode` | Windows high contrast forces colors | Windows |
| `prefersReducedTransparency` | Reduce transparency is on | Where the OS reports it |
| `shouldUseDarkColors` | Effective dark mode | All |

```typescript
// src/main/a11y.ts (after 'ready')
import { BrowserWindow, nativeTheme } from 'electron';

export function applyOsPreferences(win: BrowserWindow): void {
  const update = () => {
    if (process.platform === 'darwin') win.setVibrancy(nativeTheme.prefersReducedTransparency ? null : 'sidebar');
  };
  nativeTheme.on('updated', update);
  update();
}
```

Forward a value to the renderer only when no media feature covers it, as a contract event (`theme:changed` already carries `highContrast`; add e.g. `reducedTransparency` the same way); never poll from the renderer.

### Accessibility support flag

Chromium builds the accessibility tree automatically when it detects assistive technology. `app.setAccessibilitySupportEnabled(true)` (macOS, Windows, after `ready`) forces it on, which costs noticeable performance. Use it only behind a user setting for assistive tools that are not detected, and never enable it unconditionally. `app.on('accessibility-support-changed', ...)` tells you when it flips.

## Testing Accessibility

- **Automated:** run axe against the real app in the Playwright E2E suite (testing.md). axe catches missing labels, contrast and ARIA misuse, roughly a third of real issues.

```typescript
// tests/e2e/a11y.spec.ts
import AxeBuilder from '@axe-core/playwright';

test('main window has no serious axe violations', async () => {
  const page = await app.firstWindow();
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')).toEqual([]);
});
```

- **Keyboard E2E:** one test per core flow driven only by `page.keyboard` (Tab, Enter, Escape, arrows), asserting `document.activeElement` at each step.
- **Screen readers, manually, before release:** VoiceOver on macOS (Cmd+F5), NVDA (free) and Narrator on Windows, Orca on Linux (GNOME). Check the menu bar, a full core flow, dialogs, live status announcements and the tray.
- **OS settings:** toggle high contrast / forced colors, reduce motion, reduce transparency, dark mode and 200% text scaling, and look at every main screen.

## Locale: Decide in Main, Tell the Renderer

Main decides the UI language once, because main also needs it for menus, dialogs, notifications and the tray.

| API | Returns | Use for |
|-|-|-|
| `app.getPreferredSystemLanguages()` | User's ordered language list (country codes may be missing on Windows) | Choosing the UI language |
| `app.getLocale()` | Chromium's locale for this run | Fallback; reflects a `--lang` switch |
| `app.getSystemLocale()` | OS regional locale | Date/number formatting when it differs from the UI language |

All three need `ready`.

```typescript
// src/shared/locales.ts (pure data, safe to share)
export const UI_LOCALES = ['en', 'de', 'fr', 'ar', 'he'] as const;
export type UiLocale = (typeof UI_LOCALES)[number];
export const RTL_LOCALES: readonly UiLocale[] = ['ar', 'he'];
```

```typescript
// src/main/locale.ts
import { app } from 'electron';
import { RTL_LOCALES, UI_LOCALES, type UiLocale } from '../shared/locales';

const isUi = (tag: string): tag is UiLocale => (UI_LOCALES as readonly string[]).includes(tag);

export function resolveUiLocale(saved?: string): UiLocale {
  for (const tag of [saved, ...app.getPreferredSystemLanguages(), app.getLocale()]) {
    if (!tag) continue;
    try {
      const { language } = new Intl.Locale(tag); // 'de-AT' → 'de'; add exact matches first if you ship 'pt-BR' etc.
      if (isUi(language)) return language;
    } catch { /* malformed tag: skip */ }
  }
  return 'en';
}

export const directionOf = (locale: UiLocale) => (RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr');
```

The contract (typed-ipc.md) carries `LocaleInfo` (`locale`, `dir`, `formatLocale`) through `i18n:get` (`window.api.getLocale`) and the `i18n:changed` event (`window.api.onLocaleChanged`); main answers `i18n:get` with `currentLocaleInfo()`, built from `resolveUiLocale` and `directionOf`.

When the user picks a language in settings (`settings:set` with key `language`; the contract types the value as `UiLocale`), `applySetting` persists it and calls `applyLocale`, which rebuilds the application menu and tray menu with the new strings, and emits `i18n:changed` to every window. No restart needed.

## Translations

- Keep messages as JSON per locale (`src/locales/de.json`), keyed by stable ids (`menu.file.open`), with ICU MessageFormat or your i18n library's plural syntax. Never build sentences by concatenation; word order and plurals differ.
- **Main** imports all locale files statically (they are small) and exposes `t(key, params)`. Every native label goes through it: menu items, dialog titles and buttons, notification text, tray tooltip, jump-list tasks, the spellchecker menu.
- **Renderer** lazy-loads only its locale: ``await import(`../locales/${locale}.json`)`` lets Vite split one chunk per language. Translation files come from the bundle, never from the network or a renderer-chosen path.
- Role-based menu items (`{ role: 'copy' }`) bring default labels; set `label` explicitly when they don't match your UI language. On macOS, system-provided items (Services, dictation, emoji) follow the app's declared localizations (below).
- Native file dialogs and message box chrome follow the OS language; the strings you pass (title, message, button labels) are yours to translate.

```typescript
// src/renderer/i18n.ts
let messages: Record<string, string> = {};
const apply = async ({ locale, dir }: { locale: string; dir: 'ltr' | 'rtl' }) => {
  document.documentElement.lang = locale;
  document.documentElement.dir = dir;
  messages = (await import(`../locales/${locale}.json`)).default;
  rerender();
};
await apply(await window.api.getLocale());
const offLocale = window.api.onLocaleChanged(apply);
```

## Right-to-Left Layouts

- Set `dir` on `<html>`; use CSS logical properties (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `text-align: start`) so layouts mirror without a second stylesheet.
- Mirror directional icons (back/forward arrows, chevrons, progress) with `[dir='rtl'] .icon-directional { transform: scaleX(-1); }`; don't mirror logos, media controls or checkmarks.
- Mixed-direction text (file names, user content) goes in `<bdi>` or `dir="auto"`.
- The title bar overlay moves the native controls to the other side in RTL; the `env(titlebar-area-*)` variables handle it (native-integration.md).

## Dates, Numbers and Sorting

Use `Intl`, not hand-written formats. Format with the user's regional locale, which can differ from the UI language (English UI, German date format); main sends it as `formatLocale` from `app.getSystemLocale()`.

```typescript
const date = new Intl.DateTimeFormat(formatLocale, { dateStyle: 'medium', timeStyle: 'short' });
const size = new Intl.NumberFormat(formatLocale, { style: 'unit', unit: 'megabyte', maximumFractionDigits: 1 });
const ago = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
const byName = new Intl.Collator(locale, { sensitivity: 'base', numeric: true }).compare; // 'file2' < 'file10'
```

## Spellchecker Languages

On Windows and Linux, main sets the spellchecker languages from the UI and user preference; on macOS the OS spellchecker detects the language and `setSpellCheckerLanguages` does nothing.

```typescript
// src/main/spellcheck.ts
import { session } from 'electron';

export function setSpellcheckLanguages(wanted: string[]): void {
  if (process.platform === 'darwin') return;
  const available = new Set(session.defaultSession.availableSpellCheckerLanguages);
  session.defaultSession.setSpellCheckerLanguages(wanted.filter((l) => available.has(l))); // unknown codes throw
}
```

Dictionaries download from a Google CDN by default; to keep traffic in-house, host them and call `session.setSpellCheckerDictionaryDownloadURL`. The context menu with suggestions is in native-integration.md.

## macOS Localization Metadata

- macOS decides which language to use for system-provided UI (Services menu, permission prompts, standard dialogs) from the localizations the bundle declares: `CFBundleLocalizations` in Info.plist (Forge `packagerConfig.extendInfo`, electron-builder `mac.extendInfo`) or `<lang>.lproj` folders in `Contents/Resources`.
- Usage descriptions (`NSCameraUsageDescription`, `NSMicrophoneUsageDescription`) are localized through `InfoPlist.strings` in each `.lproj`.
- If the packager strips Chromium locale files to save size (an `electronLanguages`-style option), keep every locale you ship, or built-in Chromium strings fall back to English.

## Checklist

- [ ] Every feature reachable by keyboard, with visible focus; dialogs move and restore focus
- [ ] Every command in the application menu; accelerators avoid assistive-technology keys
- [ ] Reduced motion, contrast, forced colors and dark mode respected in CSS; native pieces follow `nativeTheme`
- [ ] axe check and keyboard-only flow in E2E; manual screen-reader pass per release
- [ ] UI locale decided in main, sent via the contract; menus, dialogs, notifications and tray translated in main
- [ ] `lang` and `dir` set on `<html>`; logical CSS properties; `Intl` for dates, numbers and sorting
- [ ] Spellchecker languages set on Windows/Linux; macOS bundle declares its localizations

# Frontend: Vue 3 + Vite + TypeScript

## Baseline: create-vue

The frontend tooling is whatever **create-vue** currently generates with TypeScript, Router, Pinia, Vitest, Playwright and ESLint (Oxlint is included with ESLint). That keeps tsconfig layout, lint config and test config aligned with the Vue team's current recommendations without this skill pinning anything.

- Keep create-vue's generated ESLint config as a base file and add project rules in a thin wrapper that imports it, so the base can be regenerated.
- Keep its tsconfig split (app, node, vitest) and its Vitest config.
- The project owns: `vite.config.ts` (Django integration), `src/`, the Playwright config and tests.

## Django integration (django-vite)

- **Django serves every page.** There is no `index.html`; templates load entries with `{% vite_hmr_client %}` and `{% vite_asset "<entry>.ts" %}`.
- `vite.config.ts`: `root` = `src`, `base` = the static URL prefix (e.g. `/static/vue/`), `build.outDir` = Django's static dir, `build.manifest = true`, one input per entry point. `manifest_path` in `DJANGO_VITE` must match where Vite writes the manifest (by default `.vite/manifest.json` inside `outDir`).
- **Development:** Vite serves modules and HMR on its own port; `server.origin` makes asset URLs absolute, and `server.cors` allows exactly the origin the pages come from (the local proxy). Do not use `cors: true`.
- **Production:** the Node build stage of the Django image runs `vite build`; `collectstatic` picks the output up; WhiteNoise serves it with hashed names.
- Vite's build option names move between majors (for example the bundler options); keep the config minimal and check the current backend-integration and migration docs when upgrading.

## Two entry points

| Entry | Pattern | Used for |
|---|---|---|
| `main.ts` | Styles for Django-rendered pages (home, allauth's login and account pages) plus islands: small Vue apps mounted into elements of those pages; `data-*` attributes become props | Widgets in server-rendered pages |
| `app-main.ts` | One SPA with Vue Router, history base `/app/`; Django routes `/app/*` to the shell template | The authenticated application |

Each island is its own app (own Pinia). Shared state across islands is the server session, not localStorage.

## HTTP client

- **One module (`src/api/client.ts`) talks HTTP**, a thin wrapper around `fetch`: same-origin credentials, `X-CSRFToken` from the `csrftoken` cookie on unsafe methods, JSON in and out, a typed error with the server's `detail`. Lint forbids `fetch` elsewhere.
- No axios by default: native `fetch` covers the need without a dependency (axios had a compromised release in 2026; fewer dependencies, smaller supply-chain surface).
- When the backend publishes OpenAPI, a generated typed client (e.g. hey-api) can replace hand-written methods; regenerate it in CI and fail on a diff.

## State and auth in the browser

- The server session is the source of truth. A Pinia store mirrors the current user (`GET /api/v1/auth/me/`); the router guard loads it and sends anonymous users to the login page (`/accounts/login/?next=…`) with a hard navigation. Vue never handles passwords; for login screens inside the SPA use allauth's headless API in cookie mode.
- Never store tokens or user secrets in localStorage. Persist only UI conveniences (a collapsed panel, a filter).
- Streams: `new EventSource('/v1/events')` on the same origin; the session cookie authenticates and EventSource reconnects by itself. Parse payloads defensively.

## Components and styling

- `<script setup lang="ts">` for all new components; no Options API in new code.
- Tailwind utilities with design tokens per `uiux-design-tailwindv4` and `uiux-design-system`; Vue patterns per the `uiux-design-vue3-*` skills.
- Accessible markup first (labels, roles); Playwright selects by role and label, `data-testid` only where no accessible name exists.

## Internationalisation

Where an app needs more than one language (for example English plus a local language): vue-i18n for the frontend with message files per locale, Django's i18n for server-rendered pages and emails, the active language from the user's setting or the browser, stored in the session. Add it when the second language is real, not in advance.

## Runtime configuration

Values that differ per environment reach the frontend through JSON that Django renders into each page, read by one config module; never through `import.meta.env`, which is compiled into a bundle that must be identical in staging and production (`environments.md`).

## Pitfalls

- `typescript@latest` can be ahead of the Vue tooling (vue-tsc, typescript-eslint): use the TypeScript line create-vue generates.
- Recent pnpm versions block dependency build scripts until approved (`pnpm approve-builds`); Corepack is removed from Node 25 on and should not be relied on; install the exact pnpm explicitly.
- The Playwright Docker image tag must equal the installed `@playwright/test` version: pin `@playwright/test` exactly.
- A Pinia persistence plugin is not needed for auth; if you persist UI state, check the plugin's maintenance status first.

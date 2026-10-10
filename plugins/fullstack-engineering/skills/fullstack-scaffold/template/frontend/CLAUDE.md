# CLAUDE.md — __PROJECT_TITLE__ frontend (`frontend/`)

Vue 3 + TypeScript + Vite + Tailwind + Pinia, generated with create-vue. Built into `backend/static/vue/` and served by Django through django-vite. Two entry points: `main.ts` mounts islands into Django pages, `app-main.ts` is the SPA under `/app/`. Login, signup and account pages are Django (allauth) templates styled by the `.auth` rules in `src/styles.css`; Vue never handles passwords.

TypeScript, ESLint (`eslint.config.base.ts`) and Vitest configs are create-vue's; `vite.config.ts` and `eslint.config.ts` hold the project's additions.

## Commands

```bash
task check:frontend      # type-check, eslint, vitest
task test:e2e            # Playwright against the built app
```

## Key Constraints

- Components use `<script setup lang="ts">`; no Options API in new code.
- HTTP only through `src/api/client.ts`, a thin `fetch` wrapper (eslint enforces it; no axios). Auth is the session cookie; never store tokens in localStorage.
- Styling with Tailwind utilities; design tokens per the `uiux-design-*` skills.
- The browser always loads pages from the proxy on :8000 (Django); Vite (:3000) only serves assets and HMR.
- Server-to-client streams use `EventSource` on `/v1/events` (same origin, session cookie).
- Environment-specific values (environment name, feature flags, public keys) come from `src/config.ts`, which reads what Django renders into the page. Never from `import.meta.env`: Vite compiles those into the bundle, and the same bundle runs in staging and production.
- Check UI changes in a real browser: the Playwright MCP server in `.mcp.json` (version pinned) lets an agent open http://localhost:8000 and look.

## Docs

`docs/architecture.md`, `docs/environments.md`.

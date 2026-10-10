# Testing

## Layers

| Layer | Tooling | Runs in CI | What it proves |
|---|---|---|---|
| Lint and format | pre-commit (Ruff, hygiene, secrets guards), Oxlint + ESLint, vue-tsc | yes | Style, types, no plaintext secrets |
| Backend unit/integration | pytest, pytest-django, pytest-asyncio, against real PostgreSQL and Redis in the dev containers | yes | Models, views, permissions, internal API, Celery tasks (eager), realtime auth |
| Migration check | `makemigrations --check --dry-run` | yes | No model change without a migration |
| Frontend unit | Vitest (jsdom) | yes | Pure logic, composables, components where it pays off |
| End-to-end | Playwright in its official image, against built assets behind the proxy | yes | The real user path through production routing |
| Evals | per `agentic-engineering` | for agent behaviour | Agent quality, not code correctness |

## Rules

- **Real services, not mocks, for the database and Redis.** Mock only external providers (model APIs, the identity provider, third-party HTTP) and the other service's internal API in unit tests.
- **Test security behaviour explicitly:** CSRF refused without token, session invalid after logout, no login endpoint besides allauth, the login rules of the app's audience (`identity.md`, last section), cross-site refusal and fail-closed in the realtime service, SSO handshake not on GET, SSO routes absent when not configured. For external users: another user's object returns 404.
- **Login in tests goes through the real login page** (POST to allauth's login view), not `force_login`, wherever the login rules themselves are under test. Clear the cache between tests (rate limits).
- **Celery:** eager mode in tests; assert that tasks are enqueued on commit (`django_capture_on_commit_callbacks`).
- **SSE/WebSocket endpoints:** test auth decisions with requests that end before streaming; test formatting functions directly; cover the live stream in the end-to-end test.
- **End-to-end through the proxy:** the browser opens the proxy origin, exactly like production. A seeded end-to-end user with a verified email (management command that refuses to run with production settings) logs in through the login page.
- **Production settings are tested on staging,** not in CI: after each staging deploy, check health, readiness, login and one live stream through the proxy (`environments.md`).
- **Deterministic:** no sleeps; Playwright's auto-waiting assertions; retries only in CI.
- **Settings for tests are forced** (`--ds=...`), independent of the container env.

## End-to-end pitfalls seen in practice

- Fetch Metadata headers are sent only to trustworthy origins; on `http://<service-name>` in CI they are missing. Server-side checks must not require them.
- The Playwright image version must match `@playwright/test` exactly; run it with `ipc: host` and `init`.
- A service without a healthcheck counts as ready for `up --wait` while it still migrates; the browser's own reconnect (EventSource) or a readiness wait covers it.
- Containers that write reports into the repo must hand them back to the host user.

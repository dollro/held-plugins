---
name: fullstack-engineering
description: "Guideline for web apps on a reference stack: Django as system of record, FastAPI for realtime and agent work, Vue 3 + Vite + TypeScript, PostgreSQL, Redis, Celery, Docker with Task, SOPS secrets, platform-neutral CI. Covers service contracts, login (company SSO over OIDC, external accounts with MFA), environments, async work, deployment, observability and testing. Use when designing, building, reviewing or debugging a web app, API, frontend, Docker, CI or deploy. New repos: /fullstack-scaffold."
---

# Fullstack Engineering

How to build web apps: a few boring, proven building blocks with clear owners, glued together by explicit contracts. New code follows this guideline by default; existing code on another stack is respected (see *Repos on another stack*).

This file holds the **principles and guardrails**. They change slowly. The `references/` hold patterns and known pitfalls per area. Frameworks move fast, so **the official docs win over anything written here**.

## Before writing framework code

1. **Check what is installed.** Read the versions in `uv.lock` and `frontend/pnpm-lock.yaml`. Never assume a version from memory.
2. **Verify every API you are about to use** against the current docs, changelog or migration guide (`references/sources.md`). Use a docs MCP server such as **context7** when available, otherwise fetch the official docs from the web, otherwise read the installed package source. Snippets in this skill show patterns, not guaranteed signatures. Where the docs and the skill disagree, follow the docs and say so in your result.
3. **Read the reference for the part you touch** (table below). Do not read all of them upfront.
4. **Repo rules apply on top:** pull request size, file and function limits, CLAUDE.md and `docs/` come from `engineering-standards`; agent code from `agentic-engineering`.

| Read | When you build or review |
|-|-|
| `references/architecture.md` | Services, contracts, choosing the app shape, FastAPI-only and Channels options |
| `references/backend-django.md` | Settings, auth, DRF, internal endpoints, Celery, migrations, admin |
| `references/realtime-fastapi.md` | Async rules, SSE vs WebSocket, auth bridge, Redis fan-out, Alembic ownership |
| `references/frontend-vue.md` | create-vue baseline, django-vite, islands and SPA, HTTP client, state |
| `references/repo-conventions.md` | What CLAUDE.md must say on this stack; updating an existing CLAUDE.md |
| `references/local-dev-and-tooling.md` | Task conventions, docs site (MkDocs), Docker Compose, local proxy, uv, pnpm, container file ownership |
| `assets/traefik-host/` | Shared Traefik per server: compose, static and dynamic config, setup and operation |
| `references/environments.md` | local/CI/staging/production, build once and promote, how values reach Docker, Django, FastAPI and Vue |
| `references/secrets-and-config.md` | Env vars, SOPS + age, example files, rotation |
| `references/ci-cd-and-deploy.md` | Pipeline contract, GitHub/GitLab wrappers, release, deploy, hardening, backups, observability |
| `references/identity.md` | Login audience (internal/external/mixed), company SSO over OpenID Connect (Entra ID as worked example), external accounts and MFA, data separation, personal data |
| `references/security.md` | Auth flows, CSRF, cross-site checks, API keys, review checklist |
| `references/testing.md` | Test layers, real services, end-to-end through the proxy |
| `references/sources.md` | Official docs, changelogs, migration guides |

## Repos on another stack

Detect the stack from the lockfiles and manifests first. If the repo is not on this stack (another framework, language or deploy model):

- **Do not migrate it** or rewrite working code towards this stack unasked.
- **Still apply the mandatory rules** (*How binding this is*); they are stack-independent.
- **Make sure CLAUDE.md documents how to start, stop and test this repo** with its own commands (`references/repo-conventions.md`), even when nothing else is changed.
- **Flag deviations sparingly:** once per task, in your hand-back, name the one or two deviations that matter most (risk, not taste), with the matching section of this skill. Never repeat the same flag in every reply.

## How binding this is

**Mandatory** in every web app, whatever the stack (deviations need a reason in the repo's architecture doc):

1. Browser auth by session cookie + CSRF; no tokens in browser storage or URLs.
2. One login path per app, with the login audience decided and recorded.
3. Authorization in code, querysets scoped to the user; external users never reach other users' data.
4. Internal service endpoints behind a secret, failing closed.
5. One owner per table; migrations committed, backward compatible for one release, run as a deploy step.
6. Secrets never in plaintext in git or images.
7. Install only from lockfiles; CI actions pinned by SHA.
8. CI runs the same commands developers run.
9. Production runs an explicitly pinned, immutable image built once (the one staging ran, where staging exists); environment differences come only from runtime configuration; rollback is a revert.
10. Hardened production containers; backups off the host.
11. Tests against real database and cache, including the security behaviour above.
12. Framework APIs checked against current docs, never written from memory.

**Recommended defaults** are everything else: the concrete stack (Django + FastAPI, Vue, Celery, Task, SOPS, Caddy), the app shapes, the project layout and the scaffold's code. Follow them for new apps unless there is a reason not to; a different choice that keeps the mandatory rules is fine.

## 1. Architecture: owners and contracts

| Concern | Owner | Never |
|-|-|-|
| Users, permissions, admin, CRUD, REST API, server-rendered pages | **Django** (system of record) | Re-implement auth or admin in another service |
| Long-lived connections, streaming, agent runs | **FastAPI** realtime service | Hold domain state that Django owns |
| Background and scheduled work | **Celery** workers (Django code) | Long work inside a request |
| Data | **PostgreSQL**; each table has exactly one owning service and one migration system | Two services writing the same table |
| Cache, broker, pub/sub | **Redis**, only features both cache and broker use need | Redis as the system of record |
| Browser UI | **Vue** islands in Django pages + an SPA under `/app/` | A second origin for the browser |

Services talk through **contracts**, so an implementation can be replaced without touching the others: HTTP API under `/api/v1/` (OpenAPI-describable, JSON errors with `detail`), browser auth by session cookie + CSRF on one origin, service auth by shared secret on internal endpoints, data ownership per table, operations through env config, health endpoints and a separate migrate step. Details: `references/architecture.md`.

**Why:** owners and contracts keep the system debuggable and let one part change (or be swapped) without a rewrite.

## 2. Choose the shape on purpose

| Shape | Use when |
|-|-|
| **Django only** (default) | Most internal tools. Simple notifications via polling or Server-Sent Events from Django. |
| **Django + FastAPI** (reference) | Realtime, streaming or agent workloads (LLM token streams, long agent runs, many connections, non-browser clients). |
| **FastAPI only** (option) | Agent- or streaming-heavy app with few tables, no business admin, identity fully in the company identity provider, coarse roles. Exit path: move to Django + FastAPI when CRUD, admin or permissions grow. |
| **Django Channels** (option) | Small, model-bound live updates without agent or streaming work. |

Record the chosen shape and every deliberate deviation in the repo's `docs/architecture.md`, with the reason.

## 3. Auth and security

- **Browser → Django: session cookie + CSRF**, HttpOnly, SameSite, Secure in production. Never put session or access tokens in localStorage.
- **Decide the login audience first:** *internal* (staff via single sign-on with the company identity provider over OpenID Connect, restricted to the company; local password only in development and tests), *external* (app accounts with mandatory email verification, invitation unless signup is opened on purpose, MFA required where data is confidential) or *mixed* (staff only via the identity provider, externals via app accounts). Record it in the repo's architecture doc. Details: `references/identity.md`.
- **One login path:** every login runs through django-allauth's flows, the admin login included. No separate login endpoint; it would bypass rate limits, verification and MFA. Django owns the user whatever the identity provider.
- **External users see only their own data:** querysets scoped to the user or organisation, tested with a second user. Their accounts are personal data: purpose, retention and privacy notice agreed with data protection before launch.
- **Browser → realtime service: the same session cookie**, validated by Django over its internal API, accepted only when the browser does not signal a cross-site request (Fetch Metadata, Origin as fallback). No tokens in URLs.
- **Machine clients: API keys**, random, shown once, stored hashed, revocable.
- **Service → service: internal endpoints** guarded by a shared secret, compared in constant time, failing closed.
- **Authorization lives in code** (permissions, querysets scoped to the user), never only in the UI.

Details and checklists: `references/identity.md`, `references/security.md`.

## 4. Data and migrations

- **One owner per table.** Django migrates its apps' tables; the realtime service migrates its own tables with Alembic, filtered to its metadata and with its own version table. The other side reads through unmanaged models, never writes.
- **Migrations are committed and backward compatible for one release** (add, backfill, then remove), so a rollback never needs a down-migration.
- **Migrations run as an explicit deploy step,** never on container start in production.
- **One PostgreSQL driver** (psycopg 3) for Django, async SQLAlchemy and the LangGraph checkpointer.

## 5. Async work and streaming

- **Celery tasks take IDs, not objects,** are idempotent, have time limits, and are **enqueued with `transaction.on_commit`**.
- **Server-Sent Events are the default** for server-to-client streams (events, agent tokens, progress). Use a WebSocket only when the client must send messages too.
- **Fan-out across processes goes through Redis pub/sub** (or streams); no in-process state that only one worker sees.
- **Agent workloads** run in the FastAPI service and follow `agentic-engineering` (LangGraph checkpointer holds run state; the queue only starts or resumes runs).

## 6. Frontend

- **Tooling comes from create-vue** (TypeScript, ESLint + Oxlint, Vitest, Playwright, Router, Pinia), so it tracks current Vue recommendations. The project adds only the Django integration.
- **Django serves every page; there is no `index.html`.** Vite builds into Django's static dir with a manifest (django-vite); in development it serves assets with HMR.
- **Two entry points:** islands mounted into Django templates, and one SPA under `/app/`.
- **All HTTP goes through one small `fetch` client** that sends the CSRF header; lint enforces it.
- **Components use `<script setup lang="ts">`;** styling and tokens per the `uiux-*` skills.

## 7. Local development and tooling

- **Everything runs in Docker, driven by Task.** People, agents and CI use the same `task` targets.
- **A local proxy routes like production** (`/` → Django, `/v1/*` → realtime) on one origin, so cookies, CSRF and streaming behave as in production.
- **uv for Python, pnpm for Node,** both from committed lockfiles. Never pip, npm or yarn for project dependencies (npm only bootstraps pnpm; `npx` only runs pinned agent tools such as an MCP server).
- **Containers must not leave root-owned files in the repo.**
- **CLAUDE.md carries the command surface:** where things run, start (in the background), state and logs, restart after env changes, stop and reset, tests, docs, secrets, deploy. Agents keep it current and, in an existing repo, add what is missing from the repo's real commands without overwriting (`references/repo-conventions.md`).
- **Task conventions:** every task has a description; namespaces by area; parameters as variables (`ENV=staging`); multi-component repos include component Taskfiles. Details: `references/local-dev-and-tooling.md`.
- **Docs as code:** Markdown in `docs/`, rendered with MkDocs + Material, built strictly in CI so broken links fail; no extra MkDocs plugins (the generator ecosystem is in transition, see the pitfall in `references/local-dev-and-tooling.md`).

## 8. Environments, secrets and configuration

- **Environments: local, CI, staging (recommended), production.** Settings modules describe the kind of runtime (development, test, production), not the environment: staging runs the production settings with its own values.
- **Build once, promote the same image:** a version tag builds each image once; staging and production pull the same tag. No per-environment builds; build arguments carry only artifact properties (runtime versions, app version, platform).
- **All configuration comes from the environment at runtime**; code has no environment-specific values. Per environment: encrypted `app.env` for secrets and config, plain `deploy.env` for the pinned version and host.
- **The frontend bundle holds nothing environment-specific:** relative API URLs, and runtime values rendered by Django into the page. `VITE_*` variables are public build constants.
- **The environment name is a label** (logs, error reports, a badge outside production); behaviour differs only through settings and explicit variables.
- **Staging has its own secrets and no production personal data.**
- **Secrets are committed only encrypted** (SOPS + age); plaintext env files are gitignored and blocked by a pre-commit hook. Generated `.example` files let a new developer boot the stack before they can decrypt.
- **Removing a person means re-encrypting and rotating** every secret they could read.

## 9. CI/CD and deployment

- **CI files are thin wrappers over Task targets,** so GitHub Actions and GitLab CI stay interchangeable.
- **Third-party CI actions are pinned by commit SHA,** kept current by Dependabot or Renovate; jobs get least-privilege permissions.
- **A version tag builds and pushes immutable images.** Production runs only an explicitly pinned version, set in a committed file; the git log of that file is the deploy history, and a rollback is a revert.
- **A release is pull → migrate → up (wait for healthy).**
- **Production containers are hardened:** non-root, no capabilities, no privilege escalation, read-only root filesystem.
- **Backups leave the host** and restores are tested.

## 10. Observability baseline

Every service has liveness and readiness endpoints used by healthchecks, logs to stdout with request context, and reports errors to Sentry (or the team's equivalent) tagged with release and environment. Tracing via OpenTelemetry is recommended where requests cross services or agents run (`agentic-engineering` covers Langfuse).

## 11. Testing

- **Backend tests run against real PostgreSQL and Redis** in the same containers as development, plus a check that no migration is missing.
- **Frontend:** type-check, lint and unit tests.
- **End-to-end tests run against built assets behind the proxy,** exactly like production routing.
- **Security behaviour is tested:** CSRF enforcement, logout invalidating sessions, cross-site refusal, fail-closed when a dependency is down.

## Dependencies and versions

- **Rules, not pins:** Python = the newest minor every core package officially supports; Node = current Active LTS; PostgreSQL and Redis = current stable majors; Django = a supported release with at least a year of security updates left; Debian suite of base images pinned on purpose.
- **Lockfiles are law:** install only from `uv.lock` and `pnpm-lock.yaml` (frozen) in images and CI; dependency updates arrive as reviewed pull requests.
- **Pre-1.0 and fast-moving packages** (FastAPI, SQLAlchemy minors, TypeScript majors, pnpm majors) get read release notes before every upgrade. Known traps are listed in the references.

## Project structure (reference)

```
repo/
  backend/            # Django: config/settings, users, api, templates, static
  realtime/           # FastAPI: routers, auth, db, models, alembic/   (if used)
  frontend/           # create-vue tooling + src/ (islands, SPA), e2e/
  docker/             # app/Dockerfile (dev + prod targets), proxy/Caddyfile, start scripts
  compose.local.yml   # dev stack · compose.ci.yml (CI overlay) · compose.deploy.yml (staging + production)
  docker-bake.hcl     # release images (multi-platform on request)
  Taskfile.yml        # the one command surface
  .envs/              # local|staging|production: app.env.enc (+ .example); staging|production: deploy.env
  scripts/            # deploy.sh, env_examples.py
  docs/ + mkdocs.yml  # index, architecture, environments, operations; built strictly in CI
  pyproject.toml, uv.lock, .pre-commit-config.yaml, .mcp.json, CLAUDE.md
```

`/fullstack-scaffold` (user-invoked) generates this layout and verifies it with the repo's own `task ci`.

## Review checklist (top mistakes)

| Mistake | Fix |
|-|-|
| Token in localStorage, or token in a URL | Session cookie + CSRF; realtime validates the cookie via Django |
| Own JSON login view next to allauth | All logins through allauth (rate limits, verification, MFA); admin login redirected there |
| External user can fetch another user's object | Queryset scoped to `request.user`; test with a second user |
| Two services writing one table, or two migration systems on it | One owner per table; read-only models on the other side |
| Migrations run on container start in production | Separate migrate step in the deploy |
| Celery task enqueued inside the transaction | `transaction.on_commit` |
| Blocking I/O inside `async def` | Async client, or run in a thread / Celery |
| HTTP calls scattered across components | One `fetch` client module, lint-enforced |
| Deploying `latest` or an unpinned tag | Pinned version in a committed file |
| API URL or other per-environment value in a Vite `.env` file | Relative URLs; runtime config rendered by Django |
| Separate staging build or `staging.py` settings | Same image and production settings; values from `.envs/staging/` |
| CI logic that developers cannot run locally | CI calls the Task targets |
| Secrets in plaintext in git, or in images | SOPS-encrypted env files, injected at runtime |
| Root-owned files in the repo after a container run | Hand files back to the host user; caches in volumes |
| API used from memory | Check the lockfile version and the docs (context7 or web) first |

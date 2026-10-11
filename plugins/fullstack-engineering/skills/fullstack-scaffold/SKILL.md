---
name: fullstack-scaffold
description: "Generates a new web app repo on the fullstack-engineering reference stack, verified by its own CI: Django with REST API and login (company SSO, external accounts with MFA, or both), optional FastAPI realtime service, Vue 3 + TypeScript, PostgreSQL, Redis, Celery, Docker Compose, Task, SOPS, MkDocs, GitHub/GitLab CI, CLAUDE.md files. Invoke as /fullstack-scaffold when starting a new web app, internal tool or portal (\"scaffold\", \"new project\", \"neues Projekt aufsetzen\")."
disable-model-invocation: true
---

# Fullstack Scaffold

Generates a repo that follows `fullstack-engineering` and passes its own CI on the first run. The template holds no dependency versions; the script resolves current releases with `uv add`, `pnpm add` and `create-vue@latest`, so the new repo starts with fresh lockfiles.

## 1. Ask before generating

Ask in one message, with defaults, and wait for the answers:

| Question | Default | Flag |
|-|-|-|
| Project slug (kebab-case) and display name | — | `--name`, `--title` |
| Target directory | `./<slug>` | positional |
| Realtime/streaming/agent service needed? (see shapes in `fullstack-engineering` §2) | no → Django only | `--no-realtime` when no |
| Who logs in? Staff only, external people (customers, applicants, partners), or both (see `fullstack-engineering/references/identity.md`) | internal | `--audience internal\|external\|mixed` |
| CI platform | GitHub, or wherever the organisation hosts its code | `--ci github\|gitlab\|both\|none` |
| Production hostname | `app.example.com` | `--app-host` |
| age public keys for secrets (the developer's and CI's) | none: encrypt later | `--age-recipient` (repeatable) |

## 2. Check prerequisites

Required on the machine: Docker (with Compose and Buildx), Task, uv, pnpm, git; sops if age keys are given. Check with `--version`; say what is missing instead of working around it.

## 3. Generate

```bash
python3 <this skill>/scripts/scaffold.py <target> --name <slug> [--title "..."] \
  --audience internal|external|mixed [--no-realtime] [--ci github|gitlab|both|none] \
  [--app-host host] [--age-recipient age1...]
```

The script copies the template, keeps only the parts for the chosen audience and shape (marker-fenced in the template), resolves Python and Node dependencies, runs create-vue and lays the Django integration over it, generates the initial migration, updates pre-commit hook revisions, pins GitHub Actions to commit SHAs, and formats the result with the project's Ruff config. It never touches an existing non-empty directory. For an existing repo, do not scaffold over it: bring its CLAUDE.md up to the conventions with the repo's real commands (`fullstack-engineering/references/repo-conventions.md`) and adopt single parts of the template deliberately.

Defaults for runtimes (Python, Node, PostgreSQL, Redis, Caddy, Debian suite) sit in `stack.json` with the rule each one follows. Before generating, check that the defaults still match their rules (for example a newer Node Active LTS, or a Python minor that all core packages now support) using the official sources in `fullstack-engineering/references/sources.md`; if not, update `stack.json` first and mention it.

## 4. Verify, do not assume

In the new repo, run and report the results:

```bash
task setup      # env file, images, frontend deps
task ci         # pre-commit, frontend checks, backend tests, end-to-end
```

If something fails because a framework moved (a renamed Vite option, a new create-vue layout, a changed lint rule, a pnpm build approval prompt), fix it by checking the current docs (context7 or the official site), never from memory. Then fix the template in this skill too, so the next scaffold works, and tell the person what changed.

## 5. Hand over

Tell the person:

- what was generated (shape, CI platform) and the result of `task ci`;
- how to start and stop: `task dev:up` (background, waits until healthy), `task dev:logs`, `task dev:down`; open http://localhost:8000, log in with `DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD` from `.envs/local/app.env` (external/mixed: outgoing mail lands in Mailpit, http://localhost:8025);
- open steps that need people: create the git remote, add age keys to `.sops.yaml` and run `task secrets:encrypt ENV=local` (if not done), fill `.envs/staging/app.env` and `.envs/production/app.env` and encrypt them (own secrets each), set `APP_HOST`/`DEPLOY_SSH_TARGET` in both `deploy.env` files, make sure each target server runs the shared Traefik (`fullstack-engineering/assets/traefik-host/`), for internal/mixed register the app at the company identity provider (Entra: ask IT; docs/operations.md), for external/mixed set up a mail transport (`EMAIL_URL`) and agree the privacy notice with data protection before external users get access, set CI secrets per environment (registry, `SOPS_AGE_KEY`, deploy SSH key and known_hosts in the `staging` and `production` CI environments);
- that the event button on the dashboard is the end-to-end check of the async chain (Celery → Redis → stream): replace the UI, keep a test for the chain.

## What the generated repo contains

| Area | Content |
|-|-|
| `backend/` | Django settings split, custom user (email login), `ApiKey` (hashed), all logins through allauth's pages (admin included) styled in the app layout; per audience: company SSO over OpenID Connect (active only when configured), external accounts with email verification by code, MFA (authenticator app, passkeys, recovery codes) and an MFA requirement switch, staff SSO-only rule (mixed); internal `validate-session`/`validate-key`, Celery with an on-commit demo task, tests per audience |
| `realtime/` (optional) | FastAPI, SSE `GET /v1/events` fed by Redis pub/sub, auth via Django session cookie with cross-site refusal, async SQLAlchemy (psycopg) with Alembic limited to its own tables, health/readiness, tests |
| `frontend/` | create-vue tooling; `vite.config.ts` for django-vite; styles and islands for Django pages (`main.ts`) and SPA under `/app/` (`app-main.ts`); `fetch` client with CSRF; session store; EventSource composable; Tailwind (also scanning Django templates); Playwright smoke test (login, live event, logout) |
| `docker/`, `compose.*.yml`, `docker-bake.hcl` | One multi-target Dockerfile; dev and CI stacks; one hardened deploy stack for staging and production; Caddy proxy; Mailpit for external/mixed; production images per service, multi-platform on request (`PLATFORMS`) |
| `Taskfile.yml`, `scripts/` | Command surface; `deploy.sh` (pull, migrate, up via Docker context over SSH, `ENV=staging\|production`); env example generator |
| `.envs/`, `.sops.yaml`, `.pre-commit-config.yaml` | Encrypted env files for local, staging and production, pinned deploy state per environment, secrets guards |
| `mkdocs.yml`, `docs/` | Docs site (index, architecture, environments, operations): `task docs:serve`, strict build in CI |
| `.mcp.json` | Playwright MCP (pinned) so agents can check the UI in a browser |
| CI | GitHub Actions (ci incl. docs, release on tag, manual deploy per environment, Dependabot) and/or GitLab CI, both calling Task |
| `CLAUDE.md` ×4, `docs/` | Per `engineering-standards` |

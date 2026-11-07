# CLAUDE.md — __PROJECT_TITLE__

## Read Docs Before Code

Before changing an area, read the matching `docs/` page, then the component CLAUDE.md (`backend/`, `frontend/`<!-- >>> realtime -->, `realtime/`<!-- <<< realtime -->), only then the source. Built on the fullstack reference (`fullstack-engineering` skill); deviations are recorded in `docs/architecture.md`.

## Project

__PROJECT_TITLE__: Django (web, admin, REST API, auth)<!-- >>> realtime --> + FastAPI realtime service (Server-Sent Events)<!-- <<< realtime --> + Vue 3 islands and SPA, on PostgreSQL, Redis and Celery. Django serves every page; the browser sees one origin.

## Commands

Everything runs in Docker through Task. Never run Django, pytest, uv sync or pnpm on the host; never call `docker compose` directly when a task exists.

```bash
task setup                 # first run: env file, images, dependencies
task dev:up                # start in the background, wait until healthy -> http://localhost:8000
task dev:ps                # service state
task dev:logs -- django    # follow logs (one service or all)
task dev:restart -- django # recreate after .envs/local/app.env changes (a plain restart keeps old env)
task dev:down              # stop (data stays); task dev:reset deletes local data
task dev:build             # rebuild images after Dockerfile or dependency changes
task dev:manage -- <cmd>   # Django management command, e.g. shell, createsuperuser
task dev:makemigrations    # then commit the migration
task deps:lock             # after editing pyproject.toml or package.json
task docs:serve            # docs site at http://localhost:8888
task --list                # everything else
```

Access points (admin, Flower, mail catcher): `backend/CLAUDE.md`.

### Secrets & env files

`.envs/<env>/app.env.enc` (SOPS + age) is committed for `local`, `staging` and `production`; plaintext `app.env` is gitignored and blocked by pre-commit. Edit with `task secrets:edit ENV=local|staging|production`; it regenerates `app.env.example`. Deploy targets (host, registry, SSH target) live in `.envs/<env>/deploy.env`. How values reach Docker, Django and Vue: `docs/environments.md`.

### Release & deploy

Before tagging: `task release:smoke` (production images and settings behind a throwaway proxy). An annotated tag `vX.Y.Z` on `main` runs the release pipeline: validate the tag → build and push → smoke test of the pushed images → deploy to staging → manual approval → production. Each deploy is `task deploy ENV=<env> VERSION=vX.Y.Z` (preflight, backup, pull, migrate, up, verify). Rollback: the deploy workflow/pipeline with the previous version and `ROLLBACK=1`. Details: `docs/operations.md`.

## Testing

| Runs in CI | Locally |
|-|-|
| Lint (pre-commit: ruff, hygiene, secrets guard) | `task check:lint` |
| Docs build (strict: broken links fail) | `task check:docs` |
| Frontend type-check, eslint, vitest | `task check:frontend` |
| Django<!-- >>> realtime --> + realtime<!-- <<< realtime --> (pytest, real Postgres/Redis), migration check | `task test:backend` |
| End-to-end (Playwright, built assets) | `task test:e2e` |
| Production smoke test (main and release tags) | `task release:smoke` |
| All of the above, as CI runs them | `task ci` |

## Constraints

- `uv` for Python (`pyproject.toml` + `uv.lock`), `pnpm` for the frontend. Never pip, npm or yarn (npm only installs pnpm itself inside images).
- Max file: 800 lines. Max function: 100 lines.
<!-- >>> realtime -->
- Each table has one owner: Django migrations or Alembic (realtime), never both.
<!-- <<< realtime -->
- Frontend HTTP only through `frontend/src/api/client.ts`.
- Every login runs through django-allauth's pages (`/accounts/`); no login endpoint of our own. Login audience: __AUTH_AUDIENCE__ (see `docs/architecture.md`).
<!-- >>> internal -->- Login: company SSO (OpenID Connect, e.g. Entra ID) where configured; local login only for development and tests.
<!-- <<< internal --><!-- >>> external -->- External users: email verification by code, MFA (required in production), invite-only unless `SIGNUP_OPEN`.
<!-- <<< external --><!-- >>> mixed -->- Staff and SSO-linked accounts log in via the company identity provider only (once configured); external users via verified accounts with MFA. Staff rights are never granted at signup.
<!-- <<< mixed -->- Deploys name an explicit release version (`VERSION=vX.Y.Z`), never `latest`; an older version than the running one needs `ROLLBACK=1`.

## Git

Branches: `main` ← `feat/*`, `fix/*`, `chore/*`. Commits: `<type>(<scope>): <subject>` (feat, fix, docs, style, refactor, test, chore).

## Planning

Plans and decisions go on the tracker issue. `./plans/<branch-name>/` is for temporary files only — not authoritative.

## Agent practices

Recommended reading: https://code.claude.com/docs/en/best-practices (live; this file and the repo's standards take precedence; raise real conflicts with the team).

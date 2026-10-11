# Local development and tooling

## One command surface: Task

`Taskfile.yml` is the interface for people, agents and CI. Typical targets:

| Target | Does |
|---|---|
| `setup` | Env file (decrypt or copy example), build images, install frontend deps |
| `dev:up` / `dev:ps` / `dev:logs` / `dev:restart` / `dev:down` / `dev:reset` | Local stack: start in the background (`up -d --wait`), state, logs, recreate after env changes, stop, delete local data (with a prompt) |
| `dev:manage -- <cmd>` | Django management commands in the container |
| `dev:makemigrations`, `dev:alembic-revision -- "msg"` | New migrations (commit them) |
| `deps:lock`, `deps:upgrade` | Re-lock or upgrade, then review the lockfile diff |
| `check:lint`, `check:docs`, `check:frontend`, `test:backend`, `test:e2e`, `ci` | Exactly what CI runs |
| `docs:serve` | Docs site with live reload |
| `secrets:* ENV=…` | SOPS edit/encrypt/decrypt/updatekeys/examples per environment |
| `release:build`, `deploy ENV=…`, `deploy:<verb>` | Images and deployment per environment |

Conventions:

- **Every task has a `desc`;** `task --list` (the default task) is the menu for people and agents. Internal helper tasks without `desc` stay hidden.
- **Namespaces by area** (`dev:`, `deps:`, `check:`, `test:`, `docs:`, `secrets:`, `release:`, `deploy:`), verbs after the colon. One `ci` task aggregates exactly what CI runs.
- **Parameters:** variables for choices (`ENV=staging`, `VERSION=v1.2.3`, `PLATFORMS=…`), with `requires` wherever a wrong default would be dangerous (secrets, deploys: `task deploy` without `ENV` refuses), and passed inline to scripts (`DEPLOY_ENV={{.ENV}} scripts/deploy.sh`) because an exported shell variable otherwise wins over Task's `env:`; free arguments after `--` (`task test:backend -- -k auth`).
- **Idempotent setup:** `status:` or `sources:`/`generates:` so repeated runs skip finished work; `preconditions:` with a clear message for missing tools or files.
- **Repos with several components** (e.g. web app plus desktop client): a root Taskfile `includes:` each component's Taskfile with its own `dir:`, giving namespaced commands (`task webapp:dev:up`, `task client:test`) and one root `setup`/`ci`.
- **Logic lives in Task or scripts, never only in CI files;** a developer reproduces every CI failure with the same target.

## Docs site (MkDocs)

- Docs are Markdown in `docs/`, rendered as a site by **MkDocs with the Material theme**, served with live reload in a container (`docs:serve`) and built with `--strict` in CI (`check:docs`): broken links, missing anchors and pages left out of the nav fail the build.
- Configuration: `mkdocs.yml` at the root with an explicit `nav`, `validation` for links and omitted files, Material theme features (`navigation.sections`, `content.code.copy`) and only core or pymdown Markdown extensions. **No extra plugins:** they are the part that breaks when the generator changes.
- MkDocs and the theme live in their own uv dependency group (`docs`), installed into the dev image only, never into production images.
- Docs change in the same pull request as the behaviour or command they describe; CLAUDE.md files point into `docs/` instead of duplicating it.
- **Pitfall (2026):** Material for MkDocs is in maintenance mode with end of life on 2026-11-05, and MkDocs 1.x has had no release since 2024. MkDocs 2.0 is reported to drop plugins and themes (Material requires `mkdocs<2`), so keep `mkdocs<2`. Exit paths when a fix is needed: Zensical (the Material team's successor, migration from `mkdocs.yml`) or ProperDocs (a maintained MkDocs 1.x fork). Keeping the config plugin-free makes either move small. Re-check the state before starting a new repo.

## Docker Compose

- **One Dockerfile for both Python services**, with targets `dev`, `django` (includes the built frontend) and `realtime`; dependencies installed with `uv sync --locked --no-install-project` into a venv outside the code mount; BuildKit cache mounts for uv and pnpm.
- **`compose.local.yml`:** PostgreSQL, Redis, Django (dev server, auto-migrate), Celery worker and beat, Flower, realtime (reload), a Node container for Vite, and the proxy. Code is bind-mounted; `node_modules` lives in a named volume.
- **Healthchecks + `depends_on: condition: service_healthy`** for the database, Redis and Django; services that need Django wait for it.
- **Fresh database: every migrating service before its dependents.** Not only Django (`migrate`) but also the realtime service (Alembic) migrates on start; dependents wait with `depends_on: condition: service_healthy` (or `service_completed_successfully` for a one-shot migrate container). Give migrating services a healthcheck with a generous `start_period` (30s or more), since the first run on an empty database is the slow one.
- **Ports bind to `127.0.0.1`** only.
- **Second stack side by side** (another worktree, a test stack, `-p atlas-test`): projects are isolated only by their default network. If the base file fixes `networks.default.name`, both projects join one network and `postgres` resolves to either stack. The overlay for the second project overrides the network name and drops published ports:

  ```yaml
  networks:
    default:
      name: atlas-test_default
  services:
    postgres:
      ports: !reset []
  ```

  `!reset` is a custom YAML tag, so pre-commit's `check-yaml` needs `args: [--unsafe]` (syntax check only) or an `exclude` for that file.
- **`compose.ci.yml`** overlays the local stack for end-to-end tests: built assets instead of the Vite server, a Playwright container, base URL through the proxy.
- Compose files have no `version:` key (obsolete).
- `develop.watch` is an option for the Node service on macOS/Windows file sharing; bind mounts remain fine for Python reload.

## Local proxy

A Caddy container on `localhost:8000` routes `/` to Django and `/v1/*` to the realtime service (with immediate flushing for SSE), mirroring production. Reasons: one origin for cookies and CSRF, streaming through a proxy as in production, and end-to-end tests that exercise the real routing.

## Python: uv

- `pyproject.toml` + committed `uv.lock`; `[tool.uv] package = false` for applications; dev tools in `[dependency-groups] dev`.
- Images: `uv sync --locked` (fails when the lock is stale), `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`, `UV_PYTHON_DOWNLOADS=0`, production without the dev group.
- Floors (`>=`) only where code relies on a feature; the lockfile pins the rest.

## Node: pnpm

- `packageManager` in `package.json` pins the exact pnpm; containers install that version explicitly. Do not rely on Corepack (removed from Node 25 on).
- `pnpm install --frozen-lockfile` in images and CI.
- Approve dependency build scripts explicitly when pnpm asks; review new approvals like code.
- **Tool versions can silently ignore newer config.** An older pnpm in the same major ignores settings it does not know yet (e.g. build-script approval settings): the build scripts never run and the install "fails" in odd ways later. Every environment uses the pinned `packageManager` version; when an install misbehaves, check the tool version first.
- Consider a minimum release age for new package versions as supply-chain protection (check pnpm's current setting name).

## File ownership

Containers that write into the bind-mounted repo must not leave root-owned files (build output, test reports, package stores). Either run as the host user, or hand the written paths back to the host user's UID/GID when the command ends, and keep package stores inside volumes. Pass the real UID/GID from the Taskfile (`id -u`, `id -g`), since CI runners often are not UID 1000.

## pre-commit

`.pre-commit-config.yaml` with hygiene hooks, Ruff (`ruff-check --fix`, `ruff-format`) and local hooks that block plaintext env files and check that `.example` env files are current. Hook revisions are updated with `pre-commit autoupdate` (Dependabot does not cover them). The config also works with compatible runners such as prek.

## Pitfalls

- A `DJANGO_SETTINGS_MODULE` in the container env overrides pytest's ini setting; force test settings with `--ds`.
- `docker compose up --wait` treats services without a healthcheck as ready once started; a service that migrates on start can still be booting.
- Tool caches (`.ruff_cache`, `__pycache__`) must never end up in templates or images (`.dockerignore`).

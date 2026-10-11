# CI/CD, deployment and operations

## Pipeline contract (platform-neutral)

| Stage | Task target | Runs on |
|---|---|---|
| Lint | `check:lint` (pre-commit on all files) | Merge requests / pull requests, main |
| Docs | `check:docs` (strict MkDocs build) | same |
| Frontend | `check:frontend` (type-check, lint, unit tests) | same |
| Backend | `test:backend` (migration check + pytest against real Postgres/Redis) | same |
| End-to-end | `test:e2e` (built assets, full stack behind the proxy, Playwright) | same, after backend |
| Release | `release:build REGISTRY=... VERSION=vX.Y.Z` (bake, push) | version tags |
| Deploy | `deploy ENV=staging\|production` (pull → migrate → up) | manual, one protected CI environment each, with its own secrets |

GitHub Actions and GitLab CI files only install Task (and uv/Docker where needed) and call these targets. Switching platforms means rewriting a thin wrapper, not the pipeline.

## CI hardening

- Pin third-party actions to a full commit SHA with the version as a comment; let Dependabot or Renovate update the pins. (A 2025 incident repointed tags of a popular action to a secret-stealing commit; SHA pins are the defence.)
- `permissions:` least privilege at the top (`contents: read`), wider grants per job only where needed (e.g. `packages: write` for releases).
- `concurrency` per ref for CI; a single non-cancelling group for deploys.
- Prefer OIDC to long-lived cloud credentials where the registry or cloud supports it.
- GitLab: pin matching `docker:<version>-cli` and `docker:<version>-dind` images with TLS (`DOCKER_TLS_CERTDIR`).

## Release

- A version tag `vX.Y.Z` builds production images with `docker buildx bake` and pushes `<registry>/<project>-<service>:vX.Y.Z`. The version is baked into the image (`APP_VERSION`, shown by the health endpoint).
- No mutable `latest` for deployment. Registry build caches go to a separate cache tag.
- **Local build from the CI bake file:** it pushes and uses the registry cache, so override both to load into the local Docker instead: `docker buildx bake --set '*.output=type=docker' --set '*.cache-from=' --set '*.cache-to='` (`type=docker` takes one platform).
- **Multi-platform:** one bake run with several platforms (`PLATFORMS=linux/amd64,linux/arm64`) pushes a single multi-platform image per tag; no per-architecture tags or manifest-merge scripts. Stages whose output is platform-independent (the frontend bundle) run on `$BUILDPLATFORM`, so they are not emulated per target.

## Deploy (single host)

- **Staging then production, same images:** one compose file and one deploy script for both, selected by an environment parameter; each environment has its own `.envs/<env>/`, compose project name and proxy router names, so both can share a host. Production gets the version staging ran (`environments.md`).
- **Pinned version:** `APP_VERSION` in the committed `deploy.env` per environment; bumping it is its own pull request, its git log is the deploy history, a rollback is a revert of the bump.
- **Caller-driven:** a laptop or a CI job decrypts secrets, resolves `compose.deploy.yml`, and drives the remote Docker daemon through a Docker context over SSH. The host needs no repo checkout, no decryption key and no env file on disk. (Access to the host's Docker socket still means access to the running secrets.)
- **Sequence:** registry login → `compose pull` → migrate as one-shot containers (Django, Alembic) → `compose up -d --remove-orphans --wait`.
- **Migrations stay backward compatible for one release**, so the previous image works against the new schema and rollbacks need no down-migrations.
- SSH: key-based, a dedicated deploy user, known_hosts pinned in CI; reuse connections (ControlMaster) for speed.
- Larger needs: Kamal is the closest step up for multi-host Docker deploys; avoid exposing self-hosted PaaS panels; Kubernetes only with a real platform team.

## Production hardening

- Containers run as a fixed high UID, `cap_drop: [ALL]`, `security_opt: no-new-privileges`, `read_only: true` with `tmpfs: /tmp`; anything that writes files gets an explicit volume (e.g. uploads).
- Base images: Debian slim with the suite pinned on purpose (unsuffixed tags switch suites by themselves). Hardened images (distroless/DHI/Wolfi) are an option once the team has adapted healthchecks and debugging.
- PostgreSQL and Redis are not published to the host network; only the proxy faces the internet.

## Reverse proxy

TLS termination and routing per host: `/` → Django, `/v1/*` → realtime with immediate flushing for SSE and long read timeouts for streams. Locally and in CI a Caddy container per app mirrors these routes.

On servers: **one shared Traefik per server**, started once, owning the external `proxy` network; app stacks attach by labels and never run their own proxy. Reference setup with setup steps: `assets/traefik-host/` (Traefik behind a read-only Docker socket proxy, `exposedByDefault: false`, HTTP→HTTPS at the entrypoint, `aliasHeadersStrategy: delete`, compression that excludes `text/event-stream`, Mozilla-intermediate TLS, Let's Encrypt, dashboard behind basic auth). Rules for app stacks: router and service names unique per server (project + environment), only internet-facing services join `proxy`, no published ports in production, quoted label values. Caddy is an acceptable alternative where a team already runs it; the same rules apply.

## Observability baseline

- `/health` (liveness) and a readiness endpoint per service (database, Redis); used by container healthchecks.
- Logs to stdout, structured, with request or trace IDs; no secrets in logs.
- Errors to Sentry (or equivalent) for Django, the realtime service, Celery and the frontend, tagged with release (`APP_VERSION`) and environment.
- OpenTelemetry traces recommended across services and agent runs; configure exporters explicitly (auto-configuration defaults change between releases). Langfuse for LLM traces per `agentic-engineering`.

## Backups

- Scheduled `pg_dump -Fc` with retention, copied **off the host** encrypted (e.g. restic or object storage). A dump on the same machine is not a backup.
- A restore test on a schedule (monthly), documented in `docs/operations.md`.
- WAL archiving (pgBackRest, WAL-G) when the recovery point must be under a day or the database grows large.

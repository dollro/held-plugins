# CI/CD, deployment and operations

## Pipeline contract (platform-neutral)

| Stage | Task target | Runs on |
|-|-|-|
| Lint | `check:lint` (pre-commit on all files, including the CI wrapper check) | Merge/pull requests, main |
| Docs | `check:docs` (strict MkDocs build) | same |
| Frontend | `check:frontend` (type-check, lint, unit tests) | same |
| Backend | `test:backend` (migration check + pytest against real Postgres/Redis) | same |
| End-to-end | `test:e2e` (built assets, full stack behind the proxy, Playwright) | same, after backend |
| Smoke | `release:smoke` (production images and settings, `compose.deploy.yml`, throwaway proxy) | main (local build); release tags (the pushed images) |
| Validate | `release:validate VERSION=vX.Y.Z` (shape, annotated, newer than the last release) | release tags, first |
| Release | `release:build REGISTRY=... VERSION=vX.Y.Z` (bake, push) | release tags, after validate |
| Deploy | `deploy ENV=staging\|production VERSION=vX.Y.Z [ROLLBACK=1]` | release tags: staging after smoke, production after approval; rollback by re-running an older tag's deploy |

## Platform-neutral by construction

The rules in this skill name **requirements**; a CI platform is only a way to meet them.

- **Logic lives in Task targets and `scripts/`,** where a developer can run it. CI files hold only what the platform must hold: triggers, secrets, environments, approvals, concurrency and job images.
- **One variable switches where targets run,** not CI-only logic: e.g. `STACK=local|ci|job` makes the same `task test:backend` exec into the compose stack locally, use the CI overlay, or run directly in the job's own container. CI jobs only install the task runner and call the targets developers run.
- **Scripts never read platform variables** (`CI_COMMIT_TAG`, `GITHUB_REF_NAME`). The CI file maps them to neutral ones (`VERSION`, `RELEASE_REGISTRY`, `DEPLOY_SSH_KEY` as a path or as content).
- **A check enforces it:** `scripts/check_ci.py` (pre-commit) fails when a CI file runs anything but `task ...` or a known setup step, and, when several platforms are configured, when they call different Task targets.
- **Platform features go in the mapping below,** not into the rules. Another platform (Forgejo/Gitea Actions, Bitbucket, Jenkins) means one more column.

| Requirement | GitLab CI | GitHub Actions |
|-|-|-|
| One deploy per environment at a time | `resource_group: <env>` | `concurrency: deploy-<env>`, `cancel-in-progress: false` |
| An older release never overwrites a newer one by accident | "Prevent outdated deployment jobs" with "Allow job retries for rollback deployments"; tag deploy jobs set `ROLLBACK=1`, so only an explicit re-run deploys an older tag | The deploy script refuses it unless the deploy workflow's `rollback` input is set |
| Deploy secrets and approval per environment | Protected environments, variables scoped to the environment (SSH key and known_hosts as file variables) | Environments with required reviewers and environment secrets; the job that declares `environment:` gets them (also in a reusable workflow) |
| Only maintainers create release tags | Protected tags `v*` (only `*` works as a wildcard: `v[0-9]*` matches nothing) | Tag ruleset `v*` |
| Annotated tag history available to the validate job | `GIT_DEPTH: 0`, `GIT_FETCH_EXTRA_FLAGS: --tags` | `fetch-depth: 0`; the script re-fetches tags with `--force` (checkout can rewrite annotated tags as lightweight) |
| Test jobs cancelled by newer commits; deploys never | `interruptible: true` on test jobs only | `concurrency` with `cancel-in-progress: true` on CI workflows only |
| Image-building jobs end instead of hanging | `timeout:` | `timeout-minutes:` |
| Rollback | Re-run the deploy job of the older tag's pipeline (a re-run cannot add variables, so none is needed) | Run the deploy workflow with environment, version, `rollback`; it checks out the version's tag |
| Test jobs in the app image, databases as services | `image:` the app image, `services:` Postgres/Redis/mail catcher; `FF_NETWORK_PER_BUILD: "true"` so services reach each other, `CI_DEBUG_SERVICES: "true"` for their logs. Services start before the checkout: one that reads code from the mounted `/builds` waits for its files. Images from the project's registry need no runner config (job token) | `container:` the app image, `services:` Postgres/Redis |
| Deploy history | Operate > Environments | Deployments page of the environment |
| Smoke test and deploy use the same Docker/Compose versions | One exact job image for all Docker jobs (`docker:29.9.3-cli` + the same `-dind`), never a major-only tag | Compose installed from `scripts/ci/tools.txt`, the version the GitLab job image ships (the check forbids setup actions that download their own) |
| Third-party CI code pinned | Job images by digest, CI components by version | Actions by commit SHA |
| CI tool downloads survive an outage of their source | Mirror = the project's generic package registry (`TOOL_MIRROR_URL=$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/generic`, `TOOL_MIRROR_HEADER="JOB-TOKEN: $CI_JOB_TOKEN"`); mirror job in stage `.pre`, protected refs, `allow_failure` | No generic package store: `TOOL_MIRROR_URL` (variable) and `TOOL_MIRROR_HEADER` (secret) point at any store with GET and PUT; mirror job on pushes to main, `continue-on-error`. Unset: original source only |

## CI hardening

- Pin third-party actions to a full commit SHA with the version as a comment; let Dependabot or Renovate update the pins. (A 2025 incident repointed tags of a popular action to a secret-stealing commit; SHA pins are the defence.)
- `permissions:` least privilege at the top (`contents: read`), wider grants per job only where needed (e.g. `packages: write` for releases).
- Prefer OIDC to long-lived cloud credentials where the registry or cloud supports it.
- **Every image-building job has a timeout,** sized from measured cold builds; a stuck push otherwise holds the runner until its global limit.
- **CI images that tests share are tagged by commit SHA,** never by a mutable branch tag: overlapping pipelines would test each other's images.
- **Measure before optimising.** Profile a real pipeline and report before/after for a cold and a warm runner. In Docker-in-Docker most pipeline time is often image pulls into an empty daemon (extraction more than download), not tests, so a registry mirror helps less than it seems. Cheap wins: share the frontend build as an artifact, use the official Playwright image as job image, skip repeated migrate/seed, drop dead cache sources, don't push stages that are only cache (`cache-to` is enough). Avoid binding the host Docker socket into jobs (isolation, concurrency).
- **Test jobs run in the app image, not in Docker-in-Docker.** Every DinD job starts with an empty image store and pulls the same images again. Instead the job's `image:` is the app's CI image (tagged by commit SHA) and Postgres, Redis and the mail catcher are `services:`. The runner caches job images between jobs, backend tests and end-to-end run side by side on a shared frontend build (artifact + `needs:`), and the tests need no privileged mode. Keep DinD only for jobs that build images. Decide early whether the dev image carries the code or only gets it from a mount: an image with no code baked in is limited as a service.
- **Merge bursts multiply pipelines:** with interruptible tests the platform cancels superseded runs; otherwise merge one at a time.
- **CI works wherever its runner is.** Deploys only over SSH; no host Docker socket, host paths or localhost shortcuts to production. The runner's image cache only speeds things up: a cold runner on another host must pass too.
- **A runner that shares a host with production is isolated,** because Docker-in-Docker needs privileged mode, which is root on the host: no privileged jobs there, protected runners for jobs with secrets, CPU and memory caps, never the production Docker socket.
- Supply chain, next step: sign images and attach build provenance (cosign or the platform's attestations) and verify before deploy.
- **Docker and Compose versions are pinned exactly, in one place per platform, and bumped like dependencies** (Renovate, Dependabot). A major-only tag (`docker:29-cli`) floats between the smoke test on main and the deploy days later; an exact pin nobody bumps falls behind. Seen in practice: the deploy job still ran `docker:28.5.2-cli` (Compose 2.40) while the smoke test ran Compose 5.6, and `up --wait` failed only in production. Compose jumped from v2 to v5: read its release notes on every major bump. Both `smoke.sh` and `deploy.sh` print the Compose version they use.
- GitLab: pin matching `docker:<version>-cli` and `docker:<version>-dind` images with TLS (`DOCKER_TLS_CERTDIR`).
- **Every tool CI downloads is pinned with its SHA-256 in one file and fetched through a mirror.** `scripts/ci/tools.txt` holds name, exact version, SHA-256 and original URL per tool (Task, sops, Compose; any further one such as `regctl`); `scripts/ci/install-tools.sh` is the only way CI installs them, never `curl | sh`, a "latest" installer or a setup action that downloads at run time. In CI it tries the mirror first (`$TOOL_MIRROR_URL/<name>/<version>/<file>`, any HTTP store with GET and PUT, optional auth header in `TOOL_MIRROR_HEADER`), then the original source; a missing or wrong mirror copy falls back to the source, and the hash is checked either way. Outside CI only the original source is used. A mirror job on protected refs only (it writes), allowed to fail, uploads every pinned version the mirror lacks (`scripts/ci/mirror-tools.sh`), so a bump is mirrored by the first pipeline on a protected branch after it, provided the source is reachable then. Bump with `scripts/ci/pin-tool.sh <name> <version>` (rewrites version and hash) after reading the release notes. Seen in practice: release downloads from a large code host returned 5xx for hours, and every job of every pipeline failed at the Task download before running a single check. Job images are the same risk one level down: a registry pull-through cache or dependency proxy covers them.

## Release

- An **annotated** tag `vX.Y.Z` on main (protected pattern) starts the release pipeline: validate → build and push → smoke test of the pushed images → staging → approval → production. The version is baked into the image (`APP_VERSION`, shown by the health endpoint).
- **Validate first:** shape, annotated, newer than the newest release. It fails in seconds instead of after the build.
- `release:build` pushes `<registry>/<project>-<service>:vX.Y.Z` with `docker buildx bake`. No mutable `latest` for deployment. Registry build caches go to a separate cache tag.
- **Build once, test as built:** smoke test, staging and production use the pushed images. Next step for larger teams: build the production image once per commit, tag it with the commit SHA, run every test against it, and release by retagging the tested digest (`crane tag` keeps the digest and signatures; `docker buildx imagetools create` can change the digest of a single-platform image). Promote by digest, not by tag.
- **Local build from the CI bake file:** it pushes and uses the registry cache, so override both to load into the local Docker instead: `docker buildx bake --set '*.output=type=docker' --set '*.cache-from=' --set '*.cache-to='` (`type=docker` takes one platform).
- **Multi-platform:** one bake run with several platforms (`PLATFORMS=linux/amd64,linux/arm64`) pushes a single multi-platform image per tag; no per-architecture tags or manifest-merge scripts. Stages whose output is platform-independent (the frontend bundle) run on `$BUILDPLATFORM`, so they are not emulated per target.

## Deploy (single host)

- **Staging then production, same images:** one compose file and one deploy script for both, selected by an environment parameter; each environment has its own `.envs/<env>/`, compose project name and proxy router names, so both can share a host.
- **The release pipeline deploys its own tag** (`task deploy ENV=<env> VERSION=$TAG`); the deploy job needs the image release and the preflight. No version is committed per environment, so no bump commit or pin file is needed and no deploy can run before its images exist. `deploy.env` holds only the target (host, registry, SSH target). Deploy variables are protected and scoped to their environment.
- **Prerelease tags (`vX.Y.Z-rc.N`) run only the read-only preflight:** a safe way to prove protected variables and SSH on tag pipelines before the first real release.
- **Laptop deploys name the version** (`VERSION` required, never a default) **from a checkout at that tag:** the compose file and scripts come from the checkout and must match the images. The deploy script checks both.
- **Caller-driven:** a CI job (or, in an emergency, a laptop) decrypts secrets, resolves `compose.deploy.yml`, and drives the remote Docker daemon through a Docker context over SSH. The host needs no repo checkout, no decryption key and no env file on disk. (Access to the host's Docker socket still means access to the running secrets.)
- **Sequence:** preflight → backup → pull → migrate as one-shot containers (Django, Alembic) → `compose up -d --remove-orphans --wait` → verify.
- **Preflight** proves, before anything changes: SSH login as the deploy user, the remote Docker daemon, registry login on the server and the caller, every image tag present in the registry the server pulls from, that registry equal to the one the release pushed to, and the version not older than the running one. Run it once by hand before the first release (`task deploy:preflight ENV=staging VERSION=...`), not first on release day.
- **Required means required:** the SSH target names user and port (`ssh://deploy@host:2222`); without a user, SSH falls back to the caller's (root in CI containers) and fails.
- **Backup before migrate** into the backup volume (skipped on a first deploy), written to a temp file and renamed only on success so a failed dump never looks like a good one, rotated by a retention period; off-host copies come from the scheduled backup.
- **Verify** on the public URL by polling: readiness, and the health endpoint reporting the deployed version. **A single-replica Compose deploy is not zero-downtime:** behind Traefik the public URL can answer 404 for a few seconds after the switch. State the gap in the operations docs, or remove it with a second replica or a rolling update.
- **Every long-running service has a real healthcheck,** so `up --wait` gates on it. Never `healthcheck: disable`; Compose versions differ in how they treat services without one.
- **One deploy path:** every production operation (deploy, one-off management commands, admin creation) runs through the same script and credentials, preferably as a CI job. One-off commands run in the **running** version (`task deploy:manage ENV=production -- <cmd>`), never in whatever a local checkout pins. Admin accounts get no stored password: create them without one and set it through the password-reset mail.
- **Migrations stay backward compatible for one release**, so the previous image works against the new schema and rollbacks need no down-migrations.
- **SSH:** key-based, a dedicated deploy user (only the deploy key, in the `docker` group), known_hosts pinned in CI. **No connection multiplexing for Docker contexts** (`ControlMaster no`): Compose opens one SSH session per service and multiplexing runs into sshd `MaxSessions`; with separate connections `MaxStartups` (default `10:30:100`) is the limit, so the deploy script caps `COMPOSE_PARALLEL_LIMIT`. Check `sshd -T | grep -E 'maxsessions|maxstartups'` on a new server.
- Larger needs: Kamal is the closest step up for multi-host Docker deploys; avoid exposing self-hosted PaaS panels; Kubernetes only with a real platform team (and then pull-based GitOps).

## Rollback

- **Redeploy the previous release, on purpose, through CI** so it uses the CI credentials and leaves an entry in the environment history. With deploy-from-tag, re-running the older tag's deploy job **is** the deliberate act: it must not need a flag (a re-run usually cannot add variables), it logs that it is a rollback, and the verify step after it is the gate. Where the platform blocks outdated deploy jobs itself (GitLab), tag deploy jobs run with `ROLLBACK=1`; where it does not (GitHub), the deploy workflow's `rollback` input carries it.
- **The version guard never refuses because it cannot read the running version:** that is exactly when production is broken and a rollback is needed. It warns and continues.
- **From a laptop** (last resort): check out the previous tag, `task deploy ENV=production VERSION=<previous> ROLLBACK=1`. The explicit flag stays here.
- Restore the backup only for data problems; migrations stay backward compatible for one release.

## Release runbook

**Before the first CI deploy**
- Deploy user on each server: only the deploy key, in the `docker` group; SSH target with user and port in `deploy.env`.
- Preflight green from the CI deploy job context, e.g. from a prerelease tag pipeline.
- sshd limits checked; no SSH multiplexing for the Docker context.
- Deploy secrets protected and scoped per environment; host key pinned; release tags protected; production needs approval.
- The registry behind a reverse proxy has upload timeouts above the longest push (Traefik's default read timeout cuts at 60 s).

**Each release**
1. Release candidate green on main: checks, e2e, smoke test (same job image as the deploy).
2. Migrations of the release run against a restored recent production backup (`SMOKE_DUMP=... task release:smoke`, only where production data may be). Every migration that repoints a foreign key or deletes a model has a data step or a written decision to drop the data. Long gaps between releases pile up unreleased migrations: check them all.
3. Annotated tag on main; the pipeline validates, builds, smoke-tests, deploys staging.
4. Check staging; approve production. The deploy backs up, migrates, starts and verifies the version on the public URL.
5. Live checks: version, login, one core flow, one real mail end to end (password reset proves SMTP and links), error tracking, security headers, proxy logs.

**Failure triage (real error lines)**

| Error | Cause |
|-|-|
| `root@host: Permission denied (publickey,password)` | SSH user missing in the target, CI fell back to root |
| `ssh: connect to host ... port 22: Connection refused` | SSH port missing in the target |
| `unauthorized to access repository ... action: pull` | No registry credentials on the caller or the server |
| `resumable blob upload invalid`, `499` on push | Reverse-proxy read timeout in front of the registry |
| `ForeignKeyViolation ... is not present in table` during migrate | Migration not tested against existing data (runbook step 2) |
| `container ... has no healthcheck configured` from `up --wait` | Disabled healthcheck, or Compose version drift between smoke test and deploy |

## Production hardening

- Containers run as a fixed high UID, `cap_drop: [ALL]`, `security_opt: no-new-privileges`, `read_only: true` with `tmpfs: /tmp`; anything that writes files gets an explicit volume (e.g. uploads).
- Base images: Debian slim with the suite pinned on purpose (unsuffixed tags switch suites by themselves), and **pinned by digest** with the tag kept for readability (`FROM python:3.13-slim-trixie@sha256:...`): a floating tag can change twice a day and turn every build cold. Renovate (`docker:pinDigests`) or Dependabot opens the bump pull requests; where the same image is pinned in several files, a test keeps the copies in sync. Hardened images (distroless/DHI/Wolfi) are an option once the team has adapted healthchecks and debugging.
- PostgreSQL and Redis are not published to the host network; only the proxy faces the internet.

## Reverse proxy

TLS termination and routing per host (a registry or large uploads behind the proxy need an explicit read timeout; Traefik's default is 60 s): `/` → Django, `/v1/*` → realtime with immediate flushing for SSE and long read timeouts for streams. Locally and in CI a Caddy container per app mirrors these routes.

On servers: **one shared Traefik per server**, started once, owning the external `proxy` network; app stacks attach by labels and never run their own proxy. Reference setup with setup steps: `assets/traefik-host/` (Traefik behind a read-only Docker socket proxy, `exposedByDefault: false`, HTTP→HTTPS at the entrypoint, `aliasHeadersStrategy: delete`, compression that excludes `text/event-stream`, Mozilla-intermediate TLS, Let's Encrypt, dashboard behind basic auth). Rules for app stacks: router and service names unique per server (project + environment), only internet-facing services join `proxy`, no published ports in production, quoted label values. Caddy is an acceptable alternative where a team already runs it; the same rules apply.

**Request size limits:** the edge cap must fit the largest valid request, a multi-file upload, not the per-file limit. Set the app's own limit just below the edge limit, so users normally get the app's readable JSON 413 instead of the proxy's plain one. Traefik's buffering middleware also buffers responses, so downloads stop streaming: put it on a separate router that matches only requests with a body (`POST`, `PUT`, `PATCH`), with CrowdSec's bouncer before it.

## Observability baseline

- `/health` (liveness) and a readiness endpoint per service (database, Redis); used by container healthchecks.
- Logs to stdout, structured, with request or trace IDs; no secrets in logs.
- Errors to Sentry (or equivalent) for Django, the realtime service, Celery and the frontend, tagged with release (`APP_VERSION`) and environment.
- OpenTelemetry traces recommended across services and agent runs; configure exporters explicitly (auto-configuration defaults change between releases). Langfuse for LLM traces per `agentic-engineering`.

## Backups

- Scheduled `pg_dump -Fc` with retention, copied **off the host** encrypted (e.g. restic or object storage). A dump on the same machine is not a backup. Media and upload volumes are backed up too.
- Dumps are written to a temp file and renamed only on success. Retention is a data-protection matter: dumps keep personal data, deleted users included, for as long as they are kept.
- A restore test on a schedule (monthly), documented in `docs/operations.md`. The same restore feeds the release check of migrations against production data (runbook step 2).
- WAL archiving (pgBackRest, WAL-G) when the recovery point must be under a day or the database grows large.

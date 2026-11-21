# CI/CD, deployment and operations

The rules for building, releasing and running the app. Build once and the release from main: `build-once-and-release.md`. The scaffold's `docs/ci.md` and `docs/operations.md` show one implementation, with the platform settings and failure triage.

## Pipeline contract (platform-neutral)

| Stage | Task target | Runs on |
|-|-|-|
| Lint, docs, frontend, type check | `check:lint`, `check:docs`, `check:frontend`, `check:types` | every branch |
| Build | `release:build-ci` (production image and `test` stage, pushed by digest; skipped when the commit is tested) | every branch, first |
| Backend, end-to-end | `test:backend`, `test:e2e` (on the built images) | every branch, after the build |
| Mark tested | `release:mark-tested` | every branch, after all checks |
| Smoke | `release:smoke` (production images and settings behind a throwaway proxy) | main; release tags |
| Create release | `release:prepare` (validate, release notes; the platform creates the annotated tag) | main, manual |
| Validate, promote | `release:validate`, `release:await-tested`, `release:promote` | release tags |
| Deploy | `deploy:preflight`, then `deploy ENV=<env> VERSION=<tag>` | release tags, manual |

## Platform-neutral by construction

- **Logic lives in Task targets and scripts,** where a developer can run it; CI files hold only triggers, secrets, environments, approvals, concurrency and job images. A pre-commit check (`check_ci.py` in the scaffold) fails on anything else.
- **One variable switches where a target runs** (the compose stack locally, the job's own container in CI), never CI-only logic.
- **Scripts never read platform variables;** the CI file maps them to neutral names (`VERSION`, `REGISTRY`, `COMMIT`).
- **Platform features go in the mapping below,** not into the rules; another platform is one more column.

| Requirement | GitLab CI | GitHub Actions |
|-|-|-|
| One deploy per environment at a time | `resource_group` | `concurrency`, no cancel |
| An older release never overwrites a newer one by accident | Block outdated deploy jobs, allow deliberate retries | The deploy script refuses unless `rollback` is set |
| Deploy secrets and approval per environment | Manual deploy jobs on protected tags, variables protected and scoped to the environment; protected environments on higher tiers | Environments with required reviewers and environment secrets |
| Only maintainers create release tags | Protected tags (protected variables reach tag pipelines only through them) | Tag ruleset |
| Superseded runs cancelled; deploys never | `interruptible` on build and test jobs | `concurrency` with cancel on CI workflows only |
| Tests in the built images, databases as services | Job `image:` plus `services:` | `container:` plus `services:` |
| Third-party CI code pinned | Job images by digest or exact version | Actions by commit SHA |

## CI rules

- **Least privilege:** minimal token permissions, wider grants per job only where needed; OIDC over long-lived cloud credentials where available.
- **Optional manual jobs are allowed to fail,** or an unplayed one leaves the pipeline blocked.
- **Every image-building and deploy job has a timeout,** so a stuck push fails instead of holding the runner.
- **Order jobs by `needs:`, not by stages,** and run independent jobs side by side.
- **Tests run in the built images, not in Docker-in-Docker;** keep Docker-in-Docker for building images. An empty daemon per job pulls everything again.
- **The type checker runs in its own job with a cache keyed on the lockfile.**
- **Measure before optimising,** per job and per phase (pull, build, test, wait), cold and warm runner, and report each change against that baseline; the cost is often pulls, not tests.
- **CI works wherever its runner is:** deploys only over SSH, never a host Docker socket, host paths or shortcuts to production. A runner that shares a host with production is isolated, since privileged jobs are root on that host.
- **Docker and Compose versions are pinned exactly, in one place, and bumped like dependencies,** so the smoke test and the deploy run the same Compose.
- **Every tool CI downloads is pinned with its checksum, fetched with time limits, and mirrored,** so an outage of its source does not stop every pipeline. The mirror job runs on named integration branches, not on a "protected ref" condition that may be false there.
- **Supply chain, next step:** sign images and attach provenance, verify before deploy.

## Release

- **The version is the release tag;** the image does not carry it and the deploy sets it at runtime. No mutable `latest` for deployment.
- **Validate the tag first** (shape, annotated, newer than the newest release), so a bad tag fails in seconds.
- **Promote by digest** with a tool that keeps the digest (regctl or crane); some copy tools change single-platform digests.
- **Multi-platform images come from one build** pushing one multi-platform tag; platform-independent stages run on the build platform.
- **A local build from the CI bake file** overrides its outputs and caches so nothing is pushed.

## Deploy (single host)

- **Caller-driven over SSH:** a CI job (or, in an emergency, a laptop) decrypts secrets and drives the remote Docker daemon through a Docker context. The host holds no checkout, no decryption key and no env file.
- **The deploy uses the checkout at the release tag** (compose file and scripts must match the images) and names its version explicitly, never a default.
- **Sequence:** preflight → backup → pull → migrate as one-shot containers → admin command → up and wait for health → verify.
- **Preflight before anything changes:** SSH login as the deploy user, remote Docker, registry login on both ends, every image present in the registry the server pulls from, the version not older than the running one. Run it once before the first release, not first on release day. Inspect images with a tool that reports the real error.
- **Backups before migrate,** written to a temp file and renamed only on success, rotated.
- **Verify on the public URL** until readiness is ok and the reported version is the tag. A single-replica deploy is not zero-downtime; say so in the operations docs.
- **Every long-running service has a real healthcheck,** so the wait gates on it.
- **One deploy path:** deploys and one-off commands run through the same script and credentials, in the running version. A new command exists in production only once its release is deployed. The admin account: `security.md`, "Admin account".
- **Migrations stay backward compatible for one release,** so rollbacks need no down-migrations.
- **SSH:** a dedicated deploy user with only the deploy key, host keys pinned, a fresh `ssh-agent` per run with its output checked before use, no connection multiplexing for Docker contexts (sshd session limits).
- Larger needs: Kamal for multi-host Docker deploys; Kubernetes only with a platform team.

## Rollback

- **Redeploy the previous release on purpose, through CI:** re-running the older tag's deploy job is the deliberate act, needs no extra flag, is logged as a rollback and gated by verify.
- **The version guard never refuses because it cannot read the running version:** that is when production is broken.
- **From a laptop** only as a last resort, at the previous tag with an explicit rollback flag.
- Restore a backup only for data problems.

## Each release

- Migrations run against a recent production backup first, on the production host, never in CI; a migration that drops or repoints data has a data step or a written decision.
- Config changes ship with the release: compare the example env files with the previous release and apply the changes to every environment before the deploy. Better still, the app refuses a removed value at startup.
- After the deploy: version, login, one core flow, one real mail, error tracking, security headers, proxy logs.

## Production hardening

- Containers run as a fixed high UID, without capabilities or privilege escalation, with a read-only root filesystem and explicit volumes for anything that writes. Find every write path before going read-only.
- Postgres and Redis images need back the few capabilities they use to drop root; prove it with the smoke test.
- Base images are pinned by suite and digest and bumped by a bot; every copy of a pin is kept in sync by a test, with no unproven exemptions.
- Image users and groups are consistent, there is no sudo, and Dockerfile syntax lines are current or absent.
- Databases are not published; only the proxy faces the internet.

## Reverse proxy

- **One shared Traefik per server** owns the external network; app stacks attach by labels and never run their own proxy (reference setup: `assets/traefik-host/`). Router names are unique per project and environment.
- `/` goes to Django, `/v1/*` to the realtime service with immediate flushing for streams; locally and in CI a Caddy container mirrors these routes.
- **Request size limits:** the edge cap fits the largest valid request; the app's own limit sits just below it, so users get the app's readable error. Body buffering applies only to requests with a body, so downloads keep streaming.

## Observability baseline

- Liveness and readiness per service; readiness bounds each check and names the failed one.
- Structured logs to stdout regardless of `DEBUG`, with request or trace IDs and no secrets.
- Errors to Sentry (or equivalent) for every service and the frontend, tagged with release and environment; SDK integrations enabled explicitly, without PII.
- OpenTelemetry traces across services and agent runs, exporters configured explicitly; Langfuse for LLM traces per `agentic-engineering`.

## Backups

- Scheduled dumps with retention, copied off the host encrypted; media volumes too. A dump on the same machine is not a backup.
- Dumps keep personal data, deleted users included: retention is a data-protection decision.
- A scheduled restore test; the same restore feeds the migration rehearsal.
- WAL archiving when the recovery point must be under a day.

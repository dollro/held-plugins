# CI and releases (GitLab)

How this repo's GitLab pipeline builds once, tests that image and releases it. The rules behind it are in the `fullstack-engineering` skill; this page is the implementation and its settings. Every job calls a Task target (`Taskfile.yml`); `scripts/check_ci.py` keeps the CI files thin.

## Pipelines

| Pipeline | Jobs |
|-|-|
| Branch (every push) | `lint`, `docs`, `frontend`; `build_images` → `test_backend`, `test_e2e`, `typecheck` → `mark_tested`; on main also `smoke` and the manual `create_release` |
| Release tag (`1.8`, `1.8.1`) | `validate_release` → `await_tested` → `rebuild_untested` (child, a no-op when tested) → `promote_tested` → `smoke_release` → manual `deploy_preflight` → manual `deploy_production` |
| Prerelease tag (`1.8a1`, `1.8-rc1`) | the same up to `deploy_preflight`; never deploys |

Jobs are ordered by `needs:`, not by stages; build and test jobs are interruptible (a newer push cancels them), deploy jobs never.

## Images and tags

| Tag | What | Written by |
|-|-|-|
| `<project>-<service>:<sha>` | Production image of the commit | `build_images` |
| `<project>-django:test-<sha>` | Stage `test`: the production django image plus dev dependencies; never deployed | `build_images` |
| `tested-<sha>`, `test-tested-<sha>` | The digests every test job ran, after all passed | `mark_tested` |
| `<version>` | Same digest as `tested-<sha>` | `promote_tested` |
| `cache-<branch>-<stage>`, `cache-tested-<sha>-<stage>` | Registry build cache | `build_images`, `mark_tested` |

- **Digests, not tags:** two pipelines building the same commit push different digests under `:<sha>`. `build_images` records what it pushed (`images.env`), test jobs run those digests and report them (`ran-*.env`), and `mark_tested` refuses unless all reports match (`scripts/ci/tested_images.sh`).
- **Reuse:** a commit that already has `tested-<sha>` is not rebuilt; its tested digests are recorded instead (develop or main fast-forwarded to a tested branch).
- **The version is not in the image:** the deploy sets `APP_VERSION` from the tag; images carry only `GIT_SHA`.

## Build cache

- Each branch reads its own cache, then develop's and main's, and writes only its own (`docker-bake.hcl`, `mode=max`).
- A reused commit builds nothing, so it would never write the integration branch's cache. `mark_tested` therefore pins the cache of the tested build as `cache-tested-<sha>-<stage>`, and the reuse path on develop and main copies it to `cache-<branch>-<stage>`.
- A missing cache never fails a job; it only makes a build slower. After a change to the build layout every branch builds cold until develop has built once.

## Tests in the built images

`task test:backend` and `task test:e2e` take `STACK=compose` (default, the dev stack) or `STACK=job` (CI):

- `test_backend` and `typecheck` run in the test image by digest from `/app` (the image's code, not the checkout), Postgres and Redis as services.
- `test_e2e` runs in the Playwright image; the app runs as services from the production images by digest, Caddy and the specs run in the job (`scripts/e2e_job.sh`).
- Pitfalls handled: per-commit digests (a cached mutable tag would stand in for a new image), app services never read the checkout (services start before the clone), tools for non-root images come from `build_images` as artifacts in `.cache/bin`, writing to the checkout needs a runner umask that allows it.
- `docs` and `frontend` still use the compose stack in Docker-in-Docker. Moving them to plain uv/node job images saves the image pulls; do it when that keeps the CI file as short as it is now.

## Type checking

`task check:types` runs mypy against `mypy-baseline.txt`: new errors fail, and so do fixed errors still in the baseline (`task check:types:sync` after fixing, on the merged tree). `lint` runs `task check:types:baseline`, which fails when the baseline grew against the merge base with main (`ALLOW_GROWTH=1` for a deliberate exception). The mypy cache is keyed on `uv.lock`.

## Releases

- `create_release` (manual, main, after `mark_tested` and `smoke`): play it with `RELEASE_VERSION=1.8`. `scripts/release.sh prepare` checks the shape, that the tag is new and newer than the newest release, and that the commit contains the newest release (the job stays playable in old pipelines), then GitLab creates the annotated tag and release on that commit.
- Fast-forward main to the tested develop where possible: a merge commit is a new SHA and is built and tested again.
- A tag pushed by hand works too: `await_tested` waits for `tested-<sha>` (`AWAIT_TESTED_TIMEOUT`, 30 min), then the child pipeline builds and tests the commit.
- Rollback: retry `deploy_production` in the older tag's pipeline. Retrying it in the running tag's pipeline redeploys that tag (e.g. to apply a changed admin password).
- **Staging** is an extension: add a `deploy_staging` job before `deploy_production` that runs `task deploy ENV=staging VERSION="$VERSION"`, with its own environment and variables.

## GitLab project settings

- **Repository > Protected tags:** `*`, Maintainers. Only maintainers create releases, and protected variables reach tag pipelines only through it (without it the preflight lists every deploy variable as missing).
- **Settings > CI/CD > Variables**, protected and scoped to `production`: `SOPS_AGE_KEY`, `DEPLOY_SSH_KEY` and `DEPLOY_KNOWN_HOSTS` (file variables).
- **Settings > CI/CD > General pipelines:** "Prevent outdated deployment jobs" on, with "Allow job retries for rollback deployments".
- **Approval** is the manual deploy job on a protected tag. On Premium, protect the `production` environment with required approvers as well.
- **Deploy > Container registry > Cleanup policy**, daily: delete after 7 days `^(test-|tested-|test-tested-)?[0-9a-f]{40}$|^cache-.+$`; keep `^(cache-(develop|main)-.+|[0-9]+\.[0-9]+.*)$` plus the newest few. Without the keep pattern the policy deletes releases and the rollback path.
- **Package registry** enabled (default): `mirror-tools` mirrors the pinned CI tools there on develop, main and tags.

## Measuring

Before speeding the pipeline up, record each job's duration and queue time (Build > Jobs, or the jobs API) for a cold and a warm runner, split slow jobs into pull, build, test and wait from the log timestamps, and report the same table after the change.

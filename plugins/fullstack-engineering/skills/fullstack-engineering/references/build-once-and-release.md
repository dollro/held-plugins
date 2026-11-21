# Build once and release from main

The default CI and release workflow: every commit is built once, the tests run on that exact image, and a release copies the tested digest to the version tag. Nothing is built in the tag pipeline unless the commit was never tested. Platform terms below are GitLab's (Free tier is enough); the GitHub column of the mapping table in `ci-cd-and-deploy.md` covers the equivalents.

Example names: images `registry.example.com/acme/atlas-<service>`, release `1.8`.

## Why

- Tests on a development image and a separate production build mean production runs an image no test has seen. Production-only bugs (static files, settings, permissions) then surface on release day.
- A tag pipeline that rebuilds is slow (10+ minutes) and ships something new. A copy of a tested digest takes seconds.
- Trade-off, chosen on purpose: branch pipelines get slower (the production build sits on the critical path), release pipelines get much faster and ship what was tested.

## Images and tags

| Tag | What | Written by |
|-|-|-|
| `atlas-<service>:<sha>` | The production image of the commit | `build_images` (branch pipeline) |
| `atlas-app:test-<sha>` | Stage `test`: `FROM production` plus test and dev dependencies; never promoted | `build_images`, same bake run |
| `atlas-<service>:tested-<sha>` | The digest that every test job ran, after all passed | `mark_tested` |
| `atlas-app:test-tested-<sha>` | The test image of that build; lets a later pipeline of the same commit skip the build | `mark_tested` |
| `atlas-<service>:<version>` | Same manifest as `tested-<sha>` (digest checked) | `promote_tested` (tag pipeline) |

## Branch pipeline: build, test, mark

1. **Build once.** One `docker buildx bake` run builds the production image and the `test` stage on top of it, so the shared layers are built once and are byte-identical. It pushes `:<sha>` and `:test-<sha>` and writes the pushed digests (`bake --metadata-file`) into a dotenv report (`images.env`: `DIGEST_APP`, `DIGEST_APP_TEST`, ...).
2. **Test the image, by digest.** Test jobs use `image: $IMAGE@$DIGEST_APP_TEST` (dotenv variables from `needs:` work in `image:` and `services:`), Postgres and Redis as `services:`, and run from the image's app directory (`cd /app`), not from the checkout: GitLab starts every job in the fresh clone, so a plain `pytest` would test the checkout. End-to-end runs the app image as a service.
3. **Each test job reports what it ran.** It ends by writing the digests it actually ran (`ran-test.env`, `ran-e2e.env`, artifacts). GitLab retries a job without its dependents, so after a retried build a retried test job can pass on new digests while another passed on the old ones.
4. **`mark_tested`** copies `<image>@<recorded digest>` to `tested-<sha>`, only if every `ran-*.env` names exactly the digests it marks. Never copy by tag: two pipelines building the same SHA (a branch pushed at an existing SHA, a retried build, develop and main after a fast-forward) push different digests under the same `:<sha>`, because builds are not bit-reproducible.
5. **Reuse when tested.** `build_images` first checks `tested-<sha>` and `test-tested-<sha>`; if both exist it records their digests and builds nothing. The integration branch (develop, main) fast-forwarded to a commit a branch already tested costs about a minute.

Rules that keep this correct:

- **Per-commit tags, never a mutable branch tag** for test images. The runner pulls `if-not-present`; a cached `test-develop` would let an old image stand in. The runner's cache may make a job fast, never decide what is tested.
- **A `test` stage branches off the final production stage**, not an earlier shared one; otherwise it drifts. The shipped image carries no test tools.
- **The version is not in the image** (next section), so a release needs no rebuild and the bundle does not change on every tag.

## Version identity

- **The version is the release tag,** nothing else. No version file, no bump commit; `deploy.env` holds only the target.
- **The image exists before the tag,** so the version cannot be baked in: no `APP_VERSION` build argument that wins at runtime, no `org.opencontainers.image.version` label (a copy cannot change labels without changing the digest), no `VITE_*` version (replaced at build time). The image carries only the commit SHA as fallback.
- **The deploy sets `APP_VERSION`** from the tag (compose `${APP_VERSION:?}`), the backend reports it at `/version` and in error reports, the frontend asks the backend.
- Before removing a baked value, find every consumer of it (scripts that read a label to decide where `:latest` points).
- Proof: start one image twice with two `APP_VERSION` values and check both are reported; the smoke test checks the version too.

## Release from main

The release is created from the pipeline that tested the commit, so the tag pipeline finds tested images at once.

- **`create_release`:** manual job on main, `needs: [mark_tested]`, `allow_failure: true` in its rule (an unplayed manual job otherwise leaves every main pipeline "blocked"). Played with the job variable `RELEASE_VERSION=1.8`. It:
  1. validates the shape and that the version is newer than the newest release and not taken yet;
  2. refuses a commit that does not contain the newest release (`git merge-base --is-ancestor <newest> $CI_COMMIT_SHA`): the job stays playable in older main pipelines, and releasing one would roll production back;
  3. writes release notes (commits since the previous release; `GIT_DEPTH: 0`);
  4. creates release and tag with GitLab's `release:` keyword and the job token: `tag_name: $RELEASE_VERSION`, `tag_message` (makes the tag annotated), `ref: $CI_COMMIT_SHA`, `description: ./release-notes.md`. Image: the official `gitlab-org/cli` pinned by digest (ships git, no entrypoint).
- **Fast-forward main when it has not diverged.** A merge commit is a new SHA, so build once cannot reuse develop's tested build and the release waits for a full build and test of the merge commit. After a merge commit, merge main back into develop so the next release can fast-forward.
- **Hand-pushed tags still work** (an older commit, an outage); the tag pipeline then waits or rebuilds.
- GitHub: a `workflow_dispatch` workflow that creates the release on the tested SHA.

## Tag pipeline

| Job | Does | Notes |
|-|-|-|
| `validate_release` | Shape, annotated, not older than the newest release | Fails in seconds, first stage, `GIT_DEPTH: 0` |
| `await_tested` | Polls the registry for `tested-<sha>` of every service, with a timeout (e.g. 30 min); writes the child pipeline config as an artifact | A registry read error (auth, outage) fails after a few tries instead of counting as "not tested yet" |
| `rebuild_untested` | Triggers the generated child: a no-op job when tested, else build + test + mark (the branch jobs, included from a shared file) | `strategy: mirror`; `inherit: variables: [...]` |
| `promote_tested` | Copies `tested-<sha>` to `<version>`, checks the digests match | Registry calls only (regctl or crane), no Docker-in-Docker |
| `deploy_preflight` | Read-only checks (`ci-cd-and-deploy.md`, Deploy) | Own job, manual, **blocking**; `environment: action: verify` |
| `deploy_production` | Deploys the pipeline's tag, `needs: [promote_tested, deploy_preflight]` | Manual, blocking, `resource_group: production`; release tags only |
| `deploy_admin` | Runs the admin command (below) without a release; every deploy runs it anyway | Optional, manual, `allow_failure: true`, `needs: [deploy_production]`, `environment: action: access` |

- **Prerelease tags** (`1.8a1`, `1.8-rc1`, or `v1.8.0-rc.1`) run validate, await, promote and only the preflight: a safe way to prove protected variables and SSH in a tag pipeline before the first real release.
- **Tag shape is a project choice:** `X.Y`/`X.Y.Z` or `vX.Y.Z`. Pick one and never mix them; version sorting (`sort -V`) and protected tag patterns depend on it.
- **Staging is optional.** With staging, a `deploy_staging` job runs before `deploy_production` on the same tag and images; production-only is a valid setup where the smoke test and preflight are the last gates.
- **The deploy job checks its version equals the tag** and refuses anything else.
- **Verify after deploy:** poll the public URL until `/health/ready` answers ok and `/version` equals the deployed tag; the job fails otherwise. The log ends with one line naming URL and version.

## Approval and protection (GitLab Free default)

- **Protected tags** with `*` or the release pattern (GitLab supports only `*` as wildcard: `v[0-9]*` matches nothing). Only maintainers create tags; the job token of `create_release` acts as the person who played it.
- **Protected variables reach only protected refs:** without protected tags the tag pipeline gets none of the deploy variables and the preflight lists all as missing. A project that used to deploy from a protected branch finds out on its first tag deploy; check the protected tags list before it. Protection is checked when a job runs: after adding it, retry the failed job, no new tag needed.
- **Approval = manual jobs** on protected tags, plus "Prevent outdated deployment jobs" and "Allow job retries for rollback deployments".
- Protected environments with required approvers are the Premium option; use them where available, not as a requirement.
- **Admin account, env is the source of truth:** one idempotent command (e.g. `ensure_admin`) runs on **every** deploy of every environment (production, and staging where it exists) after migrate (when the admin email is set), on every local dev stack start, and from an optional manual admin job (`environment: action: access`) to apply a change without a release. Dev, staging and production use the same command and env keys. The admin email is required; `DJANGO_SUPERUSER_PASSWORD` (masked, protected CI variable or env file) is optional:
  - **Set:** a new admin gets it; an existing admin whose password differs is updated to it, so a changed variable takes effect on the next deploy or start. An unchanged password keeps its hash (`check_password` first), so sessions survive. It must pass Django's password validators and is never printed.
  - **Unset:** a new admin gets an unusable password and the owner sets one through password reset (the safer default where production mail works: no admin password stored anywhere); an existing admin's password is left alone.
  - An existing non-admin with that email is never promoted.
  - A weak password, an existing non-admin with that email or a username clash fails the command, on purpose: on a deploy it runs after migrate and before `up`, so the deploy stops and the previous release keeps serving; on a dev start it stops the container. The log names the reason, never the password.

## Build cache

- **Cache refs per branch:** `cache-<ref>-<stage>` (`<ref>` = branch slug), `mode=max` (two targets; `mode=min` caches only the final stage). `cache-from` the branch's own ref, then develop's; `cache-to` only the own ref. Never per-commit cache refs: they always miss and fill the registry. A tag's rebuild child uses main's.
- **A reused tested commit never writes the integration branch's cache.** develop fast-forwarded to tested commits skips the build, so `cache-develop-*` goes stale and every new branch builds cold. Fix, the cache follows the images:
  1. `build_images` records the digests of the cache refs it exported into `images.env` (read right after the bake; the metadata file does not name the cache).
  2. `mark_tested` pins them as `cache-tested-<sha>-<stage>`.
  3. The reuse path on develop and main copies `cache-tested-<sha>-*` to `cache-<ref>-*` (regctl or crane manifest copy, no build).
- **A missing cache never fails a job.** Every cache step logs and continues; the worst case is a slower build. A cache-layout change makes everything cold until the integration branch has really built once; size build timeouts for that.

## Registry cleanup

Per-commit tags pile up (several per commit and repository). A daily cleanup policy, changed together with its docs:

- **Delete** after N days (e.g. 7): `^(test-|tested-|test-tested-)?[0-9a-f]{40}$|^cache-.+$|^scratch-.+$`
- **Keep always:** `^(cache-(develop|main)-.+|v?[0-9]+\.[0-9]+.*)$` (releases, integration-branch caches), plus the newest few per repository.
- A policy without an explicit release keep pattern deletes release tags and with them the rollback path. Check it before relying on old tags.
- Consequences to accept: a tag of a commit older than N days takes the rebuild path; `cache-tested-*` pins match `^cache-` too, so a commit reaching develop after N days leaves develop's cache as it was (slower, never wrong).
- Immutable tags need a higher tier; promotion by digest makes them unnecessary.

## Laptop fallback

`task deploy VERSION=<tag>` from a checkout of that tag (`git switch --detach <tag>`), same script as CI. The script checks that `HEAD` is the tag (compose file and scripts must match the images) and that the version is not older than the live one, unless an explicit override is set; in CI, retrying an older tag's deploy job is itself the deliberate rollback.

## GitLab pitfalls

- **No cross-pipeline wait:** `needs:pipeline` works only inside a parent/child tree, `needs:project` fetches artifacts but does not wait. The registry is the shared state; polling holds a runner slot, so prefer releasing from the tested pipeline.
- **Runtime path choice needs a generated child pipeline:** dotenv variables cannot be used in `rules:`. A job writes the child config as an artifact; a trigger job includes it with `strategy: mirror` (the trigger fails when the child fails). A child needs at least one job, so the "tested" path is a no-op job.
- **Trigger jobs forward variables that beat the child's job variables.** A global `DOCKER_TLS_CERTDIR: ""` overrode the build job's `/certs` and the child's Docker-in-Docker client missed its daemon. List what the child needs with `inherit: variables: [...]`.
- **Services start before the checkout** but see `/builds`; a service that reads code from it can start on a previous job's files. Running services from the image removes the problem.
- **Non-root job images** cannot install tools to `/usr/local/bin`: install into a directory in the checkout and put it on `PATH`.

## Runner-location agnostic

The pipeline works unchanged on a cold runner and on a runner on another host: deploys only over SSH, no host Docker socket, no host paths or volumes, no `localhost` shortcuts to production. The runner's image cache only saves pulls. Done means one green pipeline on a cold runner.

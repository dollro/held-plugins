# Build once and release from main

The default CI and release workflow: every commit is built once, the tests run on that exact image, and a release copies the tested digest to the version tag. The scaffold's `docs/ci.md` shows one implementation on GitLab (Free tier is enough); the mapping table in `ci-cd-and-deploy.md` names the platform equivalents.

## Why

- Testing a development image and shipping a separate production build means production runs an image no test has seen; production-only bugs then surface on release day.
- A tag pipeline that rebuilds is slow and ships something new; copying a tested digest takes seconds. The price, chosen on purpose: branch pipelines carry the production build on their critical path.

## Rules

- **Build once per commit:** one build produces the production image and a `test` stage `FROM` the final production stage, so every shipped layer is the tested layer and the shipped image carries no test tools.
- **Test by digest, never by tag:** two builds of the same commit push different digests under the same tag. Test jobs run the digests the build recorded, report what they ran, and the image is marked tested only if every report matches.
- **Per-commit tags, never a mutable branch tag** for images under test: a runner's cached image must never decide what is tested.
- **Reuse a tested commit:** a pipeline for a commit that is already marked tested builds nothing, which makes fast-forwarding the integration branches cheap.
- **Mark only after every check passed,** including lint and the type check, so "tested" means releasable.

## Version identity

- **The version is the release tag,** nothing else: no version file, no bump commit.
- **The image exists before its tag,** so the version is not baked in (no build argument, label or bundle constant). The deploy sets it at runtime and the app reports it; the image carries only its commit as a fallback. Before removing a baked value, find every consumer of it.

## Release from main

- **Release from the pipeline that tested the commit:** a manual job on main, after the commit is marked tested, validates the version and creates the annotated tag on that commit. It refuses a commit that does not contain the newest release, because the job stays playable in old pipelines.
- **The tag pipeline promotes, it does not build:** validate the tag, wait for the tested mark (an untested commit is built and tested first, or the pipeline fails loudly), copy the tested digests to the version, smoke-test, then manual preflight and deploy jobs. A prerelease tag stops after the read-only preflight.
- **One tag shape per project** (`X.Y` or `vX.Y.Z`), never mixed: version sorting and protected tag patterns depend on it.
- **Fast-forward the release branch when it has not diverged:** a merge commit is a new SHA and has to be built and tested again.
- **Staging is optional:** where it exists, it deploys the same tag and images before production; without it, the smoke test and the preflight are the last gates.
- **Verify after deploy:** readiness ok and the reported version equal to the tag, polled on the public URL.

## Approval and protection

- **Only maintainers create release tags** (protected tags). On GitLab, protected variables reach a tag pipeline only through a protected tag pattern: without it every deploy variable is missing.
- **Approval is a manual deploy job on a protected tag,** with outdated deploy jobs blocked and deliberate rollbacks allowed. Protected environments with required approvers are an addition where the tier has them, not a requirement.
- **The admin account follows the environment on every deploy:** `security.md`, "Admin account".

## Build cache

- **Cache per branch with a fallback to the integration branch, never per commit:** a new branch starts warm, and per-commit refs always miss and fill the registry.
- **A reused commit must still keep the integration branch's cache warm,** otherwise branches fast-forwarded into it build cold forever; pin the cache of the tested build and copy it on reuse.
- **A missing cache never fails a job;** it only makes a build slower.
- **Build steps that stay fast on an empty builder:** dependencies before code, no recursive ownership changes over dependency trees, build output cleaned in the same layer, no floating fetches in a Dockerfile.

## Registry cleanup

Per-commit tags pile up, so a scheduled cleanup policy is part of the setup. It must explicitly keep release tags and the integration branches' caches: a policy without them deletes the rollback path.

## Runner-location agnostic

The pipeline works unchanged on a cold runner and on a runner on another host: deploys only over SSH, no host Docker socket, no host paths, no shortcuts to production. The runner's cache only saves pulls. Done means one green pipeline on a cold runner.

## Platform notes (GitLab)

- **A pipeline cannot wait for another:** the registry is the shared state, and polling holds a runner slot, so prefer releasing from the tested pipeline.
- **A decision that depends on a job's output needs a child pipeline,** because `rules:` cannot read job output in the same pipeline. Keep it to one, with a comment saying why.
- **Variables forwarded to a child pipeline beat its own job variables;** forward only what the child needs.

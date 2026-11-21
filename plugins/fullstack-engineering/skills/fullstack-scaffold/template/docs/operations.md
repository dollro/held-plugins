# Operations

Servers, releases, deploys, rollback, backups. Every command here is a Task target; CI calls the same targets.

## Server setup

Once per server (staging and production may share one):

1. **Shared Traefik:** one per server, owning the external `proxy` network, TLS and Let's Encrypt (reference setup: `assets/traefik-host/` in the `fullstack-engineering` skill). App stacks never run their own proxy. If a registry or large uploads go through it, its `websecure` read timeout must exceed the longest upload (Traefik's default is 60 s).
2. **Deploy user:** a dedicated user with only the deploy key in `authorized_keys`, in the `docker` group. Put it in `DEPLOY_SSH_TARGET=ssh://<user>@<host>[:<port>]` in `.envs/<env>/deploy.env`; without a user, SSH falls back to the caller's (root in CI) and fails.
3. **SSH limits:** Docker contexts open one SSH session per service. Do not use connection multiplexing (`ControlMaster`) for the deploy host; check `sshd -T | grep -E 'maxsessions|maxstartups'`.
4. **DNS:** the app hosts point to the server; only ports 80 and 443 are open.
5. **Container logs** limited on the host (`/etc/docker/daemon.json`, `json-file` with `max-size`).
6. **CI works wherever its runner is:** deploys only over SSH, no Docker socket, host paths or localhost shortcuts into this server. If a runner shares the host with production, isolate it: no privileged jobs, protected runners for jobs with secrets, CPU and memory caps, never this server's Docker socket.
7. **Preflight** from the CI deploy context once the first images exist: `task deploy:preflight ENV=production VERSION=<tag>` (SSH login, remote Docker, registry login, images present, registry matches the release).<!-- >>> gitlab --> In CI: push a prerelease tag (e.g. a release candidate of the first version); its pipeline runs up to `deploy_preflight` and proves protected variables and SSH without deploying.<!-- <<< gitlab -->

CI settings per platform (protected release tags `__PROTECTED_TAG_PATTERN__`, environments `staging` and `production` with their own `SOPS_AGE_KEY`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, approval for production): see the header comments of the CI files.

**CI tools** (Task, sops, Compose, regctl, Caddy) are pinned with their SHA-256 in `scripts/ci/tools.txt` and installed by `scripts/ci/install-tools.sh`: mirror first, then the original source, hash checked either way. The `mirror-tools` job copies missing versions into the mirror on protected branches (GitLab: the project's generic package registry; GitHub: the store in `TOOL_MIRROR_URL`, if set). Bump a tool with `scripts/ci/pin-tool.sh <name> <version>` after reading its release notes; the first pipeline on a protected branch mirrors it.

## Release

The version is the release tag, shape `__VERSION_EXAMPLE__` (`scripts/release.sh`), and nothing else: no version file, no bump commit. Images exist before their tag, so the version is not baked in; the deploy sets `APP_VERSION` and `/api/v1/version/` reports it.
<!-- >>> gitlab -->

**Build once (GitLab).** Every branch commit is built once (`build_images`: production images and the `test` stage on top of them, pushed as `<sha>`), backend and end-to-end tests run on exactly those digests, and `mark_tested` tags them `tested-<sha>`. A commit tested before (develop or main fast-forwarded to it) is reused, not rebuilt. A release copies `tested-<sha>` to the version tag: what ships is what was tested.

1. **Candidate green on `main`:** checks, tests, `mark_tested` and the smoke test (`task release:smoke`: the tested images with production settings behind a throwaway Traefik). Fast-forward `main` to the tested `develop` where possible: a merge commit is a new SHA and is built and tested again.
2. **Migrations on real data:** restore a recent production backup into the smoke stack and migrate on top of it, only where production data may be: `SMOKE_DUMP=<file.dump> task release:smoke`. A migration that repoints a foreign key or deletes a model needs a data step or a written decision to drop the data. Diff the `.example` env files against the previous release and apply changed values to each environment.
3. **Create the release:** in `main`'s pipeline play `create_release` with the job variable `RELEASE_VERSION=__VERSION_EXAMPLE__`. It checks the shape, that the version is new and newer than the newest release, and that the commit contains the newest release, then creates the release and its annotated tag on the tested commit. (A tag pushed by hand works too; its pipeline waits for `tested-<sha>`, or builds and tests the commit in a child pipeline.)
4. **Tag pipeline:** `validate_release` → `await_tested` → `promote_tested` (copy by digest, no build) → `smoke_release` → `deploy_preflight` (manual)<!-- >>> staging --> → `deploy_staging`<!-- <<< staging --> → `deploy_production` (manual). Prerelease tags stop after the preflight.
5. **Live checks:** version on `/api/v1/version/`, login, one core flow, one real password-reset mail end to end, error tracking, security headers, proxy logs.
<!-- <<< gitlab -->
<!-- >>> github -->

**GitHub:**

1. **Candidate green on `main`:** checks, end-to-end, production smoke test (`task release:smoke`).
2. **Migrations on real data:** `SMOKE_DUMP=<file.dump> task release:smoke`, only where production data may be.
3. **Tag:** `git tag -a __VERSION_EXAMPLE__ -m "..." && git push origin __VERSION_EXAMPLE__`. The release workflow validates the tag, builds and pushes the images, smoke-tests them and deploys to staging; approve production in CI.
4. **Live checks:** version on `/api/v1/version/`, login, one core flow, one real password-reset mail end to end, error tracking, security headers, proxy logs.
<!-- <<< github -->

Each deploy runs `task deploy ENV=<env> VERSION=<tag>`: preflight → backup → pull → migrate → admin (`ensure_admin`, when `DJANGO_SUPERUSER_EMAIL` is set) → up (waits for healthy) → verify (polls `/api/v1/health/ready/` and `/api/v1/version/` on the public URL until it reports the tag). The CI platform's environment history records what runs.

## Rollback

Redeploy the previous release on purpose, through CI so it uses the CI credentials and shows in the environment history:

<!-- >>> gitlab -->
- **GitLab:** re-run the production deploy job of the previous tag's pipeline. "Prevent outdated deployment jobs" stops stale pipelines; the explicit re-run is allowed and logged as a rollback.
<!-- <<< gitlab -->
<!-- >>> github -->
- **GitHub:** run the `deploy` workflow with the previous version and `rollback` checked.
<!-- <<< github -->

As a last resort from a laptop, at the previous tag (the compose file comes from the checkout):

```bash
git switch --detach <previous tag>
task deploy ENV=production VERSION=<previous tag> ROLLBACK=1
```

Outside a rollback, the deploy refuses a version older than the running one. It never refuses because the running version cannot be read (that is when production is broken); the verify step after the deploy is the gate. Migrations stay backward compatible for one release, so a rollback needs no restore; restore a backup only for data problems.

**Brief 404 during a deploy:** with one replica per service behind Traefik, the public URL can answer 404 for a few seconds while containers are replaced; verify polls for that reason. Zero downtime needs a second replica or a rolling update.
<!-- >>> gitlab -->

## Registry cleanup

Build once leaves several tags per commit (`<sha>`, `test-<sha>`, `tested-<sha>`, `test-tested-<sha>`, `cache-tested-<sha>-<stage>`) and per-branch caches (`cache-<branch>-<stage>`). Set a daily cleanup policy (Deploy > Container registry), and change it together with this section:

- **Delete** after 7 days: `^(test-|tested-|test-tested-)?[0-9a-f]{40}$|^cache-.+$`
- **Keep always:** `^(cache-(develop|main)-.+|v?[0-9]+\.[0-9]+.*)$` (releases and the integration branches' caches), plus the newest few per repository.

A policy without the release keep pattern deletes release tags and with them the rollback path. A tag on a commit older than the delete window takes the rebuild path; a missing cache only makes a build slower.
<!-- <<< gitlab -->

## Day to day

```bash
task deploy:version ENV=production          # requested and running version
task deploy:ps ENV=production
task deploy:logs ENV=production -- django
task deploy:manage ENV=production -- shell  # one-off command in the running version
task deploy:backup ENV=production
```

**Admin account, the env is the source of truth.** `ensure_admin` runs after migrate on every deploy, on every start of the local stack, and on demand (`task deploy:admin ENV=production`<!-- >>> gitlab -->, or the manual `deploy_admin` job of the running release<!-- <<< gitlab -->). Dev, staging and production use the same keys in their env files:

- `DJANGO_SUPERUSER_EMAIL` (required for the admin; unset: no admin is managed).
- `DJANGO_SUPERUSER_PASSWORD` (optional). Set: a new admin gets it, and an existing admin whose password differs is updated on the next deploy or start; an unchanged password keeps its hash, so sessions survive. It must pass the password validators and is never printed. Unset: a new admin gets an unusable password and sets one through the password-reset mail (nothing stored anywhere; the safer default once production mail works); an existing admin's password is left alone.
- An existing non-admin account with that email is never promoted: the command fails and names it.
- **Failing is intended:** a weak password, an existing non-admin with that email or a username clash fails `ensure_admin`. On a deploy it runs after migrate and before `up`, so the deploy stops and the previous release keeps serving (with the new schema, which stays backward compatible); fix the env file and deploy again. On a dev start it stops the django container (`task dev:logs -- django` names the reason).
- **Quote secrets** in env files with single quotes (`DJANGO_SUPERUSER_PASSWORD='...'`, the database password): Compose expands `$` and cuts at ` #` in env files. Inside `DATABASE_URL` and `EMAIL_URL` they are URL-encoded instead.

Further admins: create them without a password and let them set one through the password-reset mail (not `createsuperuser --noinput`: it would take `DJANGO_SUPERUSER_PASSWORD` from the container environment):

```bash
task deploy:manage ENV=production -- shell -c \
  "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@example.com')"
```

## Backups

- Each deploy dumps the database into the `postgres_backups` volume before migrating (`task deploy:backup` does the same on demand). The dump goes to a temp file renamed only on success, so a failed dump never looks like a good one, and dumps older than `BACKUP_RETENTION_DAYS` (default 14) are deleted: they hold personal data, deleted users included.
- A scheduled job copies dumps and the upload/media volumes **off the server**, encrypted (restic or object storage), with retention. A dump on the same machine is not a backup.
- Restore test monthly, into a throwaway stack (`SMOKE_DUMP=... task release:smoke` proves the dump restores and migrates).
<!-- >>> sso -->

## Single sign-on

Company login over OpenID Connect (Entra ID as example). Register the app with the identity provider (Entra: ask IT for an app registration):

- **Redirect URI** per environment: `https://<APP_HOST>/accounts/oidc/<SSO_PROVIDER_ID>/login/callback/` (`SSO_PROVIDER_ID` defaults to `company`). Staging has its own registration or redirect URI, never production credentials.
- **Values** in `.envs/<env>/app.env.enc`: `SSO_ISSUER_URL` (Entra: `https://login.microsoftonline.com/<tenant-id>/v2.0`), `SSO_CLIENT_ID`, `SSO_CLIENT_SECRET`, `SSO_VERIFIED_EMAIL_DOMAINS` (the company's managed mail domains), `SSO_DISPLAY_NAME`, `SSO_AUTO_PROVISION`.
- SSO is active only when issuer, client ID and secret are set; its routes do not exist otherwise.
- **Client secrets expire:** note the expiry date and rotate before it (`task secrets:edit ENV=<env>`, then deploy).
<!-- <<< sso -->

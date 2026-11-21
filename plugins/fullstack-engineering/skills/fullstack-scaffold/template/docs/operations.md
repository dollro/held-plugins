# Operations

Servers, releases, deploys, rollback, backups. Every command here is a Task target; CI calls the same targets.

## First setup

Steps that need people, once per project:

1. Create the git remote; add the age keys to `.sops.yaml` and run `task secrets:encrypt ENV=local`.
2. Fill `.envs/production/app.env` (and `.envs/staging/app.env` if you run staging), each with its own secrets; `task secrets:encrypt ENV=<env>`. Single-quote secrets.
3. Set `APP_HOST`, `REGISTRY` and `DEPLOY_SSH_TARGET` (`ssh://<deploy-user>@host[:port]`) in `.envs/<env>/deploy.env`.
4. Prepare each server (next section) and run the preflight once before the first release.
5. Per login audience: register the app at the company identity provider ("Single sign-on" below), or set up a mail transport (`EMAIL_URL`) and agree the privacy notice before external users get access.
6. CI: secrets per environment (`SOPS_AGE_KEY`, deploy SSH key and known hosts) and the project settings<!-- >>> gitlab --> in `docs/ci.md`, "GitLab project settings"<!-- <<< gitlab --><!-- >>> !gitlab --> named in the CI files' header comments<!-- <<< !gitlab -->.
7. Prove the release automation once with a prerelease tag; delete the probe tag and release afterwards.

## Server setup

Once per server (staging and production may share one):

1. **Shared Traefik:** one per server, owning the external `proxy` network, TLS and Let's Encrypt (reference setup: `assets/traefik-host/` in the `fullstack-engineering` skill). App stacks never run their own proxy. If a registry or large uploads go through it, its `websecure` read timeout must exceed the longest upload (Traefik's default is 60 s).
2. **Deploy user:** a dedicated user with only the deploy key in `authorized_keys`, in the `docker` group. Put it in `DEPLOY_SSH_TARGET=ssh://<user>@<host>[:<port>]` in `.envs/<env>/deploy.env`; without a user, SSH falls back to the caller's (root in CI) and fails.
3. **SSH limits:** Docker contexts open one SSH session per service. Do not use connection multiplexing (`ControlMaster`) for the deploy host; check `sshd -T | grep -E 'maxsessions|maxstartups'`.
4. **DNS:** the app hosts point to the server; only ports 80 and 443 are open.
5. **Container logs** limited on the host (`/etc/docker/daemon.json`, `json-file` with `max-size`).
6. **CI works wherever its runner is:** deploys only over SSH, no Docker socket, host paths or localhost shortcuts into this server. If a runner shares the host with production, isolate it: no privileged jobs, protected runners for jobs with secrets, CPU and memory caps, never this server's Docker socket.
7. **Preflight** from the CI deploy context once the first images exist: `task deploy:preflight ENV=production VERSION=<tag>` (SSH login, remote Docker, registry login, images present, registry matches the release).<!-- >>> gitlab --> In CI: push a prerelease tag (e.g. a release candidate of the first version); its pipeline runs up to `deploy_preflight` and proves protected variables and SSH without deploying.<!-- <<< gitlab -->

CI settings per platform (protected release tags, deploy variables per environment, approval for production):<!-- >>> gitlab --> `docs/ci.md`, "GitLab project settings"<!-- <<< gitlab --><!-- >>> !gitlab --> see the header comments of the CI files<!-- <<< !gitlab -->.

**CI tools** (Task, sops, Compose, regctl, Caddy) are pinned with their SHA-256 in `scripts/ci/tools.txt` and installed by `scripts/ci/install-tools.sh`: mirror first, then the original source, hash checked either way. The `mirror-tools` job copies missing versions into the mirror on the integration branches (GitLab: the project's generic package registry; GitHub: the store in `TOOL_MIRROR_URL`, if set). Bump a tool with `scripts/ci/pin-tool.sh <name> <version>` after reading its release notes; the next pipeline on an integration branch mirrors it.

## Release

The version is the release tag, shape `1.8` (`scripts/release.sh`), and nothing else: no version file, no bump commit. Images exist before their tag, so the version is not baked in; the deploy sets `APP_VERSION` and `/api/v1/version/` reports it.
<!-- >>> gitlab -->

**Build once (GitLab):** every commit is built once, tested on exactly that image and tagged `tested-<sha>`; a release copies the tested digest to the version tag. How the pipeline does it: `docs/ci.md`.

1. **Candidate green on `main`:** checks, tests, `mark_tested` and the smoke test (`task release:smoke`: the tested images with production settings behind a throwaway Traefik). Fast-forward `main` to the tested `develop` where possible: a merge commit is a new SHA and is built and tested again.
2. **Migrations on real data:** restore a recent production backup into the smoke stack and migrate on top of it, on the production host (over SSH, a throwaway stack; production data never goes to CI or laptops): `SMOKE_DUMP=<file.dump> task release:smoke`. A migration that repoints a foreign key or deletes a model needs a data step or a written decision to drop the data. Diff the `.example` env files against the previous release and apply changed values to each environment.
3. **Create the release:** in `main`'s pipeline play `create_release` with the job variable `RELEASE_VERSION=1.8` (release tags `1.8`, `1.8.1`; prereleases `1.8a1`, `1.8-rc1`).
4. **Tag pipeline:** play `deploy_preflight`, then `deploy_production`. Prerelease tags stop after the preflight.
5. **Live checks:** version on `/api/v1/version/`, login, one core flow, one real password-reset mail end to end, error tracking, security headers, proxy logs.
<!-- <<< gitlab -->
<!-- >>> github -->

**GitHub:**

1. **Candidate green on `main`:** checks, end-to-end, production smoke test (`task release:smoke`).
2. **Migrations on real data:** `SMOKE_DUMP=<file.dump> task release:smoke` on the production host; production data never goes to CI.
3. **Tag:** `git tag -a 1.8 -m "..." && git push origin 1.8`. The release workflow validates the tag, builds and pushes the images, smoke-tests them and deploys to staging; approve production in CI.
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
## Day to day

```bash
task deploy:version ENV=production          # requested and running version
task deploy:ps ENV=production
task deploy:logs ENV=production -- django
task deploy:manage ENV=production -- shell  # one-off command in the running version
task deploy:backup ENV=production
```

**Admin account, the env is the source of truth.** `ensure_admin` runs after migrate on every deploy and on every start of the local stack (rules: the `fullstack-engineering` security reference). To apply a changed admin password without a release, change the env file and redeploy the running tag (<!-- >>> gitlab -->retry its `deploy_production` job<!-- <<< gitlab --><!-- >>> !gitlab -->the deploy workflow with that version<!-- <<< !gitlab -->). Dev, staging and production use the same keys in their env files:

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

## Pins and versions

Bump pins like dependencies, after reading the release notes, one at a time:

- **Python:** the newest minor that every core package officially supports (Celery is usually last). **Node:** the current Active LTS. **PostgreSQL:** the current major with at least a year of minor releases. **Redis:** the current stable major. **Debian:** the suite pinned on purpose, since unsuffixed slim tags switch suites by themselves. **Caddy, Mailpit, Traefik:** current majors.
- **Docker and Compose:** one exact version for every Docker job (`-cli` and `-dind` equal), so the smoke test and the deploy run the same Compose; read the release notes on every Compose major.
- **CI tools** (Task, sops, Compose, regctl, Caddy): exact versions with SHA-256 in `scripts/ci/tools.txt`, bumped with `scripts/ci/pin-tool.sh <name> <version>`.

## Failure triage

| Error | Cause |
|-|-|
| `root@host: Permission denied (publickey,password)` | SSH user missing in `DEPLOY_SSH_TARGET`; CI fell back to root |
| `ssh: connect to host ... port 22: Connection refused` | SSH port missing in the target |
| `unauthorized to access repository ... action: pull` | No registry credentials on the caller or the server |
| `resumable blob upload invalid`, `499` on push | Reverse-proxy read timeout in front of the registry |
| `ForeignKeyViolation ... is not present in table` during migrate | Migration not rehearsed on production data |
| `container ... has no healthcheck configured` from `up --wait` | Disabled healthcheck, or Compose version drift between smoke test and deploy |
| Every deploy variable missing in the preflight of a tag pipeline | Release tags not protected |

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

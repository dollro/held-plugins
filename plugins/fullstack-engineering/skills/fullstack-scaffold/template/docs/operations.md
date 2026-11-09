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
7. **Preflight** from the CI deploy context once the first images exist: `task deploy:preflight ENV=staging VERSION=vX.Y.Z` (SSH login, remote Docker, registry login, images present, registry matches the release).

CI settings per platform (protected release tags `v*`, environments `staging` and `production` with their own `SOPS_AGE_KEY`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, approval for production): see the header comments of the CI files.

**CI tools** (Task, sops, Compose) are pinned with their SHA-256 in `scripts/ci/tools.txt` and installed by `scripts/ci/install-tools.sh`: mirror first, then the original source, hash checked either way. The `mirror-tools` job copies missing versions into the mirror on protected branches (GitLab: the project's generic package registry; GitHub: the store in `TOOL_MIRROR_URL`, if set). Bump a tool with `scripts/ci/pin-tool.sh <name> <version>` after reading its release notes; the first pipeline on a protected branch mirrors it.

## Release

1. **Candidate green on `main`:** checks, end-to-end, production smoke test (`task release:smoke`: release images and production settings behind a throwaway Traefik).
2. **Migrations on real data:** restore a recent production backup into the smoke stack and migrate on top of it, only where production data may be: `SMOKE_DUMP=<file.dump> task release:smoke`. A migration that repoints a foreign key or deletes a model needs a data step or a written decision to drop the data.
3. **Tag:** `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`. The release pipeline validates the tag, builds and pushes the images, smoke-tests them and deploys to staging.
4. **Staging check,** then approve the production deploy in CI.
5. **Live checks:** version on `/api/v1/health/`, login, one core flow, one real password-reset mail end to end, error tracking, security headers, proxy logs.

Each deploy runs `task deploy ENV=<env> VERSION=vX.Y.Z`: preflight → backup → pull → migrate → up (waits for healthy) → verify (version on the public URL). The CI platform's environment history records what runs.

## Rollback

Redeploy the previous release on purpose, through CI so it uses the CI credentials and shows in the environment history:

- **GitLab:** re-run the production deploy job of the previous tag's pipeline. "Prevent outdated deployment jobs" stops stale pipelines; the explicit re-run is allowed and logged as a rollback.
- **GitHub:** run the `deploy` workflow with the previous version and `rollback` checked.

As a last resort from a laptop, at the previous tag (the compose file comes from the checkout):

```bash
git switch --detach v1.2.2
task deploy ENV=production VERSION=v1.2.2 ROLLBACK=1
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

Admin accounts: the bootstrap superuser from `DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD` is for the first login only; change its password through the reset mail and remove the password from the env file afterwards. Create further admins without a password and let them set one through the password-reset mail (not `createsuperuser --noinput`: it would take `DJANGO_SUPERUSER_PASSWORD` from the container environment):

```bash
DEPLOY_ENV=production scripts/deploy.sh manage shell -c \
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

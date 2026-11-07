# Environments and configuration flow

How local, CI, staging and production differ, and how a value travels from an env file into Docker, Django, FastAPI and the Vue bundle.

## The environments

| Environment | Purpose | Runs | Settings |
|-|-|-|-|
| local | Development | Compose dev stack, code bind-mounted, Vite dev server with HMR | Development settings (debug tools) |
| ci | Checks before merge | The dev stack plus a CI overlay: built assets, no dev server, debug off | Development settings with debug off, or test settings for unit tests |
| staging | Verify a release before production | The release images, on a server | **Production settings**, own env values |
| production | Users | The same release images | Production settings |

Settings modules describe the *kind of runtime* (development, test, hardened production), not the environment name. Staging uses the production module so it exercises the production code path; a `staging.py` that differs from production defeats its purpose.

Small apps may skip staging. Then the release pipeline's smoke test is the last gate before production, and the rollback path (redeploy the previous release with `ROLLBACK=1`) is tested once.

## Build once, promote the same artifact

- A version tag builds each image **once**. The smoke test, staging and production use the same tag; promotion is the release pipeline's production deploy of the version staging ran (after approval).
- **No per-environment builds**, Dockerfile targets or bake files. A separate staging image tests something other than what production runs.
- **Build arguments** carry only properties of the artifact: runtime versions, the app version, the target platform. Never URLs, hostnames, feature flags or secrets; build arguments and anything they set end up in image layers.
- Multi-platform images (amd64 + arm64) come from one build with several platforms; platform-independent stages (the frontend bundle) run once on the build platform.

## Where values live

| Kind | Where | Committed |
|-|-|-|
| Secrets and per-environment config | `.envs/<env>/app.env`, encrypted (SOPS) | Only encrypted, plus a generated example with credentials blanked |
| Deploy target (host, registry, SSH target with user and port, proxy network) | `.envs/<env>/deploy.env` | Yes, plain text. The version is not stored: the release pipeline passes its tag; the CI environment history records what runs |
| Local development defaults | `.envs/local/app.env` | Encrypted; the example works as is for booting the stack |
| CI-only differences | The CI compose overlay | Yes |

Each environment has its own secrets; a secret is never shared between staging and production.

## How a value reaches each layer

- **Docker Compose:** `env_file:` passes the file into the container environment. `${VAR}` interpolation in the compose file is resolved on the machine running `docker compose`: use it only for deploy state (image tag, host, network names), and make required ones fail loudly (`${APP_VERSION:?}`). Files edited on Windows carry CRLF; strip `\r` before compose reads them, or every value keeps it.
- **Django:** settings read the environment once at startup (django-environ). Secrets have no defaults, so a missing value stops the process at boot rather than failing on first use. Never read `os.environ` outside settings.
- **FastAPI:** a typed settings class (pydantic-settings) with the same variable names as Django for shared values (database URL, Redis URL, session cookie name, internal secret).
- **Vue / Vite:** `import.meta.env.VITE_*` is replaced at build time and ends up readable in the bundle. Treat it as public and identical for all environments: build constants at most. Environment-specific values (environment name, feature flags, public keys such as a frontend error-reporting DSN) are rendered by Django into each page as JSON (`json_script`) and read by one small config module. API and stream URLs stay relative (same origin), so they need no configuration at all.
- **Celery and other workers** use the Django settings and the same env file as the web process.

## The environment name

One variable (e.g. `APP_ENVIRONMENT`) names the environment for logs, error reports, metrics and a visible badge in non-production UIs. Code never branches on it; behaviour differs only through the settings module and explicit, named variables (`MFA_REQUIRED`, `SIGNUP_OPEN`, …), so every difference is visible in the env file.

## Staging rules

- Own hostname, database, secrets and identity-provider registration (or redirect URIs); never production credentials.
- No production personal data. Invented data, or an anonymised copy agreed with data protection.
- Outgoing mail to a sandbox or catching SMTP service; external APIs in their test modes.
- Same compose file and deploy script as production, selected by an environment parameter, so the deploy path itself is tested before production uses it.

## Pitfalls seen in practice

- **API base URLs in Vite `.env.production` files** (`VITE_API_ROOT=https://...`): forces a build per environment and breaks the promote-the-same-image rule. Use relative URLs and runtime config.
- **`DEBUG` or `ALLOWED_HOSTS` defaults that are permissive** in shared settings: production must fail closed when a value is missing.
- **A `DJANGO_SETTINGS_MODULE` in the container environment** overrides what pytest's config says; force test settings explicitly.
- **Compose's YAML output (`docker compose config`) wraps long lines;** check rendered values with `--format json` before concluding a value was cut.
- **Tests on development images do not exercise production settings.** End-to-end tests run with development settings, so `ALLOWED_HOSTS`, the HTTPS redirect, secure cookies, static files with `DEBUG` off and internal service URLs are proven only by the production smoke test (`testing.md`) and staging. Seen in practice: every page 500 because static files were missing from the image; a numeric gid without a group entry; the realtime service's internal call to Django refused (internal hostname not allowed, plain-HTTP call redirected to HTTPS); account links pointing at routes that did not exist. CI was green each time.
- **Changing an env file needs a container recreate,** not a restart (`up -d` recreates; `restart` keeps the old environment).
- **Automatic image updaters (Watchtower and similar)** deploy whatever is newest: incompatible with pinned, migrated releases.
- **Empty values in old local env files override pinned defaults:** an `IMAGE_VERSION=` left from an older template wins over a bake or script default. Treat empty like unset for pinned versions (as compose's `${VAR:-default}` does) and keep each pin in one place.
- **A laptop checkout is a stale source of truth:** deploy commands that read a version from local files deploy what that checkout says, not what runs. Pass the version explicitly, default one-off commands to the running version, and refuse an older one without a rollback flag.

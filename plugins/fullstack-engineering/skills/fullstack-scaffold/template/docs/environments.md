# Environments

| Environment | Runs | Settings | Values |
|-|-|-|-|
| local | Compose dev stack (`compose.local.yml`), code bind-mounted, Vite dev server | `backend.config.settings.local` | `.envs/local/app.env` |
| CI | Dev stack plus `compose.ci.yml` (built assets, debug off); smoke test with the release images | test / production | `.envs/local/app.env.example`; smoke test: generated throwaway values |
| staging | The release images on a server (`compose.deploy.yml`) | `backend.config.settings.production` | `.envs/staging/` |
| production | The same release images | `backend.config.settings.production` | `.envs/production/` |

Staging runs the production settings with its own values; there is no `staging.py`. Settings describe the kind of runtime, not the environment name. `APP_ENVIRONMENT` is only a label (logs, error reports, a badge outside production).

## Where values live

| File | Holds | Committed |
|-|-|-|
| `.envs/<env>/app.env.enc` | Secrets and per-environment configuration, SOPS-encrypted | Yes, encrypted only |
| `.envs/<env>/app.env.example` | The same keys with credentials blanked, generated | Yes |
| `.envs/<env>/app.env` | Decrypted working copy | No (gitignored, blocked by pre-commit) |
| `.envs/<staging\|production>/deploy.env` | Deploy target: host, registry, SSH target (`ssh://user@host[:port]`), proxy network | Yes, plain text |

The version is never stored in a file: the release pipeline passes its tag (`task deploy ENV=<env> VERSION=vX.Y.Z`).

```bash
task secrets:edit ENV=staging      # edit encrypted values; regenerates the example
task secrets:decrypt ENV=local     # working copy for local development
task secrets:updatekeys            # after adding or removing a person in .sops.yaml
```

Removing a person means re-encrypting (`secrets:updatekeys`) **and rotating** every secret they could read.

## How a value reaches each layer

- **Docker Compose:** `env_file:` passes `app.env` into the containers. `${VAR}` in compose files is resolved on the machine running `docker compose` and is used only for deploy state (image tag, host, network).
- **Django:** settings read the environment once at startup; secrets have no defaults, so a missing one stops the process at boot.
<!-- >>> realtime -->
- **Realtime service:** a typed settings class with the same variable names as Django for shared values (database, Redis, session cookie name, internal secret).
<!-- <<< realtime -->
- **Vue:** the bundle holds nothing environment-specific. API and stream URLs are relative; runtime values are rendered by Django into the page (`json_script`) and read by `frontend/src/config.ts`. `VITE_*` variables are public build constants.
- **Celery** uses the Django settings and the same env file.

Changing an env file needs a recreate, not a restart: `task dev:restart -- <service>` locally, a deploy on servers.

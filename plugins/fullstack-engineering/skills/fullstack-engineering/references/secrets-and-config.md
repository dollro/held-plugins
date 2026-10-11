# Secrets and configuration

## Configuration

- Every environment-specific value comes from environment variables. One env file per environment feeds all services (`.envs/<env>/app.env`); each service ignores keys it does not know.
- Required secrets have no defaults, so a missing value fails at startup instead of running with a placeholder.
- Non-secret deploy state (the pinned `APP_VERSION`, host name, proxy network) lives in a separate, committed file per deployed environment (`.envs/staging/deploy.env`, `.envs/production/deploy.env`).
- How values flow into Docker, Django, FastAPI and the Vue bundle, and what staging may and may not share with production: `environments.md`.

## SOPS + age

| File | Committed | Purpose |
|---|---|---|
| `.envs/<env>/app.env.enc` | yes | Encrypted source of truth |
| `.envs/<env>/app.env` | no (gitignored, pre-commit blocks it) | Decrypted working copy |
| `.envs/<env>/app.env.example` | yes | Generated: external credentials blanked, local infrastructure values kept so the stack boots without decryption |
| `.sops.yaml` | yes | Which age public keys may decrypt which files |

- Edit in place with `sops` (Task: `secrets:edit ENV=...`), which re-encrypts on save; then regenerate the examples (`secrets:examples`). A pre-commit hook fails when an example is out of date.
- Masking in the example generator blanks credential-shaped keys (API keys, tokens, passwords, secrets, private keys, URLs with embedded credentials such as `DATABASE_URL`), with an explicit allowlist of harmless local values.
- **Decrypt and generate via a temp file.** `cmd > file` truncates the target before `cmd` runs, so a failed `sops -d` leaves an empty env file (which `status:` checks then treat as done). Replace the target only on success: `sops -d in > out.tmp && mv out.tmp out`. Same for encrypting into the committed `.enc`.
- **Adding a person:** add their age public key to `.sops.yaml`, run `sops updatekeys` on each file, commit.
- **Removing a person:** remove the key, `updatekeys`, and **rotate every secret they could read**; old ciphertext stays readable in git history for anyone who had the key.
- The age private key never enters git. Back it up outside the repo (password manager). CI gets its own age key as a masked secret.

## When SOPS is not enough

SOPS + age fits small teams with one or a few hosts. Move to a secrets manager (cloud secret manager, Vault, 1Password, Infisical, Doppler) when you need audit logs of who read what, revocation without re-encryption, dynamic credentials, or SSO-gated access.

## At runtime

- Secrets reach containers as environment variables at deploy time. They never get baked into images (`.dockerignore` excludes env files; build steps that need settings use dummy values).
- Values passed as env are visible in the container config to anyone with access to the host's Docker socket (`docker inspect`). Treat Docker socket access as secret access; for the most sensitive values consider Compose `secrets:` (files under `/run/secrets`).
- Logs, traces and error reports must not contain secrets or tokens; scrub before sending.

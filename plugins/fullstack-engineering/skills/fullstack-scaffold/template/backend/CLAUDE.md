# CLAUDE.md — __PROJECT_TITLE__ Django (`backend/`)

Django owns users, auth, the REST API under `/api/v1/`, the admin, server-rendered pages and Celery tasks. It is the only service that decides who a caller is; the realtime service asks it through `/api/v1/internal/*`.

## Commands

```bash
task dev:manage -- shell                  # Django shell
task dev:makemigrations                   # commit the result
task test:backend -- backend/api          # one app
task dev:manage -- issue_api_key <email> <name>
```

## Access Points

| Service | URL |
|-|-|
| App (via local proxy) | http://localhost:8000 |
| Admin | http://localhost:8000/admin/ |
| Flower | http://localhost:5555 |
<!-- >>> accounts -->| Mailpit (outgoing mail) | http://localhost:8025 |
<!-- <<< accounts -->
## Key Patterns

- Settings: `config/settings/{base,local,production,test}.py`; every value that differs per environment comes from env.
- Browser auth is the Django session + CSRF. Every login (password, SSO, MFA) runs through django-allauth's pages under `/accounts/`; the admin login redirects there too. Never add a login endpoint of your own: it would bypass rate limits, verification and MFA. Audience rules: settings `AUTH` sections and `docs/architecture.md`.
- Non-browser clients use hashed API keys (`users.ApiKey`, `Authorization: Bearer`).
- Enqueue Celery tasks with `transaction.on_commit`.
- Internal endpoints (`api/internal.py`) skip user auth and require `X-Internal-Secret`; they fail closed.
- Long or external work goes to Celery (`*/tasks.py`); tasks take IDs, not model instances.
- Tables owned by the realtime service are read here only through `managed = False` models.

## Docs

`docs/architecture.md`, `docs/operations.md`.

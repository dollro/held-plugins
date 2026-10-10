# Sources

Check these before writing framework code (context7 resolves most of them as library docs). Links point to stable entry pages; follow them to the current version's docs, changelog and migration guide.

Last reviewed: 2026-10-10. The stack choices were checked against these sources then; versions were deliberately not pinned here.

## Backend

| Component | Docs | Changes |
|---|---|---|
| Django | https://docs.djangoproject.com/ | https://docs.djangoproject.com/en/stable/releases/ · supported versions: https://www.djangoproject.com/download/ |
| Django REST framework | https://www.django-rest-framework.org/ | https://www.django-rest-framework.org/community/release-notes/ |
| django-allauth | https://docs.allauth.org/ | https://docs.allauth.org/en/latest/release-notes/ · Microsoft provider: https://docs.allauth.org/en/latest/socialaccount/providers/microsoft.html · MFA: https://docs.allauth.org/en/latest/mfa/configuration.html · admin: https://docs.allauth.org/en/latest/common/admin.html |
| django-vite | https://github.com/MrBin99/django-vite | releases on GitHub |
| Celery | https://docs.celeryq.dev/ | https://docs.celeryq.dev/en/stable/changelog.html · Redis broker caveats: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html |
| FastAPI | https://fastapi.tiangolo.com/ | https://fastapi.tiangolo.com/release-notes/ |
| Starlette | https://www.starlette.dev/ | release notes on the site |
| SQLAlchemy | https://docs.sqlalchemy.org/ | https://docs.sqlalchemy.org/en/latest/changelog/ (read the migration guide per minor) |
| Alembic | https://alembic.sqlalchemy.org/ | https://alembic.sqlalchemy.org/en/latest/changelog.html |
| psycopg | https://www.psycopg.org/psycopg3/docs/ | news on the site |
| pydantic-settings | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | |
| Python versions | https://devguide.python.org/versions/ | |
| Microsoft Entra ID (OIDC) | https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc | |
| Microsoft Entra External ID (B2B guests, external tenants) | https://learn.microsoft.com/en-us/entra/external-id/external-identities-overview | |

## Frontend

| Component | Docs | Changes |
|---|---|---|
| Vue | https://vuejs.org/ | https://github.com/vuejs/core/releases |
| create-vue | https://github.com/vuejs/create-vue | `pnpm dlx create-vue@latest --help` |
| Vite | https://vite.dev/ | https://vite.dev/guide/migration · backend integration: https://vite.dev/guide/backend-integration · env variables: https://vite.dev/guide/env-and-mode |
| Vue Router | https://router.vuejs.org/ | migration guides on the site |
| Pinia | https://pinia.vuejs.org/ | https://github.com/vuejs/pinia/releases |
| Tailwind CSS | https://tailwindcss.com/docs | https://github.com/tailwindlabs/tailwindcss/releases |
| TypeScript | https://www.typescriptlang.org/docs/ | https://devblogs.microsoft.com/typescript/ |
| Vitest | https://vitest.dev/ | https://github.com/vitest-dev/vitest/releases |
| Playwright | https://playwright.dev/ | Docker: https://playwright.dev/docs/docker |
| ESLint / Oxlint | https://eslint.org/docs/latest/ · https://oxc.rs/docs/guide/usage/linter.html | |
| pnpm | https://pnpm.io/ | https://github.com/pnpm/pnpm/releases · CI: https://pnpm.io/continuous-integration |
| Node.js release schedule | https://nodejs.org/en/about/previous-releases | |

## Platform

| Component | Docs |
|---|---|
| uv | https://docs.astral.sh/uv/ · Docker guide: https://docs.astral.sh/uv/guides/integration/docker/ |
| Ruff | https://docs.astral.sh/ruff/ · pre-commit hooks: https://github.com/astral-sh/ruff-pre-commit |
| Docker Compose | https://docs.docker.com/compose/ · startup order: https://docs.docker.com/compose/how-tos/startup-order/ |
| Docker Bake | https://docs.docker.com/build/bake/ |
| Docker security / contexts over SSH | https://docs.docker.com/engine/security/protect-access/ |
| PostgreSQL | https://www.postgresql.org/docs/ · versioning: https://www.postgresql.org/support/versioning/ · image notes: https://hub.docker.com/_/postgres |
| Redis | https://redis.io/docs/latest/ |
| Caddy | https://caddyserver.com/docs/ |
| Traefik | https://doc.traefik.io/traefik/ · releases: https://github.com/traefik/traefik/releases · header aliases: https://doc.traefik.io/traefik/security/header-aliases/ |
| Docker socket proxy | https://github.com/linuxserver/docker-socket-proxy |
| TLS configuration | https://ssl-config.mozilla.org/ |
| SOPS | https://getsops.io/docs/ |
| age | https://github.com/FiloSottile/age |
| Task | https://taskfile.dev/ · includes: https://taskfile.dev/docs/reference/schema |
| MkDocs | https://www.mkdocs.org/ · Material: https://squidfunk.github.io/mkdocs-material/ · end of life notice: https://github.com/squidfunk/mkdocs-material/issues/8523 |
| MkDocs successors | Zensical: https://zensical.org/ · ProperDocs: https://github.com/properdocs/properdocs |
| Docker multi-platform builds | https://docs.docker.com/build/building/multi-platform/ |
| Playwright MCP | https://github.com/microsoft/playwright-mcp |
| pre-commit | https://pre-commit.com/ |
| GitHub Actions security | https://docs.github.com/en/actions/reference/security/secure-use |
| GitLab Docker-in-Docker | https://docs.gitlab.com/ci/docker/docker_in_docker/ |
| Sentry (Python, JavaScript) | https://docs.sentry.io/ |
| OpenTelemetry Python | https://opentelemetry-python-contrib.readthedocs.io/ |

## Security guidance

| Topic | Source |
|---|---|
| Authentication | https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html |
| Multi-factor authentication | https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html |
| Session management | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html |
| CSRF | https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html |
| WebSockets | https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html |
| Browser storage | https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html |
| Docker | https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html |
| OAuth for browser-based apps | IETF "OAuth 2.0 for Browser-Based Applications" (BCP), https://www.rfc-editor.org/ |

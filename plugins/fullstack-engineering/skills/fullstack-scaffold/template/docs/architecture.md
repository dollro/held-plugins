# Architecture

Built on the fullstack reference stack (`fullstack-engineering` skill). This page records the choices made for this app and every deliberate deviation, with the reason.

## Shape

<!-- >>> realtime -->
**Django + FastAPI:** Django is the system of record; the FastAPI realtime service holds long-lived connections (Server-Sent Events under `/v1/*`) and asks Django who a caller is through internal endpoints.
<!-- <<< realtime -->
<!-- >>> !realtime -->
**Django only:** Django is the system of record and serves pages, the REST API and the admin. Add a realtime service only for streaming or agent workloads.
<!-- <<< !realtime -->

| Concern | Owner |
|-|-|
| Users, permissions, admin, REST API (`/api/v1/`), pages | Django |
<!-- >>> realtime -->
| Streams (`/v1/*`), its own tables (Alembic, own version table) | FastAPI realtime service |
<!-- <<< realtime -->
| Background and scheduled work | Celery workers and beat (Django code) |
| Data | PostgreSQL, one owning service per table |
| Cache, broker, pub/sub | Redis |
| Browser UI | Vue islands in Django pages, SPA under `/app/` |

## Contracts

- **Browser → Django:** session cookie + CSRF on one origin; all HTTP through `frontend/src/api/client.ts`.
<!-- >>> realtime -->
- **Browser → realtime:** the same session cookie, validated by Django over `/api/v1/internal/validate-session`; cross-site requests refused.
- **Realtime → Django:** internal endpoints guarded by `INTERNAL_API_SECRET`, compared in constant time, failing closed.
<!-- <<< realtime -->
- **Machine clients:** hashed API keys (`Authorization: Bearer`), shown once, revocable.
- **Operations:** configuration from the environment, liveness and readiness endpoints, migrations as a separate deploy step.

## Login

Login audience: **__AUTH_AUDIENCE__**. Every login runs through django-allauth's pages under `/accounts/`, the admin login included.

<!-- >>> internal -->
- Staff log in through the company identity provider over OpenID Connect ([Single sign-on](operations.md#single-sign-on)), restricted to the company. Local password login is off in production (`LOCAL_LOGIN_ENABLED=False`) and exists for development and tests only.
<!-- <<< internal -->
<!-- >>> external -->
- External users have app accounts with email verification by code; MFA is required in production (`MFA_REQUIRED`); signup is by invitation unless `SIGNUP_OPEN` is on.
- External users see only their own data: querysets are scoped to the user and tested with a second user.
<!-- <<< external -->
<!-- >>> mixed -->
- Staff and SSO-linked accounts log in only through the company identity provider ([Single sign-on](operations.md#single-sign-on)); external users have verified app accounts with MFA. Staff rights are never granted at signup.
- External users see only their own data: querysets are scoped to the user and tested with a second user.
<!-- <<< mixed -->

## Deviations from the reference

None yet. Record each one here: what, why, and what would make us revisit it.

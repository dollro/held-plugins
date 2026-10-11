# Backend: Django

## Settings

- `config/settings/base.py` holds everything shared; `local.py`, `production.py`, `test.py` change only what differs. Every value that differs per environment comes from env (`django-environ`), with no defaults for secrets so a missing one fails at startup.
- `DATABASES["default"]` from `DATABASE_URL`, `ATOMIC_REQUESTS = True`, persistent connections (`CONN_MAX_AGE`) under WSGI. Under ASGI use pooling instead of persistent connections.
- Custom user model from day one (`AUTH_USER_MODEL`), email as login identifier. Swapping it later is a migration project.
- Argon2 first in `PASSWORD_HASHERS`, older hashers kept so existing hashes upgrade on login.
- pytest selects the test settings explicitly (`--ds=...` in `addopts`), because a `DJANGO_SETTINGS_MODULE` in the container env would otherwise win.

## Auth

| Path | How |
|-|-|
| Browser login | django-allauth's server-rendered flows under `/accounts/` for every audience (`identity.md`), styled through an override of `allauth/layouts/base.html`. The admin login is wrapped with `secure_admin_login`. |
| SSO | allauth's generic OpenID Connect provider (`SOCIALACCOUNT_PROVIDERS["openid_connect"]["APPS"]`) configured from env: issuer URL, client ID and secret, PKCE on, `verified_email` limited to company-managed domains. Any OIDC provider is configuration only; a tenant-specific issuer (Entra: `https://login.microsoftonline.com/<tenant-id>/v2.0`) restricts sign-in to the company, because the token issuer is checked. Unconfigured: no button, its routes answer 404. |
| External accounts | allauth accounts with mandatory email verification by code, `allauth.mfa` (TOTP, passkeys as second factor, recovery codes), a middleware that sends users without a second factor to the setup where MFA is required. |
| Session use | DRF `SessionAuthentication` (enforces CSRF for authenticated unsafe requests). Pages that host Vue set the CSRF cookie (`ensure_csrf_cookie`). |
| Machine clients | API key model: random key with a short visible prefix, SHA-256 hash stored, `last_used_at`, `revoked_at`; a DRF authentication class for `Authorization: Bearer`. |
| Service-to-service | Internal views with no user authentication and a permission class that compares `X-Internal-Secret` with `hmac.compare_digest`; the secret has no default. |

Principles for the login layer: the SSO handshake starts with a POST, never a GET link; internal apps switch password login off in production; who may sign up is decided in one place (the account adapter); provisioning from the tenant is a switch; the installed apps never depend on the environment, so migrations never change with configuration. Look up the current setting names in the allauth docs.

allauth pitfalls seen in practice:

- `ACCOUNT_SIGNUP_FIELDS` also shapes the login form: without `password1` allauth switches to passwordless login by emailed code, even when signup is closed.
- Rate limits live in the cache: clear it between tests, or one test's sent verification mail blocks the next.
- Verification code format is allauth's choice (it changed to `XXXX-XXXX`); tests should not hard-code its length.
- Passkey-only login and login by code skip `authenticate()`: rules implemented in an authentication backend do not cover them.

Validating a session for another service: build an `HttpRequest`, attach `SessionStore(session_key)`, call `django.contrib.auth.get_user()`. It also verifies the session auth hash, so logout and password changes invalidate the session everywhere.

## API

- DRF, JSON renderer only in production (browsable API locally), `IsAuthenticated` by default; public endpoints opt out explicitly.
- Serializers validate all input; querysets are scoped to the requesting user in the view, not filtered in the frontend.
- Describe the API as OpenAPI (e.g. drf-spectacular) when other clients consume it; pin it and diff the schema in CI, since such tools are pre-1.0.
- DRF versus django-ninja: DRF stays the default for CRUD- and admin-heavy apps. Do not mix both in one app.

## Celery

- One Celery app in `config/celery_app.py`, settings with the `CELERY_` prefix, JSON serialization only, task time limits set.
- Tasks take IDs and reload data; they are idempotent (a retry or redelivery must be harmless).
- Enqueue with `transaction.on_commit(lambda: task.delay(obj_id))`, so workers never see rolled-back data.
- Scheduled tasks via Celery beat with the database scheduler.
- **Redis broker pitfalls:** the visibility timeout (default about an hour) redelivers unacknowledged tasks, so ETA/countdown tasks scheduled further out than that can run again; do not use the broker as a long-range scheduler. Redis must not evict keys (`maxmemory-policy noeviction`, the default when no `maxmemory` is set). Several apps sharing one broker share the shortest visibility timeout.
- Django's built-in tasks framework (`django.tasks`) defines tasks but ships no production worker; keep Celery as the default until a vetted backend exists.

## Migrations

- Committed, reviewed, and checked in CI (`makemigrations --check --dry-run`).
- Backward compatible for one release: add nullable or defaulted fields, backfill, switch code, remove in a later release.
- Run as a deploy step (`manage.py migrate`), not on every container start in production.
- Tables owned by another service are mapped with `managed = False` (and a read-only base model if writes must be impossible); link them with plain ID fields, not foreign keys.

## Admin

The admin is a tool for operators: register models deliberately, use `list_display`, `search_fields`, read-only fields for secrets (never show raw API keys). Put it under a non-default URL in production (`DJANGO_ADMIN_URL`).

## Pitfalls

- A debug toolbar that is forced on (`SHOW_TOOLBAR_CALLBACK = lambda r: True`) breaks tests; make it depend on `DEBUG` at request time.
- Health endpoints must be exempt from the HTTPS redirect, or container healthchecks get a 301.
- `collectstatic` at image build needs importable settings, not real secrets: pass dummy values for required env vars in that build step only.

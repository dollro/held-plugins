# Security

Baseline for web apps, internal or external. Sources: OWASP cheat sheets (session management, CSRF, WebSocket, Docker, HTML5 storage) and the OAuth guidance for browser-based apps (`references/sources.md`).

## Auth flows

| Caller | Credential | Checked by |
|---|---|---|
| Browser → Django | Session cookie (HttpOnly, SameSite=Lax, Secure in production; `__Host-` name prefix in production) + `X-CSRFToken` on unsafe methods | Django session + CSRF middleware, DRF `SessionAuthentication` |
| Browser login | Per audience (`identity.md`): company SSO over OpenID Connect via allauth (restricted to the company's tenant or realm), app accounts with verified email and MFA, local password in dev/test. Always through allauth's flows | allauth (rate limits, verification, MFA stages) |
| Browser → realtime | Same session cookie, same origin | Realtime refuses cross-site signals, then asks Django `validate-session` |
| Machine client → any service | `Authorization: Bearer <api key>` | Django `ApiKey.resolve()` (directly or via `validate-key`) |
| Service → Django internal API | `X-Internal-Secret` | Constant-time compare, no default secret, fail closed |

## Rules

- **No tokens in localStorage or sessionStorage**, no tokens in URLs (they leak into logs and referrers).
- **CSRF:** Django's token for every unsafe request, login included (allauth's forms carry it). SameSite is defence in depth, not the defence.
- **Cross-site checks for cookie-authenticated endpoints outside Django** (realtime): refuse when `Sec-Fetch-Site` is present and not `same-origin`/`none`, or when `Origin` is present and neither this host nor allowlisted; accept when both are absent (plain-HTTP origins get no Fetch Metadata, same-origin GETs no Origin).
- **WebSockets:** exact `Origin` allowlist on every handshake, auth by cookie or first message, message size and rate limits, close on logout.
- **SSO:** OpenID Connect with PKCE against an issuer restricted to the company (Entra: tenant-specific issuer, never `common`), handshake by POST, provisioning switchable, email matching only for company-managed domains (not for guests). Map provider app roles or groups to permissions in code.
- **External accounts:** mandatory email verification, signup closed unless decided otherwise, rate limits, MFA required for confidential data and enforced on pages, API and realtime alike; in mixed apps staff and SSO-linked accounts cannot use passwords once SSO exists. Details: `identity.md`.
- **API keys:** CSPRNG, ≥128 bits, a visible prefix for identification and secret scanning, shown once, stored as SHA-256 (HMAC with a server pepper is a further hardening), `last_used_at`, revocation, never logged.
- **Internal endpoints:** no user data without the shared secret; never fall back to "allow localhost" in production.
- **Authorization in querysets and permissions**, not in the UI. Every endpoint states its permission explicitly.
- **Passwords** (where local accounts exist): Argon2, Django's validators.
- **Security headers in production:** HTTPS redirect (health endpoints exempt), HSTS, secure cookies, `X-Content-Type-Options`, frame protection; a Content Security Policy where feasible (Django ships CSP support in recent releases).
- **Uploads:** stored outside the static root, size- and type-checked, served with a safe content type; a dedicated volume when the root filesystem is read-only.
- **Dependencies:** lockfiles, frozen installs, automated update PRs, SHA-pinned CI actions, explicit approval of package build scripts.
- **Containers:** non-root, no capabilities, no privilege escalation, read-only root filesystem, no secrets in images.

## Review checklist

- [ ] No credential in localStorage, URLs, logs, traces or images
- [ ] Every unsafe browser request carries CSRF; login too
- [ ] Cookie-authenticated non-Django endpoints refuse cross-site signals
- [ ] Internal endpoints require the secret, compare in constant time, fail closed
- [ ] Every login through allauth (admin included); no other login endpoint
- [ ] SSO restricted to the tenant; handshake by POST
- [ ] External accounts: verified email, MFA where required, staff and SSO-linked accounts SSO-only in mixed apps
- [ ] API keys hashed, prefixed, revocable, shown once
- [ ] Querysets scoped to the user; permissions explicit per endpoint
- [ ] Production cookies Secure; HTTPS redirect and HSTS on
- [ ] Containers hardened; Docker socket access treated as root
- [ ] Tests cover CSRF refusal, logout invalidation, cross-site refusal, fail-closed behaviour

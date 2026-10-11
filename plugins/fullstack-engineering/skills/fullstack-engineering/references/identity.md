# Identity and login

Who logs in decides the auth setup more than any framework choice. Decide it per app, before the first model, and record it in `docs/architecture.md`.

## Choose the audience

| Audience | Typical app | Login | Second factor |
|-|-|-|-|
| **Internal** | Staff tools, dashboards, agent UIs for the team | Company identity provider over OpenID Connect, restricted to the company. Local password login only in development and end-to-end tests | The identity provider |
| **External** | Customer portal, applicant portal, partner portal | Accounts in the app: email + password, verified email, invitation or open signup | In the app (authenticator app, passkey, recovery codes); required where the data is confidential |
| **Mixed** | Portal for externals plus a back office for staff | Staff via the identity provider only; externals via app accounts | Staff: the identity provider. Externals: in the app |

Questions that settle it:

- Do people outside the company log in at all? If not: internal.
- Are the externals a few known people from partner organisations, managed by IT? Then **guest accounts in the company's identity provider** can be enough: the app stays "internal", guests use the same login and MFA policies. Needs IT's consent and a guest process.
- Many externals, self-registration, or a separate brand? App accounts (external/mixed), or a dedicated customer-identity service (CIAM) when central identity management or social logins at scale are required; it speaks OpenID Connect, so it plugs into the same SSO setting.
- Anything else (Google/LinkedIn login, SAML from customer IdPs) is a later addition through the same allauth layer, not a reason to change the architecture.

## Rules for every audience

- **Django owns the user.** Identity providers authenticate; the `User` row, permissions and data scoping stay in Django. The realtime service and API keys keep working unchanged whichever provider is used.
- **One login path.** Every login (password, SSO, MFA, code) runs through django-allauth's flows; the Django admin login redirects there (`secure_admin_login`). Never add a separate JSON login endpoint: it would bypass rate limits, email verification and MFA.
- **Sessions, not tokens, in the browser.** Session cookie + CSRF; for an SPA that wants its own login screens, use allauth's headless API in browser (cookie) mode, not tokens in storage.
- **Configuration switches providers on, code does not.** An SSO provider without configuration is invisible (no button, 404 on its routes), never a 500.

## Internal: company SSO over OpenID Connect

The reference uses allauth's generic OpenID Connect provider. Every standard provider (Microsoft Entra ID, Google Workspace, Keycloak, Okta) is configuration only: issuer URL, client ID, secret.

- **Restricted to the company:** the issuer must identify the company's tenant or realm. allauth checks every ID token against the issuer of the discovery document, so a tenant-specific issuer keeps everyone else out. Never a multi-tenant issuer unless the app is deliberately multi-tenant.
- Handshake starts with a POST; PKCE on.
- Provisioning on first login is a switch; off means only pre-created users get in.
- **Matching existing users by email** only for addresses the company manages: list those domains as verified (`verified_email` in the app settings). Guests and other domains then always get their own account, which closes account takeover by a forged or unverified email claim.
- The provider ID is part of the callback URL and stored with every linked account: choose it once, never change it.
- No refresh or access tokens stored unless the app calls the provider's APIs on the user's behalf; then store them encrypted and request the smallest scopes.
- Roles: start with Django groups and permissions; map provider roles or groups into them only when IT manages access centrally.

### Example: Microsoft Entra ID

- **Issuer:** `https://login.microsoftonline.com/<tenant-id>/v2.0`, never `common` or `organizations`. App registration by IT, single tenant, redirect URI `https://<host>/accounts/oidc/<provider-id>/login/callback/`, scopes `openid profile email`.
- **Email:** Entra does not send the standard `email_verified` claim by default, so addresses only count as verified through the configured company domains. `email` is only present when the user has a mailbox address or the optional claim is configured.
- **MFA and offboarding** come from Conditional Access and the tenant; that is why internal people must not have a password in the app (see Mixed).
- **External people in the Microsoft world:** B2B guests in the company tenant (few, known partners, managed by IT), or Entra External ID with its own external tenant (self-service at scale). Azure AD B2C is closed to new customers since 1 May 2025; do not start on it.

## External accounts

- **Email verification is mandatory**, by code (robust against mail scanners that open links). Production needs a real mail transport; development catches mail (Mailpit).
- **Signup is closed by default.** Invitation: create the user, they set their password via "Forgot password". Open signup is a deliberate per-app decision (spam: honeypot field, rate limits; consider a review step before access to data).
- **MFA:** authenticator app (TOTP) and passkeys as second factor, recovery codes. Where the app holds confidential or personal data, require it: users without a second factor are sent to the setup before anything else, API calls get 403, and the realtime service applies the same rule. Passkey-only login is a later option; enabling it must not bypass audience rules (see Mixed).
- **Rate limits and enumeration protection** on login, signup and password reset (allauth defaults, shared cache).
- **Account lifecycle:** deactivate instead of delete while data must be kept; delete or anonymise on request; lost second factor → recovery codes, otherwise an admin resets after verifying identity out of band.

## Mixed

- Staff, and every account linked to the company identity provider, cannot log in with a password once SSO is configured (an authentication backend that refuses password auth for `is_staff` or a linked account). Otherwise a company member can set a password through "Forgot password" and bypass the provider's MFA and offboarding. Before SSO exists (development), password login stays possible.
- Signup never grants staff rights; `is_staff` is set by an admin.
- The in-app MFA requirement is waived only for sessions that authenticated through SSO (allauth records how a session logged in), never because an account has a provider link; a password session always needs the app's second factor.
- Every other way in (passkey login, login by code) must keep these rules; add it with tests or leave it off.

## Data separation for external users

- Every queryset an external user reaches is scoped to them or their organisation (`get_queryset()` filters by `request.user`; object permissions on detail views). A forgotten filter is the classic portal data leak.
- Test it: user A requesting user B's object gets 404, in the API and in any server-rendered page.
- Staff access to external data goes through explicit staff views or the admin, not through widened user querysets.

## Personal data

External accounts are personal data, as are staff accounts. Keep only what the app needs; write down purpose, retention and deletion; agree the privacy notice and any processor (mail provider, hosting) with data protection before launch. Test and demo data uses invented people, never copies of real users.

## Tests every app keeps

Password login works through allauth; wrong password fails; no other login endpoint exists; admin login redirects to allauth; logout needs CSRF. Then per audience: local login switchable and no password signup (internal); verification required, closed signup creates nothing, second factor asked once set up, MFA requirement enforced on pages, API and realtime (external); staff and SSO-linked passwords refused with SSO, external password allowed, only SSO sessions exempt from in-app MFA (mixed); SSO routes 404 and no button without configuration, redirect to the provider by POST only, with PKCE (with SSO).

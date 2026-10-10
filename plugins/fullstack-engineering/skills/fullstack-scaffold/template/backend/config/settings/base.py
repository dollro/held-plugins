"""Settings shared by every environment. Values that differ come from the environment."""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

ROOT_DIR = Path(__file__).resolve().parents[3]
APPS_DIR = ROOT_DIR / "backend"

env = environ.Env()

# GENERAL
# ------------------------------------------------------------------------------
_version_file = ROOT_DIR / "VERSION.txt"
APP_VERSION = (
    _version_file.read_text().strip()
    if _version_file.exists()
    else env.str("APP_VERSION", default="development")
)
# local | ci | staging | production. A label for logs, error reports and the UI
# banner; code never branches on it (behaviour differs only through settings
# modules and explicit env vars).
APP_ENVIRONMENT = env.str("APP_ENVIRONMENT", default="local")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
# Names other services in the stack use to call Django directly (e.g. the
# realtime service on its internal URL); set by compose.deploy.yml.
ALLOWED_HOSTS += env.list("DJANGO_INTERNAL_HOSTS", default=[])
TIME_ZONE = env.str("TIME_ZONE", default="UTC")
LANGUAGE_CODE = "en"
USE_I18N = True
USE_TZ = True
ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# An empty value must not mount the admin at the site root (it would swallow
# every other URL), so empty means the default.
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="") or "admin/"
if not ADMIN_URL.endswith("/"):
    raise ImproperlyConfigured("DJANGO_ADMIN_URL must end with '/'.")

# DATABASE
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    # Login flows (django-allauth). Installed independent of the environment, so
    # migrations never change with configuration; see AUTH below.
    "allauth",
    "allauth.account",
    # >>> sso
    "allauth.socialaccount",
    "allauth.socialaccount.providers.openid_connect",
    # <<< sso
    # >>> accounts
    "allauth.mfa",
    # <<< accounts
    "django_vite",
    "django_celery_beat",
]
LOCAL_APPS = [
    "backend.users",
    "backend.api",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTH
# ------------------------------------------------------------------------------
# Login audience: __AUTH_AUDIENCE__ (chosen at scaffold time, see docs/architecture.md).
# All login flows run through django-allauth's pages under /accounts/, so rate
# limits, verification and MFA apply to every way in. Details: AUTH sections below.
AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    # >>> mixed
    "backend.users.backends.AuthenticationBackend",
    # <<< mixed
    # >>> !mixed
    "allauth.account.auth_backends.AuthenticationBackend",
    # <<< !mixed
]
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    # >>> accounts
    "backend.users.policy.RequireMfaMiddleware",
    # <<< accounts
]

# TEMPLATES / STATIC
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [APPS_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.api.context.runtime_config",
            ],
        },
    },
]
STATIC_URL = "/static/"
STATIC_ROOT = APPS_DIR / "staticfiles"
STATICFILES_DIRS = [APPS_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = APPS_DIR / "media"

# SESSIONS / CSRF
# ------------------------------------------------------------------------------
# The browser only ever talks to one origin (Django serves pages, API and the
# built Vue assets), so session cookies + CSRF are enough and no token lives in
# localStorage. The CSRF cookie stays readable for src/api/client.ts.
# Shared with the realtime service, which reads the same env var.
SESSION_COOKIE_NAME = env.str("SESSION_COOKIE_NAME", default="sessionid")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# REST FRAMEWORK
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "backend.users.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# REDIS / CACHE / CELERY
# ------------------------------------------------------------------------------
REDIS_URL = env.str("REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# VITE
# ------------------------------------------------------------------------------
DJANGO_VITE = {
    "default": {
        "dev_mode": env.bool("DJANGO_VITE_DEV_MODE", default=False),
        "dev_server_host": env.str("DJANGO_VITE_DEV_SERVER_HOST", default="localhost"),
        "dev_server_port": 3000,
        "static_url_prefix": "vue",
        "manifest_path": APPS_DIR / "static" / "vue" / ".vite" / "manifest.json",
    }
}

# SERVICE-TO-SERVICE
# ------------------------------------------------------------------------------
# Shared secret for internal endpoints (realtime service -> Django). Required:
# internal endpoints fail closed when it is missing.
INTERNAL_API_SECRET = env.str("INTERNAL_API_SECRET")
API_KEY_PREFIX = env.str("API_KEY_PREFIX", default="__PROJECT_KEY_PREFIX__")

# EMAIL
# ------------------------------------------------------------------------------
# One URL per environment, e.g. smtp+tls://user:password@host:587 (django-environ).
# Empty or unset falls back to the console (development); production settings
# require a real transport where users depend on mail.
EMAIL_URL = env.str("EMAIL_URL", default="") or "consolemail://"
vars().update(env.email_url_config(EMAIL_URL))
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="noreply@__APP_HOST__")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# AUTH: ACCOUNTS (django-allauth)
# ------------------------------------------------------------------------------
ACCOUNT_ADAPTER = "backend.users.adapters.AccountAdapter"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[__PROJECT_TITLE__] "
# >>> internal
# Local email/password login: on for development and end-to-end tests, off in
# production, where SSO is the only way in. Nobody signs up with a password.
LOCAL_LOGIN_ENABLED = env.bool("LOCAL_LOGIN_ENABLED", default=True)
SOCIALACCOUNT_ONLY = not LOCAL_LOGIN_ENABLED
SIGNUP_OPEN = False
ACCOUNT_EMAIL_VERIFICATION = "none"
# Signup is closed, but the fields still define the login form: without a
# password field allauth switches to passwordless login by emailed code.
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
# <<< internal
# >>> accounts
# External users sign up (if open) or are invited, verify their email with a
# code, and set up a second factor where MFA_REQUIRED is on.
SIGNUP_OPEN = env.bool("SIGNUP_OPEN", default=False)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = "website"
# Rate limits (ACCOUNT_RATE_LIMITS) and enumeration protection stay at allauth's
# defaults; they need the shared Redis cache configured above.

# MFA (allauth.mfa): authenticator app, passkeys as second factor, recovery codes.
MFA_SUPPORTED_TYPES = ["totp", "webauthn", "recovery_codes"]
MFA_TOTP_ISSUER = "__PROJECT_TITLE__"
# Passkey-only login stays off: it would skip the password-based rules above
# (and INTERNAL_USERS_SSO_ONLY). Enable only together with matching tests.
MFA_PASSKEY_LOGIN_ENABLED = False
# Users without a second factor are sent to set one up before anything else
# (backend/users/policy.py). Sessions that came through SSO get MFA from the
# identity provider.
MFA_REQUIRED = env.bool("MFA_REQUIRED", default=False)
# <<< accounts
# >>> sso

# AUTH: SSO (the company identity provider over OpenID Connect)
# ------------------------------------------------------------------------------
# Provider-neutral: Microsoft Entra ID, Google Workspace, Keycloak, Okta … are
# configuration only. Active once issuer, client ID and secret are set. Register
# this redirect URI at the provider: https://<host>/accounts/oidc/<SSO_PROVIDER_ID>/login/callback/
# Entra ID example (single tenant): https://login.microsoftonline.com/<tenant-id>/v2.0
SSO_ISSUER_URL = env.str("SSO_ISSUER_URL", default="")
SSO_CLIENT_ID = env.str("SSO_CLIENT_ID", default="")
SSO_CLIENT_SECRET = env.str("SSO_CLIENT_SECRET", default="")
SSO_ENABLED = bool(SSO_ISSUER_URL and SSO_CLIENT_ID and SSO_CLIENT_SECRET)
# Part of the URLs and stored with every linked account: never change it later.
SSO_PROVIDER_ID = env.str("SSO_PROVIDER_ID", default="company")
SSO_DISPLAY_NAME = env.str("SSO_DISPLAY_NAME", default="Company login")
# Create users on first SSO login. Off: only users that already exist can sign in.
SSO_AUTO_PROVISION = env.bool("SSO_AUTO_PROVISION", default=True)
# Email domains the company manages at the provider (e.g. example.com). Only these
# addresses count as verified, so only they may match an existing account by
# email; guests and other domains always get or keep their own account.
SSO_VERIFIED_EMAIL_DOMAINS = env.list("SSO_VERIFIED_EMAIL_DOMAINS", default=[])
# >>> mixed
# Once SSO is configured, staff and every account linked to the company identity
# provider may not log in with a password: internal people always come through
# the provider (backend/users/backends.py). External accounts keep password + MFA.
INTERNAL_USERS_SSO_ONLY = SSO_ENABLED
# Provider addresses are managed by the company; the mandatory verification
# above is for external accounts.
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
# <<< mixed

SOCIALACCOUNT_ADAPTER = "backend.users.adapters.SocialAccountAdapter"
SOCIALACCOUNT_LOGIN_ON_GET = False  # the handshake starts with a POST (allauth advice)
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "OAUTH_PKCE_ENABLED": True,
        # Match existing users by email, but only for verified addresses
        # (SSO_VERIFIED_EMAIL_DOMAINS); see references/identity.md.
        "EMAIL_AUTHENTICATION": True,
        "EMAIL_AUTHENTICATION_AUTO_CONNECT": True,
        "APPS": (
            [
                {
                    "provider_id": SSO_PROVIDER_ID,
                    "name": SSO_DISPLAY_NAME,
                    "client_id": SSO_CLIENT_ID,
                    "secret": SSO_CLIENT_SECRET,
                    "settings": {
                        # The issuer is checked against every ID token: a
                        # tenant-specific issuer restricts sign-in to that tenant.
                        "server_url": SSO_ISSUER_URL,
                        "verified_email": SSO_VERIFIED_EMAIL_DOMAINS,
                    },
                }
            ]
            if SSO_ENABLED
            else []
        ),
    }
}
# <<< sso

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "root": {"handlers": ["console"], "level": env.str("DJANGO_LOGLEVEL", "INFO")},
}

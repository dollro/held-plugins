# >>> accounts
from django.core.exceptions import ImproperlyConfigured

# <<< accounts
from .base import *  # noqa: F403
from .base import env

DEBUG = False

# TLS terminates at the reverse proxy in front of the stack.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# Health checks and service-to-service calls use plain HTTP inside the Docker
# network; internal endpoints are protected by X-Internal-Secret instead.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/(ready/)?$", r"^api/v1/internal/"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_CONTENT_TYPE_NOSNIFF = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Fail closed: a value missing from the env file must not loosen login rules.
# >>> internal
LOCAL_LOGIN_ENABLED = env.bool("LOCAL_LOGIN_ENABLED", default=False)
SOCIALACCOUNT_ONLY = not LOCAL_LOGIN_ENABLED
# <<< internal
# >>> accounts
MFA_REQUIRED = env.bool("MFA_REQUIRED", default=True)
SIGNUP_OPEN = env.bool("SIGNUP_OPEN", default=False)

# External users depend on email (verification codes, password reset).
if not env.str("EMAIL_URL", default=""):
    raise ImproperlyConfigured("EMAIL_URL is required in production.")
# <<< accounts

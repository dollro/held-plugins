from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Login settings are fixed here, so test results never depend on the env file
# of the container that runs them. Tests that need other values set them.
# >>> internal
LOCAL_LOGIN_ENABLED = True
SOCIALACCOUNT_ONLY = False
# <<< internal
# >>> accounts
SIGNUP_OPEN = False
MFA_REQUIRED = False
# <<< accounts
# >>> sso
from .base import SOCIALACCOUNT_PROVIDERS  # noqa: E402

SSO_ENABLED = False
SOCIALACCOUNT_PROVIDERS["openid_connect"]["APPS"] = []
# <<< sso
# >>> mixed
INTERNAL_USERS_SSO_ONLY = False
# <<< mixed

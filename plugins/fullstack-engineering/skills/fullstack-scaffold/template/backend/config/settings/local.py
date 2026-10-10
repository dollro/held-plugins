from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, REST_FRAMEWORK, env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
# Serve built assets from backend/static without collectstatic (CI end-to-end runs).
WHITENOISE_USE_FINDERS = True

if DEBUG:
    INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
    # Containers see the host as a bridge IP, so INTERNAL_IPS does not fit;
    # show the toolbar whenever DEBUG is on at request time.
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": "backend.config.settings.local.show_toolbar"
    }
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]


def show_toolbar(request) -> bool:
    from django.conf import settings

    return settings.DEBUG

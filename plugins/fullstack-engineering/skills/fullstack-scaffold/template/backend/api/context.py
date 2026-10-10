"""Runtime configuration for the frontend.

Rendered into every page as JSON (see templates/base.html) and read once by
frontend/src/config.ts. This is how environment-specific values reach Vue: the
built bundle is identical in staging and production, so nothing environment
specific may be compiled into it. Only public values belong here.
"""

from django.conf import settings


def runtime_config(request) -> dict:
    return {
        "runtime_config": {
            "environment": settings.APP_ENVIRONMENT,
            "version": settings.APP_VERSION,
        }
    }

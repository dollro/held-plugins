from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from backend.api import pages

# The admin has no login of its own: it sends people through allauth, so rate
# limits, MFA and the audience rules apply there too.
admin.site.login = secure_admin_login(admin.site.login)

urlpatterns = [
    path("", pages.home, name="home"),
    # The Vue SPA owns everything below /app/; Django serves the shell page.
    re_path(r"^app(?:/.*)?$", pages.spa, name="app"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include("backend.api.urls")),
]
# >>> sso

if not settings.SSO_ENABLED:
    # The OpenID Connect provider is installed but not configured: answer 404
    # instead of letting it fail on a missing app.
    urlpatterns.append(re_path(r"^accounts/oidc/", pages.not_found))
# <<< sso

urlpatterns.append(path("accounts/", include("allauth.urls")))

if "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns = [path("__debug__/", include("debug_toolbar.urls")), *urlpatterns]

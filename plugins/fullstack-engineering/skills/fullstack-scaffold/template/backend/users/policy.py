"""Login policy for external users: a second factor where MFA_REQUIRED is on."""

# >>> mixed
from allauth.account.authentication import get_authentication_records
# <<< mixed
from allauth.mfa.utils import is_mfa_enabled
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect


def mfa_setup_required(request, user) -> bool:
    """True while a user who must use MFA has not set up a second factor yet."""
    if not settings.MFA_REQUIRED or not user.is_authenticated:
        return False
    # >>> mixed
    if signed_in_via_sso(request):
        # This session came through the identity provider, which enforces MFA.
        return False
    # <<< mixed
    return not is_mfa_enabled(user)
# >>> mixed


def signed_in_via_sso(request) -> bool:
    """Decided by how this session authenticated, not by whether the user has a
    provider link: a password login never counts, even for a linked account."""
    methods = {record.get("method") for record in get_authentication_records(request)}
    return "socialaccount" in methods and "password" not in methods
# <<< mixed


class RequireMfaMiddleware:
    """Send users without a second factor to the MFA setup before anything else.

    allauth asks for the second factor at every login once one exists, so this
    only has to close the gap between first login and setup. API calls get a
    403 instead of a redirect. The realtime service applies the same rule
    through the validate-session endpoint. API keys are exempt by design: they
    are issued by an admin for machine clients and never log in a browser.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Internal endpoints serve other services, not this user's browser.
        self.exempt = (
            "/accounts/",
            settings.STATIC_URL,
            "/api/v1/health/",
            "/api/v1/internal/",
            "/api/v1/auth/logout/",
        )

    def __call__(self, request):
        if not request.path.startswith(self.exempt) and mfa_setup_required(
            request, request.user
        ):
            if request.path.startswith("/api/"):
                return JsonResponse(
                    {"detail": "Set up multi-factor authentication first."}, status=403
                )
            return redirect("mfa_index")
        return self.get_response(request)

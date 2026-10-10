from allauth.account.auth_backends import AuthenticationBackend as AllauthBackend
from django.conf import settings


class AuthenticationBackend(AllauthBackend):
    """allauth's password backend plus the mixed-audience rule.

    With INTERNAL_USERS_SSO_ONLY, staff and every account linked to the company
    identity provider cannot authenticate with a password (not even one set via
    password reset), so internal people always come through the provider and
    its MFA and offboarding.
    SSO logins do not call authenticate(), so they are unaffected.
    """

    def authenticate(self, request, **credentials):
        user = super().authenticate(request, **credentials)
        if user is not None and settings.INTERNAL_USERS_SSO_ONLY and is_internal(user):
            return None
        return user


def is_internal(user) -> bool:
    return (
        user.is_staff
        or user.socialaccount_set.filter(provider=settings.SSO_PROVIDER_ID).exists()
    )

from allauth.account.adapter import DefaultAccountAdapter
# >>> sso
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# <<< sso
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request) -> bool:
        # >>> internal
        # No self-registration with a password: users come from SSO or the admin.
        # <<< internal
        # >>> accounts
        # SIGNUP_OPEN off: users are invited (created in the admin, then they
        # use "Forgot password" to set their own).
        # <<< accounts
        return settings.SIGNUP_OPEN
# >>> sso


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin) -> bool:
        return settings.SSO_AUTO_PROVISION
# <<< sso

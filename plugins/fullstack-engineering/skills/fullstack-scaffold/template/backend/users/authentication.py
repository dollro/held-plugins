from rest_framework import authentication, exceptions

from .models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """`Authorization: Bearer <api key>` for non-browser clients."""

    keyword = "Bearer"

    def authenticate(self, request):
        # Latin-1 never fails to decode; a malformed key then simply does not match.
        header = authentication.get_authorization_header(request).decode("latin-1")
        if not header.startswith(f"{self.keyword} "):
            return None
        api_key = ApiKey.resolve(header.removeprefix(f"{self.keyword} ").strip())
        if api_key is None:
            raise exceptions.AuthenticationFailed("Invalid API key.")
        return api_key.user, api_key

    def authenticate_header(self, request):
        return self.keyword

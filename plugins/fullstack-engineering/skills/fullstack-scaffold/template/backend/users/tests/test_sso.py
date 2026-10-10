import importlib

import pytest
from allauth.socialaccount.providers.openid_connect.views import (
    OpenIDConnectOAuth2Adapter,
)
from django.test import override_settings
from django.urls import clear_url_caches

pytestmark = pytest.mark.django_db

ISSUER = "https://idp.example.com/tenant-id/v2.0"
AUTHORIZE = "https://idp.example.com/tenant-id/oauth2/v2.0/authorize"
PROVIDERS = {
    "openid_connect": {
        "OAUTH_PKCE_ENABLED": True,
        "APPS": [
            {
                "provider_id": "company",
                "name": "Company login",
                "client_id": "client-id",
                "secret": "secret",
                "settings": {"server_url": ISSUER},
            }
        ],
    }
}
SSO_START = "/accounts/oidc/company/login/"
DISCOVERY = {
    "issuer": ISSUER,
    "authorization_endpoint": AUTHORIZE,
    "token_endpoint": "https://idp.example.com/tenant-id/oauth2/v2.0/token",
    "userinfo_endpoint": "https://idp.example.com/oidc/userinfo",
}


def reload_urls() -> None:
    import backend.config.urls

    importlib.reload(backend.config.urls)
    clear_url_caches()


@pytest.fixture
def sso_enabled(monkeypatch):
    # No network in tests: answer the provider's discovery document locally.
    monkeypatch.setattr(
        OpenIDConnectOAuth2Adapter,
        "openid_config",
        property(lambda self: DISCOVERY),
    )
    with override_settings(
        SSO_ENABLED=True, SSO_PROVIDER_ID="company", SOCIALACCOUNT_PROVIDERS=PROVIDERS
    ):
        reload_urls()
        yield
    reload_urls()


def test_without_sso_there_is_no_button_and_no_route(client):
    assert "/accounts/oidc/" not in client.get("/accounts/login/").content.decode()
    assert client.post(SSO_START).status_code == 404


def test_sso_login_redirects_to_the_identity_provider(client, sso_enabled):
    page = client.get("/accounts/login/").content.decode()
    assert SSO_START in page
    assert "Company login" in page
    response = client.post(SSO_START)
    assert response.status_code == 302
    assert response["Location"].startswith(AUTHORIZE)
    assert "code_challenge=" in response["Location"]  # PKCE


def test_sso_handshake_never_starts_on_get(client, sso_enabled):
    response = client.get(SSO_START)
    assert response.status_code == 200  # a confirmation page, not a redirect
    assert "idp.example.com" not in response.get("Location", "")

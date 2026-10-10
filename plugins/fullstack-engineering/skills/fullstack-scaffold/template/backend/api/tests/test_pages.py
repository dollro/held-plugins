import json
import re

import pytest

pytestmark = pytest.mark.django_db


def runtime_config(html: str) -> dict:
    match = re.search(r'<script id="runtime-config"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(match[1])


def test_pages_carry_the_runtime_config(client, settings):
    settings.APP_ENVIRONMENT = "staging"
    config = runtime_config(client.get("/").content.decode())
    assert config == {"environment": "staging", "version": settings.APP_VERSION}


def test_health_reports_version_and_environment(client, settings):
    settings.APP_ENVIRONMENT = "staging"
    body = client.get("/api/v1/health/").json()
    assert body["environment"] == "staging"
    assert body["version"] == settings.APP_VERSION


def test_readiness_checks_database_and_cache(client):
    response = client.get("/api/v1/health/ready/")
    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "checks": {"database": True, "cache": True},
    }

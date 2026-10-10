import pytest
from fastapi.testclient import TestClient

from realtime.main import create_app


class FakeRedis:
    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


@pytest.fixture
def client(monkeypatch):
    app = create_app()
    with TestClient(app) as test_client:
        app.state.redis = FakeRedis()
        yield test_client

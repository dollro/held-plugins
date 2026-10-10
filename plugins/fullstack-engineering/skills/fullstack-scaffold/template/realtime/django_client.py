"""The only way this service learns who a caller is: ask Django over its internal API."""

import logging
from dataclasses import dataclass

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Principal:
    user_id: int
    email: str


class AuthUnavailable(Exception):
    """Django could not be reached. Callers fail closed."""


async def _validate(path: str, payload: dict) -> Principal | None:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            base_url=settings.django_internal_url, timeout=settings.django_timeout_s
        ) as client:
            response = await client.post(
                path,
                json=payload,
                headers={"X-Internal-Secret": settings.internal_api_secret},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Auth validation against Django failed: %s", exc)
        raise AuthUnavailable from exc
    data = response.json()
    if not data.get("valid"):
        return None
    return Principal(user_id=data["user_id"], email=data["email"])


async def validate_session(session_key: str) -> Principal | None:
    return await _validate(
        "/api/v1/internal/validate-session/", {"session_key": session_key}
    )


async def validate_api_key(api_key: str) -> Principal | None:
    return await _validate("/api/v1/internal/validate-key/", {"api_key": api_key})

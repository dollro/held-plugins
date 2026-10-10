"""Who is calling? Browsers bring the Django session cookie; other clients an API key.

Django decides in both cases (internal API). This service never trusts a
cookie on its own and fails closed when Django is unreachable.
"""

from fastapi import HTTPException, Request, status

from .config import get_settings
from .django_client import (
    AuthUnavailable,
    Principal,
    validate_api_key,
    validate_session,
)


def is_cross_site(request: Request) -> bool:
    """True when the browser says the request comes from another site.

    Fetch Metadata first, Origin as fallback (OWASP). Sec-Fetch-Site is only sent
    to trustworthy origins (HTTPS, localhost), and same-origin GETs carry no
    Origin, so a request with neither header is accepted. Cross-origin
    EventSource/WebSocket requests always carry an Origin.
    """
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site is not None:
        return fetch_site not in ("same-origin", "none")
    origin = request.headers.get("origin")
    if origin is None:
        return False
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return (
        origin != f"{proto}://{host}" and origin not in get_settings().allowed_origins
    )


async def authenticate(request: Request) -> Principal:
    """FastAPI dependency for every user-facing endpoint."""
    header = request.headers.get("authorization", "")
    session_key = request.cookies.get(get_settings().session_cookie_name)
    try:
        if header.startswith("Bearer "):
            principal = await validate_api_key(header.removeprefix("Bearer ").strip())
        elif session_key:
            if is_cross_site(request):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "Cross-site request refused"
                )
            principal = await validate_session(session_key)
        else:
            principal = None
    except AuthUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication unavailable"
        ) from exc
    if principal is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return principal

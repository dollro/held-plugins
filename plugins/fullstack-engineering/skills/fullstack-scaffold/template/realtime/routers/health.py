import logging

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

from ..config import get_settings
from ..db import get_sessionmaker

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": get_settings().app_version}


@router.get("/health/ready")
async def ready(request: Request, response: Response) -> dict:
    checks = {"database": False, "redis": False}
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:  # noqa: BLE001 - readiness reports, it never raises
        logger.warning("readiness: database check failed", exc_info=True)
    try:
        checks["redis"] = bool(await request.app.state.redis.ping())
    except Exception:  # noqa: BLE001
        logger.warning("readiness: redis check failed", exc_info=True)
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": all(checks.values()), "checks": checks}

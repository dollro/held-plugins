import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from .config import get_settings
from .db import dispose_engine
from .routers import events, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.redis = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        health_check_interval=30,
        socket_keepalive=True,
    )
    yield
    await app.state.redis.aclose()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    app = FastAPI(
        title="__PROJECT_TITLE__ realtime",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    # No CORS middleware: browsers reach this service through the same origin
    # as Django (the reverse proxy routes /v1/* here, in development too).
    app.include_router(health.router)
    app.include_router(events.router)
    return app


app = create_app()

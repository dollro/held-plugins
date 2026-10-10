"""GET /v1/events: per-user Server-Sent Events, fed by Redis pub/sub.

Django and Celery publish to `user:<id>:events`; this endpoint streams them.
SSE is the default for server-to-client streams (events, agent tokens);
use a WebSocket only when the client must send messages too.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

import anyio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..auth import authenticate
from ..config import get_settings
from ..django_client import Principal

router = APIRouter(prefix="/v1", tags=["events"])
logger = logging.getLogger(__name__)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    # Tell nginx-style proxies not to buffer the stream.
    "X-Accel-Buffering": "no",
}


def user_channel(user_id: int) -> str:
    # Must match backend/api/events.py.
    return f"user:{user_id}:events"


def sse(data: str, event: str | None = None) -> str:
    lines = [f"event: {event}"] if event else []
    lines += [f"data: {line}" for line in data.splitlines() or [""]]
    return "\n".join(lines) + "\n\n"


async def _stream(request: Request, principal: Principal) -> AsyncIterator[str]:
    channel = user_channel(principal.user_id)
    keepalive = get_settings().sse_keepalive_s
    pubsub = request.app.state.redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        yield sse(json.dumps({"channel": channel}), event="ready")
        while not await request.is_disconnected():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=keepalive
            )
            # A comment line keeps proxies and the browser from timing out.
            yield sse(message["data"]) if message else ": keepalive\n\n"
    finally:
        # The surrounding task is usually being cancelled (client gone); shield
        # the cleanup so the Redis connection is always released.
        with anyio.CancelScope(shield=True):
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        logger.info("event stream closed for user %s", principal.user_id)


@router.get("/events")
async def events(
    request: Request, principal: Annotated[Principal, Depends(authenticate)]
) -> StreamingResponse:
    return StreamingResponse(
        _stream(request, principal), media_type="text/event-stream", headers=SSE_HEADERS
    )

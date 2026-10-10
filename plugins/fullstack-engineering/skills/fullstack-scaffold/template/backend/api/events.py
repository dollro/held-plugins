"""Publish per-user events to Redis pub/sub (channel `user:<id>:events`).

Any subscriber can consume them; the realtime service streams them to browsers.
"""

import json
from functools import cache

import redis
from django.conf import settings


def user_channel(user_id: int) -> str:
    return f"user:{user_id}:events"


@cache
def _client() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL)


def publish_user_event(user_id: int, event_type: str, data: dict) -> None:
    payload = json.dumps({"type": event_type, "data": data})
    _client().publish(user_channel(user_id), payload)

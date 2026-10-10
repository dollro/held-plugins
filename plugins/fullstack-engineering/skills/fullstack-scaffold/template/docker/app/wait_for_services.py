"""Block until Postgres and Redis accept connections (max ~60s)."""

import os
import sys
import time
from urllib.parse import urlparse

import psycopg
import redis

DEADLINE = time.monotonic() + float(os.environ.get("WAIT_FOR_SERVICES_TIMEOUT", "60"))


def wait(name: str, check) -> None:
    while True:
        try:
            check()
            print(f"{name} is available", file=sys.stderr)
            return
        except Exception as exc:  # noqa: BLE001 - any failure means "not yet"
            if time.monotonic() > DEADLINE:
                sys.exit(f"{name} not available: {exc}")
            print(f"waiting for {name}...", file=sys.stderr)
            time.sleep(1)


def check_postgres() -> None:
    url = urlparse(os.environ["DATABASE_URL"])
    if url.scheme.startswith("postgres"):
        psycopg.connect(
            os.environ["DATABASE_URL"].replace("+psycopg", ""), connect_timeout=3
        ).close()


def check_redis() -> None:
    redis.Redis.from_url(os.environ["REDIS_URL"], socket_connect_timeout=3).ping()


wait("postgres", check_postgres)
wait("redis", check_redis)

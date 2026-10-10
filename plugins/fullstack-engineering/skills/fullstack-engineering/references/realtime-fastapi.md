# Realtime service: FastAPI

The realtime service holds long-lived connections and streams: Server-Sent Events, WebSockets, LLM token streams and agent runs. It shares PostgreSQL and Redis with Django but owns only its own tables, and it never decides who a user is.

## Async rules

- **Never block the event loop.** No sync I/O (requests, sync DB drivers, file reads of size) inside `async def`. Use async clients (httpx, redis.asyncio, async SQLAlchemy) or move the work to a thread or to Celery. CPU-heavy work goes to Celery.
- **One `AsyncSession` per request or task**, from one `async_sessionmaker(expire_on_commit=False)` created at startup; never share a session across concurrent tasks (`asyncio.gather`). Avoid lazy loading (eager loads or `lazy="raise"`).
- **Lifespan handler** creates and closes shared clients (Redis, engine); no import-time connections.
- **Settings** via pydantic-settings from the same env file as Django; unknown keys ignored. List settings as comma-separated strings, like Django's.
- **FastAPI is pre-1.0** and ships breaking changes in minor releases: install from the lockfile, read release notes before every bump.

## Streaming

- **SSE by default** for server → client (events, tokens, progress): `text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`, a keep-alive comment every ~15 s, stop when the client disconnects. A plain `StreamingResponse` with a small formatter is enough; recent FastAPI versions also ship a built-in SSE response.
- **WebSocket only for two-way traffic.** Then: check `Origin` against an exact allowlist on every handshake, authenticate with the session cookie or the first message (never a token in the URL), limit message size and rate, close sockets on logout.
- **Fan-out through Redis pub/sub** (or streams for replay): one channel per user or topic, published by Django/Celery. No in-process broadcast; it breaks with more than one worker.
- **Proxies must not buffer streams:** flush immediately (Traefik `flushInterval: -1s`, Caddy `flush_interval -1`, nginx `X-Accel-Buffering: no`) and allow long read timeouts.

## Auth bridge

Browser requests carry the Django session cookie (same origin). The service:

1. refuses cookie-authenticated requests that the browser marks as cross-site: `Sec-Fetch-Site` other than `same-origin`/`none`, or an `Origin` that is neither this host nor in `REALTIME_ALLOWED_ORIGINS`;
2. sends the cookie value to Django's internal `validate-session` endpoint (or a Bearer key to `validate-key`) with `X-Internal-Secret`;
3. returns 401 if Django says invalid, 503 if Django cannot be reached (fail closed).

**Pitfall:** browsers send `Sec-Fetch-Site` only to trustworthy origins (HTTPS or `localhost`), and same-origin GETs carry no `Origin`. A check that *requires* either header rejects legitimate browsers on plain-HTTP hosts (for example `http://proxy:8080` in CI). Reject on a cross-site *signal*, accept when neither header is present; cross-origin EventSource and WebSocket requests always send `Origin`.

Cookies are sent per host, not per port, and SameSite treats `localhost:8000` and `localhost:8001` as same-site; still, keep one origin through the proxy so production and development behave the same.

## Data

- Models on the service's own `DeclarativeBase`; Alembic `target_metadata` is exactly that metadata, with its own `version_table` and an `include_object` filter that ignores reflected tables not in the metadata, so autogenerate never proposes to drop Django's tables.
- psycopg 3 async (`postgresql+psycopg://`); rewrite Django's `postgres://` URL in the settings.
- User references are plain integer columns, no foreign keys into Django tables.
- Migrations run in the deploy's migrate step; locally the dev start script may run `alembic upgrade head`.

## Agent workloads

Agents live here and follow `agentic-engineering`. The HTTP layer starts or resumes runs and streams their output (SSE); the LangGraph checkpointer (Postgres) holds run state; long runs are started from a queue, not inside a request.

## Testing

- `TestClient` (or httpx `AsyncClient` with `ASGITransport` and a lifespan manager) with dependencies or module functions monkeypatched; never call Django or a model provider for real in unit tests.
- Test the auth matrix: no credentials (401), cross-site cookie (403), invalid session (401), Django down (503).
- Starlette's test client has been moving away from httpx; follow the current testing docs when warnings appear.

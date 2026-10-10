# CLAUDE.md — __PROJECT_TITLE__ realtime (`realtime/`)

FastAPI service for long-lived connections and streaming under `/v1/` (Server-Sent Events by default, WebSockets only for two-way traffic), and the home for agent workloads. Async SQLAlchemy on the shared Postgres, Redis pub/sub for fan-out. It never authenticates users itself: it validates the Django session cookie or an API key against Django's internal API and fails closed.

## Commands

```bash
task dev:alembic-revision -- "describe change"   # migrations for realtime-owned tables
task test:backend -- realtime                    # realtime tests
task dev:logs -- realtime
```

## Access Points

| Endpoint | Purpose |
|---|---|
| `GET /health`, `/health/ready` | liveness, readiness (DB + Redis) |
| `GET /v1/events` | per-user event stream (SSE) |

## Key Patterns

- Alembic sees only tables on `realtime.db.Base` and uses its own version table; Django's tables are never touched.
- Browsers are authenticated by the Django session cookie, accepted only on same-origin requests (`Sec-Fetch-Site`, Origin allowlist as fallback); other clients send `Authorization: Bearer <api key>`.
- 401 unauthenticated, 403 cross-site, 503 when Django cannot be asked (fail closed).
- Never block the event loop: no sync I/O in `async def`; CPU work goes to Celery.

## Docs

`docs/architecture.md`.

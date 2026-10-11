# Architecture

## Reference shape

```
                Browser (one origin)
                       |  HTTPS
              +--------+---------+
              |  reverse proxy   |  TLS; / -> django, /v1/* -> realtime
              +---+----------+---+
                  |          |
          +-------+--+   +---+-----------+
          |  Django  |<--+  realtime     |  internal API (X-Internal-Secret):
          | web, API |   |  FastAPI      |  validate-session, validate-key
          | admin    |   |  SSE / WS     |
          +--+---+---+   +--+--------+---+
             |   |          |        |
     Celery -+   +-- PostgreSQL -----+        Redis: cache, broker, pub/sub
     worker/beat     (one owner per table)    (Celery publishes, realtime streams)
```

Locally and in CI a small proxy container (Caddy) plays the reverse proxy, so the browser, cookies and streaming behave exactly as in production.

## Contracts

A service can be replaced (another framework, another language) if the replacement keeps these contracts.

| Contract | Rule |
|-|-|
| HTTP API | REST under `/api/v1/`, JSON in and out, errors as `{"detail": "..."}`, describable as OpenAPI. Breaking changes get a new version prefix. |
| Browser auth | One origin. Session cookie (HttpOnly, SameSite, Secure in production) + CSRF header on unsafe methods. |
| Login | Per audience (`identity.md`): the company identity provider (OpenID Connect) for staff, app accounts with verified email and MFA for externals; always through one login layer (allauth). |
| Machine auth | `Authorization: Bearer <api key>`; keys stored hashed, validated by the system of record. |
| Service auth | Internal endpoints under `/api/v1/internal/`, header `X-Internal-Secret`, constant-time compare, fail closed. Never reachable for browsers in a way that matters (no user data without the secret). |
| Streaming | `GET /v1/events` style Server-Sent Events; WebSockets only for two-way traffic. Same auth as the browser contract. |
| Data | Each table has one owning service and one migration system. Others read only. |
| Operations | Config only from env. `/health` (liveness) and a readiness endpoint per service. Migrations as a separate deploy step. Same Task targets in every repo. |

## Choosing the shape

| Question | If yes |
|-|-|
| Do users need realtime updates, streams, long-running agent runs or many open connections? | Add the realtime service (Django + FastAPI). |
| Is it only "refresh when something changed"? | Django only; poll, or SSE from a Django async view. |
| Mostly agents/streaming, few tables, no business admin, identity fully in the company identity provider, coarse roles, team accepts owning the glue? | FastAPI only is acceptable (below). |
| Small model-bound live updates, no agents or streaming? | Django Channels is acceptable. |

Write the decision into `docs/architecture.md` of the repo.

### Why Django + FastAPI as the reference

Django brings what internal tools need on day one: users, permissions, admin, ORM migrations, forms, a mature ecosystem. FastAPI is async-native and Pydantic-first, the natural home for streaming and for the agent stack (`agentic-engineering`: LangGraph, Pydantic AI). The price is a second service and an auth bridge; the reference implementation (fullstack-scaffold) solves both and tests them.

### Option: FastAPI only

Use it only when **all** of these hold: the app is mainly agent runs or streaming; roughly a dozen domain tables or fewer with simple CRUD; no business-user admin (ops views suffice); identity fully delegated to the company identity provider (no local accounts); coarse authorization from the provider's roles or groups; the team accepts owning session, CSRF and admin glue and keeping up with FastAPI's 0.x releases. Exit path: when CRUD, admin, object permissions or reporting grow, move to the Django + FastAPI reference instead of rebuilding Django.

| Component | Choice | Why |
|-|-|-|
| ORM / migrations | SQLAlchemy 2.x (async) + Alembic, separate Pydantic schemas | Most capable and stable; SQLModel is still pre-1.0 |
| Driver | psycopg 3 | Shared with the LangGraph Postgres checkpointer |
| Login | Authlib OIDC against the company identity provider, backend-for-frontend; server-side session in Redis; `__Host-` cookie | Current OAuth guidance for browser apps: no tokens in the browser |
| CSRF | Small middleware: reject unsafe methods unless Fetch Metadata says same-origin (Origin allowlist as fallback), plus a required custom header | CSRF libraries for Starlette are stale or naive |
| Jobs | Procrastinate (Postgres only) or Taskiq (Redis) | Async-native, durable, maintained |
| Agent state | LangGraph Postgres checkpointer | The queue starts runs; the checkpointer holds their state |
| Streaming | FastAPI SSE; WebSocket only if bidirectional; Redis pub/sub for fan-out | Built in; no extra library |
| Admin | SQLAdmin or Starlette-Admin, ops only, behind SSO and a role check | Maintained, far from Django admin |
| Frontend | Proxy serves the built SPA with history fallback; Vite proxy in development | Same origin |
| API client | Generated from OpenAPI (e.g. hey-api), regenerated in CI with a diff check | Typed client without hand-written glue |

Avoid for new code (unmaintained or maintenance-only at last check): fastapi-users, passlib, arq, encode/broadcaster. Re-check status before adopting any auth or job library.

### Option: Django Channels

Fine for small, model-bound live updates: same ORM, sessions and permissions, a Redis channel layer for fan-out. Costs: consumer boilerplate, async transaction limits, WebSocket load inside the web processes. Not for agent workloads or heavy streaming.

## Boundaries that matter

- **Django owns identity.** The realtime service never decides who a user is; it asks Django (session cookie or API key) and fails closed when Django is down.
- **Realtime-owned tables** use plain integer user IDs, not foreign keys into Django's tables, so neither migration system depends on the other.
- **Events, not shared state:** Django and Celery publish to Redis channels named per user or per topic; the realtime service subscribes and streams.

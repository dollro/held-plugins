# Operations: dependencies, deployment, cost, durable execution, protocols

## 1. Dependencies

### Principles

1. **Use `uv` with a committed `uv.lock`.** CI, Docker and production install with `uv sync --frozen`. Install order never matters with a lockfile; without one, results are luck.
2. **Put floor pins on the packages that matter** (the frameworks, the tracing SDK, Pydantic). When the resolver would have to fall back to an old release to satisfy a conflict, the floor makes it fail loudly instead.
3. **Add a CI drift check:** after resolving, compare installed versions with the floors and fail on a mismatch.

   ```bash
   uv sync --frozen
   uv pip list --format json | python scripts/check_floors.py   # compares against your floors
   uv tree --invert --package openai                            # who pulls what, when debugging
   ```

4. **Raise floors to the latest security fix,** not just to the version that happened to work.
5. **Upgrade deliberately:** one framework at a time, reading its changelog and migration guide, with the eval suite run before merging.
6. **Isolate when versions cannot coexist.** If CrewAI and Pydantic AI need different major versions of a shared SDK, choose provider extras that avoid the clash. If that is not possible, run the crews in their own process or service (HTTP or A2A) called from a LangGraph node. Never accept a silent downgrade of one framework to make room for the other.

### Packages

| Need | Install | Avoid |
|---|---|---|
| LangGraph orchestration | `langgraph` with an explicit floor, plus `langchain` if you use `create_agent`, middleware or the Langfuse callback | Relying on transitive versions only |
| Langfuse + LangGraph | `langfuse` + full `langchain` (the callback imports it) | `langchain-core` alone |
| Langfuse + CrewAI | `openinference-instrumentation-crewai` | — |
| Pydantic AI | `pydantic-ai-slim[<provider>]` with only the providers you use (extras exist on both packages in 2.x) | The full package: it pulls default extras including logfire, which conflicts with current Langfuse (in 1.x it pulled every provider SDK, ~500 MB) |
| CrewAI | `crewai` (+ the provider extra, for example `anthropic`) | `crewai-tools` unless you need specific tools; LangChain tool wrappers unless needed |
| Postgres checkpointer | `langgraph-checkpoint-postgres` + `psycopg[pool]` | — |
| Python | 3.12 | 3.10 (async context issues); versions above CrewAI's supported range |

### Current conflict picture (checked 2026-10-08, re-check on every upgrade)

| Topic | State | Consequence |
|---|---|---|
| OpenTelemetry | CrewAI accepts `>=1.42,<2`; Langfuse 4.16+ needs `>=1.45` | Resolves at current versions. The old "install CrewAI first" trick is obsolete. CrewAI below 1.15.22 and Langfuse 4.16+ conflict. |
| OpenAI SDK | CrewAI caps `openai<3`; Pydantic AI's `openai`/`openrouter` extras need `openai>=3` in recent 2.x releases | `pydantic-ai-slim[openrouter]` next to CrewAI silently falls back to an old 2.x. Use `pydantic-ai-slim[anthropic]` (resolves to current versions) or isolate the crews. |
| Anthropic SDK | `crewai[anthropic]` pins an older `anthropic` than current Pydantic AI needs | Check the resolution: install the Anthropic provider on one side only, or isolate. |
| Logfire | Logfire 5.x caps OTel below 1.45; full `pydantic-ai` pulls logfire | Full `pydantic-ai` next to Langfuse 4.16+ silently downgrades Langfuse. Use `pydantic-ai-slim`. |
| Pydantic | CrewAI caps `pydantic<2.13`; Pydantic AI needs `>=2.12` | Pydantic is held at 2.12.x while both are installed. |
| MCP SDK | CrewAI pins the MCP SDK to the 1.x line | The 2.x MCP SDK (stateless spec) cannot be used in the same environment yet. |
| Python | CrewAI supports `<3.14` | Stay on 3.12 or 3.13. |

### Security floors (checked 2026-10-08)

| Package | Floor | Reason |
|---|---|---|
| `langgraph` | `>=1.2.14` | Fix for an advisory affecting 1.2.3–1.2.13; earlier msgpack deserialization advisory |
| `langgraph-checkpoint` | `>=4.1.1` (4.2 recommended) | Unsafe JSON deserialization; cache RCE in versions below 4.0 |
| `langgraph-checkpoint-postgres` / `-sqlite` | `>=3.1.1` | Store namespace prefix matching |
| `langgraph-sdk` | `>=0.4.6` | Custom auth and advisory fixes |

Re-check against the GitHub security advisories of each framework before every release.

### Audit the environment

```bash
python - <<'EOF'
from importlib.metadata import version, PackageNotFoundError
for pkg in ["langgraph", "langchain", "langchain-core", "langgraph-checkpoint", "pydantic",
            "pydantic-ai-slim", "pydantic-ai", "crewai", "langfuse", "opentelemetry-api",
            "openai", "anthropic", "mcp"]:
    try:
        print(f"{pkg:24} {version(pkg)}")
    except PackageNotFoundError:
        print(f"{pkg:24} -")
EOF
```

Use package metadata, not `module.__version__`: some packages, for example `langgraph`, are namespace packages without one.

## 2. Deployment

### Options

| Option | When |
|---|---|
| Task queue workers (Celery, RQ, Arq) | Long-running pipelines triggered by an app; you run the infrastructure |
| LangSmith Deployment (Agent Server, Studio) | Graph-centric services with streaming, threads, cron and human approval built in. Cloud, hybrid or self-hosted; check licensing. |
| Durable workflow engine (Temporal, DBOS) | Runs that span days or must survive infrastructure loss (section 4) |
| Plain web service (FastAPI) | Short, synchronous agent calls |

### Celery workers

```python
import asyncio
import uuid
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from langfuse import get_client, propagate_attributes

celery_app = Celery("refinement", broker="redis://localhost:6379/0")
langfuse = get_client()                    # thread-safe singleton, shared across tasks

@celery_app.task(bind=True, max_retries=2, acks_late=True,   # re-queue if the worker dies
                 time_limit=600, soft_time_limit=540, rate_limit="5/m")
def refine_document_task(self, draft: str, document_id: str | None = None, max_iterations: int = 2):
    document_id = document_id or uuid.uuid4().hex[:12]
    state = {"current_draft": draft, "latest_rationale": "Initial draft.",
             "iteration_count": 0, "max_iterations": max_iterations, "document_id": document_id}
    try:
        with langfuse.start_as_current_observation(as_type="span", name="refine-document"):
            with propagate_attributes(session_id=document_id):
                handler = get_tracing_callback()             # per task, never shared
                config = {"configurable": {"thread_id": document_id},
                          "callbacks": [handler] if handler else []}
                final = asyncio.run(graph.ainvoke(state, config))   # async nodes; resumes on retry
        return {"status": "success", "document_id": document_id,
                "final_draft": final["current_draft"], "rounds": final["iteration_count"]}
    except SoftTimeLimitExceeded:
        raise self.retry(countdown=60)                       # same thread_id resumes from checkpoint
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
    finally:
        langfuse.flush()                                     # export before ack
```

```bash
celery -A tasks worker --pool=prefork --concurrency=2 --prefetch-multiplier=1
# prefork, not eventlet/gevent (they conflict with CrewAI threads); low concurrency for minute-long runs
```

| Checkpointer with workers | Use |
|---|---|
| `None` | Stateless, simplest, no resume |
| Async Postgres | Crash recovery: another worker resumes the same `thread_id` (use synchronous durability with `acks_late`) |
| Redis | Fast, durable alternative |
| In-memory | ❌ Never: it is per process and useless across workers |

- **On shutdown:** drain running graphs (LangGraph 1.2+) so they stop at a step boundary and resume later.
- **Same document in parallel:** take a distributed lock so only one worker handles a document at a time.
- **CrewAI memory across workers:** use a server-backed storage backend, not a shared file system.
- **Tracing in workers:** initialise tracing and instrumentors once per worker process, create a callback handler per task, and flush before the task acknowledges.

### Container

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY pipeline/ pipeline/
COPY main.py .
RUN uv sync --frozen --no-dev
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH"
CMD ["python", "main.py"]
```

Pin the uv image tag in production. Secrets come in at runtime, never at build time.

## 3. Cost model

### Calls per refinement round (3 experts, moderator, writer, memory on)

| Component | Calls per round | Notes |
|---|---|---|
| Expert LLM calls | 1–3 each | Agent reasoning loop, capped by `max_iter` |
| Moderator | 1–2 | +1 when contract parsing or a guardrail retries |
| Writer | 1–2 | Usually one shot |
| **Agent subtotal** | **5–13** | Typically 7–8 |
| Memory recall (embeddings) | ~5 | Shallow recall needs no LLM call |
| Memory save (embeddings) | ~5 | Background |
| Memory analysis and extraction (LLM) | ~8–10 | Cheap tier |
| Memory consolidation (LLM) | 1–3 | Only when duplicates are found |
| **Memory subtotal** | **~15–23** | Mostly cheap tier |
| Tracing | 10–15 spans | No LLM cost |
| **Total per round** | **~20–36** | Typically ~25 |

Price a pipeline from these counts and the **current** price list of your provider (prices change with every model generation). Langfuse shows the real cost per session.

### Levers

- Cheap tier for experts, routing and memory analysis; strong tier only for moderator, writer and judges.
- `max_iter` 5–10 on agents; `max_iterations` 2 for refinement (a third round is usually marginal).
- Prompt caching for stable prefixes (instructions, tool lists, long documents).
- Disable memory consolidation, use shallow recall and a local embedder where quality allows.
- Usage limits per node, so a runaway loop costs a bounded amount.

## 4. Durable execution

| Need | Choice |
|---|---|
| Resume after an interrupt, worker crash or deploy | LangGraph checkpointer (default) with synchronous durability, retry policies and drain |
| Runs over days, guaranteed completion across infrastructure loss, complex compensation | A durable workflow engine: Temporal (a LangGraph plugin exists; check its maturity) or DBOS, or the engine integrations of Pydantic AI for standalone agents |

**One durable engine per run.** Never let a workflow engine and a LangGraph checkpointer both claim to own recovery of the same steps. Under a workflow engine, LLM and tool calls become activities or steps; they must be idempotent or deduplicated.

## 5. Protocols and SDKs

| Protocol / SDK | Use it for | Notes |
|---|---|---|
| **MCP** | Connecting agents to tools and data | Recent spec versions made the protocol stateless and changed elicitation and sampling. Check which spec version your SDKs speak; they differ per framework. Filter tools and pin servers (`security.md`). |
| **A2A** | Agent-to-agent calls across services, teams or vendors | 1.0 is stable and governed by an open foundation. Use it for isolating crews into their own service, too. Validate everything against contracts. |
| **AG-UI** | Streaming agents into front-ends (events, state, tool calls) | 1.0 released; framework adapters may lag. Sanitize history from the browser. |
| **Claude Agent SDK** | A Claude-native agent with its own tool loop inside a node | Same adapter rules; tracing via its OTel support or Langfuse integration. |

## 6. CrewAI Flows as the only framework

For small deployments without checkpointing, human approval steps or graph composition, CrewAI Flows (with built-in state, memory and human feedback) can replace LangGraph.

- **Choose Flows when:** single framework, short runs, no resume needed.
- **Keep LangGraph when:** you need checkpointing, interrupts, time travel, fan-out with reducers, or mixed Pydantic AI and CrewAI nodes.
- **Tracing with Flows:** there is no LangGraph callback, so no node or routing view. CrewAI's OTel instrumentation still captures all agent and LLM calls; wrap each round in a manual span with `propagate_attributes` as in `observability.md`.

```python
import uuid
from crewai.flow.flow import Flow, listen, start

class DocumentRefinementFlow(Flow):
    @start()
    def begin(self):
        self.state["iteration"] = 0
        self.state["document_id"] = uuid.uuid4().hex[:12]
        return self.state["draft"]

    @listen(begin)
    async def refine(self, draft):
        doc_id = self.state["document_id"]
        with langfuse.start_as_current_observation(
                as_type="span", name=f"flow-round-{self.state['iteration'] + 1}"):
            with propagate_attributes(session_id=doc_id):
                memory = create_pipeline_memory(doc_id)
                agents = create_scoped_agents(memory)
                ...  # build tasks, await crew.akickoff()
```

Check the current Flow API (decorators, state models, human feedback) in the Flows docs before you use it.

# Observability: Langfuse over OpenTelemetry

Patterns for the Langfuse SDK 4.x line. Version 4 is "observations-first" and renamed several span APIs. Check the Python SDK docs and upgrade guide (`sources.md`) before using any API named here.

## 1. Three paths into one trace

| Framework | Mechanism | How spans reach Langfuse |
|---|---|---|
| Pydantic AI | `Agent.instrument_all()` (or an instrumentation capability per agent) | OTel spans following the GenAI conventions |
| CrewAI | OpenInference `CrewAIInstrumentor().instrument()` | OTel spans |
| LangGraph | Langfuse LangChain `CallbackHandler`, passed in `config["callbacks"]` | Callback → Langfuse |

There is also a pure-OTel path: the OpenInference instrumentors for LangChain and Pydantic AI. Langfuse accepts OpenInference scopes, so this works when you want one mechanism for everything.

**Langfuse without LangChain installed:** use the `@observe` decorator and `propagate_attributes()` directly, with no callback handler. You lose automatic node and routing spans for LangGraph but keep manual spans and all Pydantic AI and CrewAI OTel spans.

## 2. Initialize once

```python
# pipeline/tracing.py
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def init_tracing() -> bool:
    """Idempotent. Call at process start (web app startup, worker init)."""
    settings = load_settings()
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("Tracing credentials not set, tracing disabled")
        return False

    from langfuse import get_client
    from openinference.instrumentation.crewai import CrewAIInstrumentor
    from pydantic_ai import Agent

    get_client()                                            # registers the OTel exporter
    Agent.instrument_all()                                  # Pydantic AI → OTel
    CrewAIInstrumentor().instrument(skip_dep_check=True)    # CrewAI → OTel
    logger.info("Tracing initialised")
    return True

def get_tracing_callback():
    """Callback handler for one LangGraph invocation, or None.
    Create it INSIDE the propagate_attributes context so it inherits the session."""
    if not init_tracing():
        return None
    from langfuse.langchain import CallbackHandler   # needs the full `langchain` package
    return CallbackHandler()
```

## 3. Session glue

Every span created inside the context inherits the same session, tags and metadata, whether it comes from OTel or from the callback.

```python
from langfuse import get_client, propagate_attributes

langfuse = get_client()

async def run_pipeline(document_id: str, initial_state: dict) -> dict:
    with langfuse.start_as_current_observation(as_type="span", name="document-refinement"):
        with propagate_attributes(
            session_id=document_id,                 # = LangGraph thread_id = agent conversation id
            trace_name="document-refinement",
            tags=["pipeline", "refinement"],
            metadata={"tenant": "acme"},            # string values only
        ):
            handler = get_tracing_callback()
            config = {"configurable": {"thread_id": document_id},
                      "callbacks": [handler] if handler else []}
            result = await graph.ainvoke(initial_state, config)   # async nodes need ainvoke
    langfuse.flush()                                # short-lived processes: always flush
    return result
```

- Set trace-level name and attributes through `propagate_attributes`. Set input and output on the root observation with `update(...)`.
- The old `update_trace` and `start_as_current_span` APIs from v3 no longer exist.
- Trace-level input/output setters remain only for legacy trace-level evaluators. Prefer observation-level evaluators.

### Per-round spans

```python
async def refinement_round_node(state: DocumentRefinementState) -> dict:
    round_no = state["iteration_count"] + 1
    with langfuse.start_as_current_observation(as_type="span", name=f"refinement-round-{round_no}"):
        with propagate_attributes(session_id=state["document_id"],
                                  tags=state.get("trace_tags", []) + [f"round-{round_no}"]):
            ...  # build and run the crew
```

Without the manual span, CrewAI spans would still be captured, but as top-level traces disconnected from the graph.

### Context across subgraphs and threads

`propagate_attributes` uses the current context. Nodes that run in other threads, processes or workers lose it. Re-establish it from values carried in state (`document_id`, `trace_tags`), as in the per-round span above. The orchestrator sets them when it starts the graph. Current CrewAI versions carry context into their async task threads; check old versions with a test trace.

## 4. What gets exported

- **v4 exports only LLM-relevant spans by default:** Langfuse spans, spans with `gen_ai.*` attributes, and known LLM instrumentation scopes. Worker, HTTP and database spans are dropped, which can leave children without a parent. Use the export-filter hook (`should_export_span` in current versions) to keep the spans you need, and the debug flag to see what is filtered.
- **The OTel GenAI semantic conventions are still in development.** Do not hard-code dashboards or alerts on `gen_ai.*` attribute names; use Langfuse's own fields.
- **Privacy:** switch off prompt and response capture where content includes personal data. Pydantic AI instrumentation has a content-capture switch; Langfuse has masking. Never put secrets in metadata.

## 5. Expected trace hierarchy

```
Session: {document_id}
└─ document-refinement                    (root span)
   ├─ LangGraph: refine_document          (callback, node)
   │  ├─ refinement-round-1               (manual span)
   │  │  └─ crew kickoff                  (OTel)
   │  │     ├─ agent task: expert technical (+ LLM calls)
   │  │     ├─ agent task: expert growth
   │  │     ├─ agent task: expert legal
   │  │     ├─ agent task: moderator
   │  │     └─ agent task: writer
   │  ├─ LangGraph: should_continue
   │  └─ refinement-round-2 …
   └─ research (Pydantic AI agent run, tool calls, LLM calls)
```

If the trace doesn't look like this, debug the context propagation before anything else.

## 6. Environment

```bash
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"      # EU cloud; or your self-hosted URL
# LANGFUSE_BASE_URL="https://us.cloud.langfuse.com" # US cloud
LANGFUSE_TRACING_ENVIRONMENT="production"           # separates dev/staging/prod
LANGFUSE_RELEASE="<git sha>"                        # ties traces to a deploy
# LANGFUSE_SAMPLE_RATE="0.2"                        # sampling for high volume
```

`LANGFUSE_HOST` is the deprecated name for the base URL. A self-hosted server must match the SDK's minimum server version.

## 7. Prompts, sessions and cost

- **Langfuse prompt management:** version prompts outside the code and link the prompt version to traces through the propagation context. Prompt changes then show up in eval comparisons.
- **Tracing adds no LLM cost.** It is async export of metadata: roughly 30–50 spans for a three-round pipeline.
- **Cost per session** is rolled up from the model usage on each generation. Keep model prices current in Langfuse when you use custom models or gateways.

## 8. Validation and agent metrics

```python
from dataclasses import dataclass

@dataclass
class AgentMetrics:
    validation_attempts: int = 0
    validation_failures: int = 0
    total_retries: int = 0
    avg_node_latency_ms: float = 0.0
    total_execution_time_ms: float = 0.0

    @property
    def validation_failure_rate(self) -> float:   # alert > 0.3: model drift
        return self.validation_failures / self.validation_attempts if self.validation_attempts else 0.0

    @property
    def avg_retry_depth(self) -> float:           # alert > 1.5: cost degradation
        return self.total_retries / self.validation_attempts if self.validation_attempts else 0.0
```

Record them as scores or metadata on the run's trace, so they can be filtered per node, model and prompt version.

## 9. Langfuse or LangSmith

| Aspect | Langfuse | LangSmith |
|---|---|---|
| Self-hosting | Yes (open-source core, MIT; enterprise features under a separate licence) | Enterprise add-on |
| EU data residency | EU cloud or self-hosted | Check current regions |
| CrewAI / Pydantic AI | Via OTel, no extra wrappers | Via OTel |
| LangGraph | Callback handler | Native, deepest integration (Studio, deployment) |
| Sessions | `propagate_attributes` | Native threads |
| Evals and datasets | Experiments, LLM-as-judge, CI action | Datasets, evaluators |

**Default here is Langfuse:** it can be self-hosted, fits GDPR-sensitive data and treats all three frameworks equally. LangSmith is the choice when the project runs on LangSmith Deployment. The two can coexist.

```python
# LangSmith-only setup (alternative)
from langsmith.integrations.otel import configure as configure_langsmith
from pydantic_ai import Agent

configure_langsmith(project_name="production")
Agent.instrument_all()
```

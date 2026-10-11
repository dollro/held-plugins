# LangGraph: state, orchestration, human-in-the-loop, persistence

Patterns for the LangGraph 1.x line. Before you use any API named here, check the current docs and changelog (`sources.md`). Features marked *(1.2+)* or *beta* move fastest.

## 1. State

### Hybrid state: TypedDict envelope, Pydantic payload

The official docs list TypedDict as the main state pattern, dataclasses for defaults, and Pydantic state for recursive validation (slower). Prebuilt `create_agent` does not accept Pydantic state. The standard here: a TypedDict envelope with Pydantic payloads stored as JSON.

```python
# pipeline/schemas.py
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

class ResearchArtifact(BaseModel):
    artifact_id: UUID
    url: HttpUrl
    summary: str = Field(min_length=50, max_length=2000)
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_type: Literal["web", "academic", "internal"]
    timestamp: datetime          # model_dump(mode="json") turns UUID/datetime into strings

class TaskResult(BaseModel):
    task_id: UUID
    status: Literal["pending", "in_progress", "completed", "failed"]
    output: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)

class CrewOutput(BaseModel):
    crew_name: str
    tasks_completed: int
    final_output: str
    agent_contributions: list[dict] = Field(default_factory=list)
    execution_time_seconds: float
```

Use `Literal[...]` instead of regex patterns for enumerations, and `model_config = ConfigDict(...)` plus `@field_serializer` instead of the Pydantic v1 `class Config: json_encoders`.

```python
# pipeline/state.py
import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict

def merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}

class PipelineState(TypedDict, total=False):
    """Envelope passed between nodes.
    1. TypedDict envelope   2. Pydantic payloads stored as JSON dicts
    3. Reducers on keys written by parallel branches   4. total=False: return only changed keys
    """
    query: str
    # append-only payloads (JSON dicts of Pydantic models)
    artifacts: Annotated[list[dict], operator.add]
    task_results: Annotated[list[dict], operator.add]
    crew_outputs: Annotated[list[dict], operator.add]
    # operational
    current_step: str
    retry_count: int
    max_retries: int
    last_error: str | None        # short, LLM-readable message that drives routing
    error_detail: dict | None     # ErrorSnapshot (JSON) when the traceback matters
    correction: str | None        # set by the fixer, read and cleared by the source node
    review_error: str | None
    cumulative_tokens: Annotated[int, operator.add]
    phase_token_usage: Annotated[dict, merge_dicts]
    # routing
    next_action: Literal["research", "analyze", "crew_task", "human_review", "end"] | None
    requires_human_approval: bool
```

```python
def create_initial_state(query: str = "", max_retries: int = 3) -> PipelineState:
    return PipelineState(
        query=query, artifacts=[], task_results=[], crew_outputs=[],
        current_step="entry", retry_count=0, max_retries=max_retries,
        last_error=None, review_error=None, next_action=None,
        requires_human_approval=False, cumulative_tokens=0)
```

Conversational graphs only add `messages: Annotated[list[AnyMessage], add_messages]`. Task pipelines keep pure domain fields.

For iterative pipelines, a flat state is enough:

```python
class DocumentRefinementState(TypedDict, total=False):
    current_draft: str
    latest_rationale: str
    iteration_count: int
    max_iterations: int
    document_id: str      # memory scope, trace session and thread_id
    trace_tags: list[str] # re-establishes tracing context inside nodes (observability.md)
    last_error: str | None
    retry_count: int
    max_retries: int
```

### Inflate and deflate

Checkpointers serialize state at every step. Pydantic objects come back as dicts, and UUIDs and datetimes come back as strings. So deflate at node exit and inflate at node entry.

```python
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

def deflate(model: BaseModel) -> dict:
    return model.model_dump(mode="json")

def inflate(data: dict | BaseModel | None, cls: type[T]) -> T | None:
    if data is None:
        return None
    if isinstance(data, cls):
        return data
    if isinstance(data, dict):
        return cls.model_validate(data)
    raise TypeError(f"Cannot inflate {type(data)} to {cls}")

def inflate_list(items: list, cls: type[T]) -> list[T]:
    return [inflate(i, cls) for i in items if i is not None]
```

### Errors in state

Never store exception objects. They are not JSON and push the serializer toward unsafe fallbacks.

```python
import traceback
from datetime import datetime, timezone
from pydantic import BaseModel

class ErrorSnapshot(BaseModel):
    error_type: str
    message: str
    traceback_str: str
    timestamp: str

    @classmethod
    def from_exception(cls, e: Exception) -> "ErrorSnapshot":
        return cls(error_type=type(e).__name__, message=str(e),
                   traceback_str=traceback.format_exc(),
                   timestamp=datetime.now(timezone.utc).isoformat())
```

### Schema evolution for persisted threads

Threads can resume days later with old state. Add fields as optional first, deploy, and only remove the old fields after every thread that might still use them has finished. Never rename a key in one step.

## 2. Graph topology and routing

```python
# pipeline/graph.py
from langgraph.graph import StateGraph, START, END

def build_workflow() -> StateGraph:
    """
    START -> router -+-> research --> validator -+-> router
                     +-> analyzer --> validator -+
                     +-> content_crew > validator+
                     +-> human_approval ---------+
                     +-> END            fixer <--+ (retry) -> back to source
    """
    g = StateGraph(PipelineState)
    g.add_node("router", router_node)
    g.add_node("research", research_node)
    g.add_node("analyzer", analyzer_node)
    g.add_node("content_crew", crew_node)
    g.add_node("validator", validator_node)
    g.add_node("fixer", fixer_node)
    g.add_node("human_approval", human_approval_node)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s.get("next_action") or "end", {
        "research": "research", "analyze": "analyzer", "crew_task": "content_crew",
        "human_review": "human_approval", "end": END})
    for node in ("research", "analyzer", "content_crew"):
        g.add_edge(node, "validator")
    g.add_conditional_edges("validator", route_after_validation,
                            {"success": "router", "retry": "fixer", "fatal": END})
    g.add_conditional_edges("fixer", lambda s: s.get("current_step", "research"), {
        "research": "research", "analyzer": "analyzer", "content_crew": "content_crew"})
    g.add_conditional_edges("human_approval", route_after_review,
                            {"again": "human_approval", "router": "router", "end": END})
    return g

def route_after_validation(state: PipelineState) -> str:
    # One retry budget per run here; reset retry_count on success for a per-step budget.
    if state.get("last_error") is None:
        return "success"
    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return "fatal"
    return "retry"
```

### Single-node loop for iterative refinement

```python
def build_refinement_graph(checkpointer=None):
    g = StateGraph(DocumentRefinementState)
    g.add_node("refine_document", refinement_round_node)   # crewai.md
    g.add_edge(START, "refine_document")
    g.add_conditional_edges("refine_document", should_continue,
                            {"continue": "refine_document", "end": END})
    return g.compile(checkpointer=checkpointer)

def should_continue(state: DocumentRefinementState) -> str:
    if state.get("retry_count", 0) >= state.get("max_retries", 2):
        return "end"                       # crew keeps failing: stop, last_error explains why
    return "end" if state["iteration_count"] >= state["max_iterations"] else "continue"
```

Every loop needs an exit that does not depend on success: here the retry budget ends a run whose crew keeps failing.

Ways to extend the stop condition:

- **Quality:** a scoring agent rates the result, and the loop stops at a threshold.
- **Delta:** the embedding similarity between drafts.
- **Memory:** the latest ruling raised no new issues.
- **Budget:** the token or cost budget is exhausted.
- **Human:** an interrupt node decides.

### Router: heuristics first, typed LLM fallback

```python
from typing import Literal
from pydantic import BaseModel
from pydantic_ai import Agent

class RouterDecision(BaseModel):
    next_action: Literal["research", "analyze", "crew_task", "human_review", "end"]
    reasoning: str
    requires_human_approval: bool = False

router_agent = Agent(name="router", output_type=RouterDecision,
                     instructions="Choose the next pipeline step from the state summary.")

async def router_node(state: PipelineState) -> dict:
    artifacts, results = state.get("artifacts", []), state.get("task_results", [])
    if state.get("requires_human_approval"):
        decision = RouterDecision(next_action="human_review", reasoning="approval requested",
                                  requires_human_approval=True)
    elif len(artifacts) >= 3 and not any(r.get("status") == "completed" for r in results):
        decision = RouterDecision(next_action="analyze", reasoning="research complete")
    elif results and all(r.get("status") == "completed" for r in results):
        decision = RouterDecision(next_action="end", reasoning="all tasks completed")
    else:  # ambiguous: LLM, constrained to valid node names, cheap tier
        result = await router_agent.run(summarise_state(state), model=get_model("bolt"))
        decision = result.output
    return {"next_action": decision.next_action,
            "requires_human_approval": decision.requires_human_approval,
            "current_step": "router"}
```

### Fan-out and commands

- **`Send`** runs map-reduce over items, for example one research call per section. A reducer on the target key collects the results.
- **`Command(goto=..., update=...)`** lets a node update state and route in one return. Declare the possible targets so the graph renders correctly.
- **Use LangGraph fan-out for parallel work** rather than framework-internal parallelism. It keeps tracing context and checkpoints intact.

### Runtime context instead of config

Pass run-scoped, non-state values (tenant, model tier, user) through a context schema, not through state or `config["configurable"]`.

```python
from dataclasses import dataclass
from langgraph.runtime import Runtime

@dataclass
class PipelineContext:
    tenant: str
    run_id: str = ""                 # business ID: Langfuse session, thread_id, agent conversation
    model_tier: str = "workhorse"
    search_client: object | None = None   # clients are context, never state

g = StateGraph(PipelineState, context_schema=PipelineContext)

def node(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict:
    tier = runtime.context.model_tier
    ...

graph.invoke(inputs, config, context=PipelineContext(tenant="acme"))
```

`runtime` also exposes execution info (thread, run, attempt number). Use the attempt number to switch to a fallback model on retries.

### Subgraphs

Put iteration logic in a subgraph with its own state rather than cluttering the parent topology. Choose the subgraph's persistence deliberately:

- **Per invocation** (the default): the subgraph starts fresh each time it is called.
- **Per thread**: the subgraph keeps its own history across calls.
- **Stateless**: no persistence at all.

Check the current flag values in the subgraph docs. Two ways to wire one in:

```python
# 1. Shared keys: add the compiled subgraph directly as a node
parent.add_node("refinement", build_refinement_graph())

# 2. Different schema: call it inside a node and map state in and out
async def refinement_node(state: PipelineState) -> dict:
    out = await refinement_graph.ainvoke({"current_draft": state["draft"], "iteration_count": 0,
                                          "max_iterations": 2, "document_id": state["doc_id"]})
    return {"draft": out["current_draft"]}
```

## 3. Human-in-the-loop

### One interrupt per node, loop via edges

A resumed node re-runs from its first line. A `while True` loop around `interrupt()` therefore replays every earlier pass on each resume. Pause once, validate, and route back via an edge on bad input.

```python
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError, model_validator
from langgraph.types import interrupt

class HumanFeedback(BaseModel):
    action: Literal["approve", "reject", "revise"]
    comments: str | None = Field(default=None, max_length=1000)
    revised_content: str | None = None

    @model_validator(mode="after")
    def _revise_needs_content(self):
        if self.action == "revise" and not self.revised_content:
            raise ValueError("revise requires revised_content")
        return self

def human_approval_node(state: PipelineState) -> dict:
    answer = interrupt({                       # newer versions also accept a typed response schema
        "message": "Human review required",
        "latest_output": (state.get("task_results") or [None])[-1],
        "previous_error": state.get("review_error"),
        "expected_schema": HumanFeedback.model_json_schema(),
    })
    try:                                       # validate the answer, never wrap interrupt() itself
        feedback = HumanFeedback.model_validate(answer)
    except ValidationError as e:
        return {"review_error": str(e)}        # route_after_review sends us back here
    if feedback.action in ("approve", "reject"):          # the human decision is final: END
        update = {"review_error": None, "next_action": "end", "requires_human_approval": False}
        if feedback.action == "reject":
            update["last_error"] = f"Human rejected: {feedback.comments}"
        return update
    revised = TaskResult(task_id=uuid4(), status="completed", confidence=1.0,
                         output=feedback.revised_content, metadata={"source": "human"})
    return {"review_error": None, "next_action": None, "requires_human_approval": False,
            "task_results": [revised.model_dump(mode="json")]}   # router decides what follows

def route_after_review(state: PipelineState) -> str:
    if state.get("review_error"):
        return "again"                                   # invalid answer: ask again
    return "end" if state.get("next_action") == "end" else "router"
```

Rules:

- **Never wrap `interrupt()` in a bare try/except.** It works by raising.
- **Keep the order of interrupts identical across runs.** Resume values are matched by position.
- **Side effects before an interrupt run again on resume.** Make them idempotent, or move them into their own node.

### Resume and inspect

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "doc-123"}}
out = await graph.ainvoke(initial_state, config, version="v2")   # typed output: .value, .interrupts
if out.interrupts:
    await graph.ainvoke(Command(resume={"action": "approve", "comments": "ok"}), config, version="v2")

snapshot = graph.get_state(config)             # current values, next nodes
for past in graph.get_state_history(config):   # time travel
    print(past.metadata.get("step"), past.created_at)
```

On the 1.x line, the typed output (`version="v2"`) is opt-in, and dict access on it is deprecated. For UIs, prefer the event-streaming API for messages, values and interrupts (check its stability status in the docs). `interrupt_before` and `interrupt_after` at compile time are debugging and testing tools, not the human-in-the-loop mechanism.

### Validate manual state edits

```python
def validate_state_edit(proposed: dict) -> tuple[bool, str]:
    errors = []
    for i, a in enumerate(proposed.get("artifacts", [])):
        try:
            ResearchArtifact.model_validate(a)
        except ValidationError as e:
            errors.append(f"artifact {i}: {e}")
    return (not errors, "\n".join(errors))

ok, err = validate_state_edit(changes)
if ok:
    graph.update_state(config, changes)   # as_node=... to apply as if a node wrote it
```

## 4. Persistence

### Checkpointer selection

| Environment | Checkpointer | Notes |
|-|-|-|
| Tests, local dev | `InMemorySaver` | Lost on restart (`MemorySaver` is only an old alias) |
| Production | `AsyncPostgresSaver` with a connection pool | Durable, multi-worker, resume on another worker |
| Production alternatives | Redis (maintained by Redis Inc.), MongoDB, SQLite (single host) | Check maintenance status and security advisories |
| Stateless workers | `None` | No time travel, no human approval steps, simplest |

With a checkpointer, every call needs `{"configurable": {"thread_id": ...}}`. Use the run's business ID.

### Hardened production checkpointer

```python
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer

# Strict deserialization: set LANGGRAPH_STRICT_MSGPACK=true (or pass an explicit
# allowlist of modules to the serializer). The default only warns on unknown types.
serde = EncryptedSerializer.from_pycryptodome_aes()   # key from LANGGRAPH_AES_KEY

async def make_checkpointer(db_uri: str) -> AsyncPostgresSaver:
    pool = AsyncConnectionPool(db_uri, max_size=10, open=False,
                               kwargs={"autocommit": True, "row_factory": dict_row})
    await pool.open()
    saver = AsyncPostgresSaver(pool, serde=serde)
    await saver.setup()      # run once per deploy (migrations)
    return saver
```

- `from_conn_string(...)` is a **context manager** (`with ... as saver:`), not a factory that returns a saver.
- Pickle fallback is off by default in current versions. Keep it off and never pass objects that would need it.
- Encrypt checkpoints that contain personal or confidential data. Rotating the key requires a migration plan.

### Durability modes

Choose how eagerly checkpoints are written:

- **On exit only**: fastest; on a crash the run restarts from scratch.
- **Asynchronously** (the default): fast; the last step can be lost.
- **Synchronously** before the next step: no loss. Pair it with worker re-queueing (`acks_late`).

Check the parameter name in the persistence docs; the old `checkpoint_during` flag is deprecated.

## 5. Fault tolerance *(1.2+)*

Set the policies once for all nodes, then override per node:

- **Retry policy:** attempts, backoff and which exceptions to retry (transient API errors, not validation errors, which belong to the fixer loop).
- **Timeout:** run timeout and idle timeout per node (async nodes).
- **Error handler:** receives the node error and returns a `Command`, for example routing to a compensation or fallback node. It still runs after a crash.
- **Cache policy:** TTL caching for deterministic, expensive nodes. Pass a cache when you compile the graph.
- **Graceful drain:** on SIGTERM, request a drain. Running graphs stop at the next step boundary and can resume.

```python
from langgraph.types import RetryPolicy

g.set_node_defaults(retry_policy=RetryPolicy(max_attempts=3))   # plus timeout / error_handler / cache_policy
g.add_node("research", research_node, retry_policy=RetryPolicy(max_attempts=5))
```

Exact class names for timeouts, error handlers and drain control are listed in the fault-tolerance docs; verify them before use.

## 6. Compile

```python
def compile_graph(checkpointer=None, cache=None):
    return build_workflow().compile(checkpointer=checkpointer, cache=cache)
```

- Compile once per process and reuse the compiled graph. It is safe to share; callback handlers and configs are per invocation.
- **Async nodes need async invocation:** `await graph.ainvoke(...)` / `astream(...)`. From sync code (a Celery task, a script), wrap the call in `asyncio.run(...)`. Calling `.invoke()` on a graph with async nodes fails.
- Async context propagation (stream writers, tracing context) needs Python 3.11 or later; the project baseline is in `operations.md`.

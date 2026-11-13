# Architecture

## Core paradigm

A deterministic harness around probabilistic engines. In this picture:

- **LangGraph** is the nervous system: workflow control.
- **Pydantic** is the immune system: data integrity.
- **Pydantic AI** is the specialist: one agent, typed. Several of them in a subgraph form a team.
- **CrewAI** (optional) is a packaged alternative for teams with scoped memory (`SKILL.md` §1 lists when to opt in).
- **Langfuse** is the flight recorder.

```
+-----------------------------------------------------------------+
|                    LangGraph (control plane)                    |
|  +----------+    +----------+    +----------+    +----------+  |
|  |  Router  |--->| Pydantic |--->|  Team    |--->| Validator|  |
|  |   node   |    | AI node  |    | subgraph |    |   node   |  |
|  +----------+    +----------+    +----------+    +----------+  |
|        +--------------+---------------+---------------+         |
|                 Shared typed state (TypedDict + Pydantic)        |
+-----------------------------------------------------------------+
```

## Component responsibilities

| Layer | Component | Responsibility | Failure handling |
|-|-|-|-|
| Control flow | LangGraph | Sequence, loops, branches, cross-step state, persistence, interrupts | Routes to retry, fixer or end by edge logic; node retry/timeout/error-handler policies |
| Data integrity | Pydantic | State payloads, contracts, validation, serialization | `ValidationError` feeds the validator/fixer loop |
| Single-agent execution | Pydantic AI | Typed agent with dependency injection, tools, structured output | Output validators and an output retry budget inside the agent |
| Multi-agent collaboration | LangGraph subgraph of Pydantic AI agents (CrewAI optional) | Role agents, fan-out, moderator, delegation via agent-as-tool | Output validators per role agent, failed roles collected in state, moderator works with what arrived |
| Cognition | LLM | Content, reasoning, tool calls | Raw material, always shaped by validation |
| Persistence | Checkpointer | State snapshot at every step, time travel, resume after interrupt or crash | Hardened serializer, durability mode |
| Memory | Nudge in state + a scoped retrieval tool (CrewAI memory if opted in) | Deterministic context plus semantic recall, scoped per role | Graceful degradation: memory failure → defaults |
| Observability | Langfuse over OTel (LangSmith as an alternative) | Traces, sessions, cost, latency, prompts, evals | Async export, no LLM cost |

## Adapter pattern

LangGraph owns the workflow; framework agents are wrapped as node functions.

```
LangGraph node types
  Standard nodes      → pure functions: routing, validation, preprocessing
  Pydantic AI nodes   → single-agent tasks with typed output
  Team subgraphs      → several Pydantic AI role agents (fan-out, moderator)
  CrewAI nodes        → only if opted in: crews as one node
  Interrupt nodes     → human decisions (one interrupt per node)
  Subgraphs           → iterative sub-flows with their own state
```

Every adapter does the same four steps:

1. **Extract and inflate:** read the needed keys from state and `model_validate()` them.
2. **Run** the framework agent or crew with injected dependencies and a model from the factory.
3. **Validate** the result against its contract.
4. **Deflate:** return only changed keys, as `model_dump(mode="json")`. On failure, return `last_error`, `retry_count + 1` and `current_step`.

### Handler pattern for domain I/O

Documents and other domain inputs enter and leave the pipeline through handlers, so the graph never knows file formats:

- `BaseHandler` (abstract) with `extract()` → pipeline → `apply()`; one handler per format (`handlers/pdf.py`, …).
- A stable Pydantic contract (for example `Section` in, `SectionOptimized` out) sits between the handlers and the graph; state holds `sections: list[dict]`.
- Format metadata is opaque to the agents: it is stripped before anything reaches an LLM and carried through untouched for `apply()`.

Alternatives inside a node, under the same adapter rules:

- **LangChain `create_agent` with middleware**, when a LangChain-native agent with built-in middleware (human approval, retries, summarisation, PII) fits better than Pydantic AI. Note that it does not take Pydantic state.
- **The Claude Agent SDK**, for a Claude-native agent with its own tool loop.

## Layered view with observability

```
+---------------------------------------------------------------------+
|  Langfuse (observability)                                           |
|  - session = business ID (e.g. document_id) groups all rounds       |
|  - LangGraph nodes via callback handler                             |
|  - Pydantic AI (and CrewAI, if used) via OTel                       |
|  +-------------------------------------------------------------+    |
|  |  LangGraph (orchestration)                                  |    |
|  |  - owns iteration loop, global state, routing, persistence  |    |
|  |  +-------------------------------------------------------+  |    |
|  |  |  Pydantic AI / optional CrewAI (execution)            |  |    |
|  |  |  memory scoped per pipeline run                       |  |    |
|  |  +-------------------------------------------------------+  |    |
|  +-------------------------------------------------------------+    |
+---------------------------------------------------------------------+
```

## Key design patterns

1. **Hybrid state:** a TypedDict envelope around Pydantic payloads.
2. **Adapter pattern:** framework agents wrapped as node functions.
3. **Inflate/deflate:** explicit serialization boundaries at node entry and exit.
4. **Validator node topology:** generation and validation in separate nodes.
5. **Moderator shield:** experts never talk directly to downstream consumers; a moderator harmonises their output.
6. **Pydantic contracts:** inter-agent output is typed JSON, not free text.
7. **Dual context:** a nudge (push, deterministic) plus scoped memory (pull, semantic).
8. **Fresh instances per call:** no shared mutable agents or crews.
9. **Memory scoping:** access is enforced in the memory layer, not only in prompts.
10. **Session-grouped tracing:** all rounds of one run sit in one session.
11. **One durable engine per run:** the checkpointer, unless an explicit durable workflow engine owns the run.

## What owns what when frameworks overlap

| Overlap | Decision |
|-|-|
| Pydantic AI graphs / durable execution vs LangGraph | Inside a LangGraph node, Pydantic AI runs the single-agent loop only. Its durable execution is for standalone agent services. |
| CrewAI Flows vs LangGraph | Don't nest a Flow orchestrator in a node. Flows can replace LangGraph for small single-framework deployments without checkpointing or human approval steps (`operations.md`). |
| CrewAI checkpointing vs LangGraph checkpointer | Leave CrewAI checkpointing off inside nodes. Use it only for long crews that must resume on their own. |
| Pydantic AI deferred tools vs LangGraph interrupts | The agent defers; the graph interrupts (`pydantic-ai.md`). |

## Project structure

Organise by **pipeline phase**, not by framework.

```
project/
  pyproject.toml
  uv.lock
  pipeline/
    orchestrator.py  # entry point, run_pipeline(), tracing context
    graph.py         # StateGraph builder + node adapters, node defaults
    state.py         # TypedDict graph state
    schemas.py       # Pydantic output models and contracts
    models.py        # model factory (get_model; get_crewai_llm if CrewAI is used)
    research.py      # Pydantic AI agents + adapters
    tracing.py       # Langfuse/OTel init
    handlers/        # domain I/O adapters (extract/apply)
      base.py
      pdf.py
    refinement/      # multi-agent refinement subpackage
      schemas.py     # inter-agent contracts
      prompts.py     # prompt builders
      roles.py       # role specs + Pydantic AI role agents
      memory.py      # scoped retrieval (or CrewAI memory factory if opted in)
      loop.py        # refinement subgraph
    prompts/
  evals/             # datasets, evaluators, judge prompts
  tests/
    unit/
    integration/
    conftest.py
  main.py
```

Keep files and functions within the length limits of `engineering-standards`. Split a growing `graph.py` by phase before it crosses them.

## Quick reference card

```
STATE        TypedDict(total=False) envelope + Pydantic payloads as model_dump(mode="json")
             reducers on parallel keys; domain fields only in task pipelines
INFLATE      Model.model_validate(data) at node entry; errors → last_error (+ ErrorSnapshot)
MODELS       TIERS (brain / workhorse / bolt) → get_model() (+ get_crewai_llm() if CrewAI is used)
NODES        plain function | Pydantic AI adapter | team subgraph (Send fan-out → moderator)
             | interrupt node (one interrupt) | subgraph | CrewAI adapter (optional, fresh crew)
VALIDATION   in-agent validator/guardrail → validator node → fixer → source; budgets everywhere
HITL         one interrupt() per node, typed answer, loop via edge; tool approval = deferred → interrupt
PERSISTENCE  InMemorySaver (tests) | AsyncPostgresSaver (prod) | None (stateless); thread_id always
             strict msgpack, encryption at rest, durability mode, node retry/timeout/error handler
TRACING      init once: Agent.instrument_all() (+ CrewAIInstrumentor if used); CallbackHandler per invocation
             inside propagate_attributes(session_id=business id); flush in short-lived processes
DEPENDENCIES uv.lock + floors + CI drift check; with CrewAI: isolate crews if SDK majors clash
TESTING      ALLOW_MODEL_REQUESTS=False; TestModel/FunctionModel; InMemorySaver; evals in CI
```

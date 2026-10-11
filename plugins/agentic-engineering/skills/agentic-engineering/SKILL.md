---
name: agentic-engineering
description: "Architecture standards for production agentic AI systems on a reference stack: LangGraph orchestration, Pydantic AI single agents, CrewAI teams, Pydantic contracts, Langfuse/OpenTelemetry tracing. Covers state, model tiers, validation loops, human-in-the-loop, persistence, security, testing and evals. Use when someone designs, builds, reviews or debugs an agent, multi-agent system, graph, crew, agent tracing or evals, even if no framework is named. Not for PR size or CLAUDE.md (engineering-standards)."
---

# Agentic Engineering

Standards for agentic systems that run stably in production: a deterministic harness (LangGraph + Pydantic) around probabilistic engines (LLMs).

This file holds the **principles and guardrails**. They change slowly. The `references/` hold short, idiomatic code for the current major versions. The frameworks change fast, so **the official docs win over every snippet here**.

## Before writing framework code

1. **Check the baseline.** The reference stack targets the latest stable major version of each framework:

   | Component | Major line | Role |
   |-|-|-|
   | LangGraph (+ langchain, langchain-core) | 1.x | Orchestration, state, persistence, human-in-the-loop |
   | Pydantic AI | 2.x | Single-agent execution |
   | CrewAI | 1.x | Multi-agent teams, scoped memory |
   | Pydantic | 2.x | Contracts, validation, serialization |
   | Langfuse SDK | 4.x | Tracing, sessions, prompts, evals |
   | OpenTelemetry | 1.x | Transport for spans |
   | Python | 3.12 (supported range is set by the strictest package, see `references/operations.md`) | |

   This table was last checked on 2026-10-08. If a newer major line has shipped, read its migration guide before building and flag the gap to the person you are working with.
2. **Verify the API you are about to use** against the current docs, changelog or migration guide listed in `references/sources.md`. Use a docs MCP server such as context7 when one is available, or read the installed package source. Snippets here show the pattern, not a guaranteed signature.
3. **Read the reference for the part you build** (table below). Do not read all of them upfront.
4. **Repo rules apply on top:** pull request size, file and function length limits, CLAUDE.md and `docs/` come from `engineering-standards`.

| Read | When you build or review |
|-|-|
| `references/architecture.md` | Framework roles, node types, layering, project structure |
| `references/langgraph.md` | State, graph topology, routing, human-in-the-loop, persistence, fault tolerance, streaming |
| `references/pydantic-ai.md` | Single-agent nodes, capabilities, output validation, tool approval, MCP |
| `references/crewai.md` | Crews as nodes, agent templates, scoped memory, guardrails |
| `references/contracts-and-validation.md` | Inter-agent contracts, moderator shield, validator/fixer loop |
| `references/observability.md` | Langfuse, OTel, session grouping, metrics |
| `references/security.md` | Untrusted input, tool permissions, serialization, secrets |
| `references/testing-and-evals.md` | Unit, integration and snapshot tests, eval datasets, LLM-as-judge |
| `references/operations.md` | Dependencies, lockfile, deployment, workers, cost, durable execution, protocols |
| `references/anti-patterns.md` | Review checklist of known mistakes |
| `references/sources.md` | Official docs, changelogs and migration guides per framework |

## 1. Architecture: one owner per concern

| Concern | Owner | Never |
|-|-|-|
| Control flow, loops, branching, cross-step state, persistence, human approval | **LangGraph** | Duplicate it with Pydantic AI graphs, CrewAI Flows or a second durable engine inside the same run |
| One agent with tools and structured output | **Pydantic AI** (adapter node) | Let it own state across graph steps |
| Several role-based agents collaborating | **CrewAI** (adapter node, fresh crew per call) | Reuse crews or agents across calls |
| Data shape at every boundary | **Pydantic** models | Pass free text between pipeline stages |
| Traces, sessions, cost, evals | **Langfuse** over OTel | Build custom logging for LLM calls |

Choose the node type by the task:

| Task | Node |
|-|-|
| Deterministic routing, validation, preprocessing | Plain LangGraph function |
| One agent, structured output | Pydantic AI adapter node |
| Several agents debating or dividing work | CrewAI adapter node |
| Human decision | Node with one `interrupt()` |
| Iterative refinement with its own state | Subgraph |

Every framework agent sits behind an **adapter node**: read and inflate from state, run, validate, deflate back into state. The graph never sees framework objects. Organise code by **pipeline phase**, not by framework (`references/architecture.md`).

**Why:** clear ownership is what keeps the system debuggable. Two engines that both persist or both route will disagree after a crash.

## 2. State: small, typed, JSON-only

- **The envelope is a `TypedDict(total=False)`.** Nodes return only the keys they change. Use a reducer (`Annotated[..., operator.add]` or a custom merge) for every key that parallel branches write.
- **Payloads are Pydantic models**, stored as `model_dump(mode="json")` and inflated with `model_validate()` at node entry. Never put live objects, exceptions, clients or framework results into state. Store the error as a short `last_error` message, plus an `ErrorSnapshot` (JSON) where the traceback matters.
- **Task pipelines carry domain fields only.** Use LangChain `messages` only for conversational graphs.
- **Keep state small.** Store IDs and references rather than large blobs, and summarise long histories.
- **Treat persisted state as a schema with users.** Add fields before you remove them, and keep old fields readable while old threads may still resume.

**Why:** checkpointers serialize state at every step. Anything that is not plain JSON either breaks on resume or opens a deserialization hole.

## 3. Models: tiers, never literals

- **One model factory** maps tiers (`brain`, `workhorse`, `bolt`) to model IDs. IDs come from configuration or the environment, never from code literals scattered across agents.
- **Plain agents get their model at run time** (`agent.run(..., model=get_model("workhorse"))`). Agents that need a model at construction (durable execution, YAML agent specs) get it from the same factory.
- **Pick the tier by task.** Cheap tiers handle experts, memory analysis and routing; strong tiers handle moderation, writing and judging. An eval judge never runs on the same tier as the generator it grades.
- **Model IDs are provider-specific.** The native Anthropic API, gateways such as OpenRouter, and cloud providers spell them differently. Check the provider's current model list, and check retirement dates before pinning.

**Why:** models are retired on fixed dates and prices move. One factory turns a model change into a configuration change.

## 4. Validation: soft plus hard, always bounded

- **The prompt states the constraints (soft); code enforces them (hard).** Never rely on prompts alone. LLMs break stated constraints often enough to matter.
- **Structured output guarantees syntax, not meaning.** Validate every LLM result client-side against its Pydantic model.
- **Validation has three layers:**
  1. Self-correction inside the agent: a Pydantic AI output validator, or a CrewAI guardrail.
  2. A separate **validator node** in the graph.
  3. A **fixer node** that turns precise errors ("the first dependency of the third task: …") into a correction prompt.
- **Every loop has a budget:** `max_retries` in state, a retry limit inside the agent, and a usage or token limit per run. On exhaustion the graph routes to a defined end, never to an infinite loop.
- **Inter-agent output is a contract** (Pydantic model), not free text. Downstream agents see only the fields meant for them (moderator shield, context fencing).

Details in `references/contracts-and-validation.md`.

## 5. Human-in-the-loop: one interrupt per node

- **A node pauses with one `interrupt()` call.** Validate the answer (typed response schema). On invalid input, store the problem in state and route back to the same node via an edge. Never loop around `interrupt()` inside the node.
- **Never wrap `interrupt()` in a bare try/except,** and keep the order of interrupts deterministic.
- **Tool approval** (an agent wants to run a consequential tool) follows the same path: the agent defers the call, and the graph turns it into an `interrupt()`.
- **Validate manual state edits** (time travel, `update_state`) against the schema before applying them.

**Why:** a resumed node re-runs from its start. Loops around `interrupt()` replay all earlier passes on every resume.

## 6. Persistence and fault tolerance

- **Choose the checkpointer by environment:** in-memory for tests and local development, Postgres (async, pooled) for production, none for stateless workers that never resume. Every invocation with a checkpointer carries a `thread_id`.
- **Harden the serializer:** no pickle, an explicit allowlist (strict mode) for deserialized types, and encryption at rest for checkpoints that contain personal or confidential data.
- **Set fault-tolerance policies once for all nodes** (where the framework version supports it, see `references/langgraph.md`): retry policy, timeout, error handler. Override them per node where needed. Choose the durability mode deliberately (sync where a crash must lose nothing).
- **Shut down gracefully:** on SIGTERM, drain running graphs so they can resume, rather than killing them.
- **LangGraph's checkpointer is the default durable engine.** Add Temporal or DBOS only for runs that span days or must survive infrastructure loss, and then never run two durable engines on the same agent.

Details in `references/langgraph.md` and `references/operations.md`.

## 7. Security: least agency

- **Treat all retrieved documents, tool results, web pages and user input as untrusted data.** It never becomes instructions.
- **Give each agent only the tools it needs.** Use allowlists for commands, paths and hosts. Consequential or destructive tools go through human approval. Never execute LLM-generated code outside a sandbox.
- **Enforce access in code and memory scopes,** not in prompts. "Ignore X" in a prompt is a wish, not a control.
- **Secrets come from the environment or a secrets manager.** They never appear in code, state, prompts or traces. Switch off content capture in traces where prompts contain personal data.
- **Set minimum versions above the latest security fixes** of the frameworks (`references/operations.md`) and re-check them on every dependency update.
- **Trust MCP servers like dependencies:** pinned, reviewed, filtered to the tools you need.

Details in `references/security.md`.

## 8. Observability: one trace per run

- **Initialize tracing once at startup** (idempotent). Pydantic AI and CrewAI emit OTel spans; LangGraph is traced through a callback handler created **per invocation**, never shared across threads.
- **One business ID ties a run together:** use it as the Langfuse session ID, the LangGraph `thread_id` and the agent conversation ID. Set trace attributes in a propagation context around the whole run, and create callback handlers inside that context.
- **Short-lived processes flush** before they exit or acknowledge a task.
- **Check what is exported.** Tracing SDKs filter spans by default. Non-LLM spans such as HTTP, database or worker spans can disappear and leave orphaned children.
- **Do not hard-code dashboards on `gen_ai.*` attribute names.** The OTel GenAI conventions are still in development.
- **Watch validation health per node:** a failure rate above 0.3 suggests model drift, and an average retry depth above 1.5 suggests rising cost.

Details in `references/observability.md`.

## 9. Dependencies: locked, floored, isolated when needed

- **Use `uv` with a committed lockfile.** Install from the lockfile only (`uv sync --frozen`). Never rely on install order.
- **Put floor pins on the packages that matter,** so a resolver that would silently fall back to an old version fails loudly instead.
- **Add a CI check** that compares resolved versions with the expected floors.
- **Pick provider extras that avoid conflicts.** CrewAI and Pydantic AI can pull different major versions of shared SDKs. If they cannot share one environment at current versions, run the crews in their own process or service and call it from a LangGraph node.
- **Re-check the conflict picture on every upgrade.** It moves with each release; the current state is in `references/operations.md`.

## 10. Testing and evals

- **Unit tests never call a real model.** Block real requests globally, and use the framework's test models (Pydantic AI `TestModel`/`FunctionModel`) or mocks for crews. Test structure and routing, not wording.
- **Test adapters, not frameworks:** state in, state out, JSON-serializable, errors land in `last_error`.
- **Integration tests run the compiled graph** with an in-memory checkpointer and resume interrupts.
- **Evals are part of the definition of done for agent behaviour.** Keep an eval dataset per agent or pipeline, run it in CI on prompt or model changes, calibrate LLM judges against human labels, and evaluate trajectories (tool calls, routing), not only final answers.

Details in `references/testing-and-evals.md`.

## 11. Context and protocols

- **Context is a budget.** Use deterministic nudges for what must always be in the prompt (latest ruling, constraints) and scoped memory for deep recall. Use prompt caching for stable prefixes. Use a different tier, not a bigger prompt, when a model struggles.
- **MCP** connects tools, **A2A** connects agents across services or vendors, and **AG-UI** connects agents to front-ends. Use each only where it fits; untrusted message history from a browser is sanitized first.
- **The Claude Agent SDK** is an option for a Claude-native single agent inside a node, behind the same adapter rules.

Details in `references/operations.md`.

## Project structure

```
project/
├── pyproject.toml / uv.lock
├── pipeline/
│   ├── orchestrator.py      # entry point: run_pipeline(), tracing context
│   ├── graph.py             # StateGraph builder, edges, node defaults
│   ├── state.py             # TypedDict envelope
│   ├── schemas.py           # Pydantic payloads and contracts
│   ├── models.py            # model factory (tiers → IDs from config)
│   ├── tracing.py           # idempotent Langfuse/OTel init
│   ├── research.py          # Pydantic AI agents + adapter nodes
│   ├── handlers/            # domain I/O adapters
│   └── refinement/          # multi-agent subpackage: schemas, prompts, crews, memory, subgraph
├── evals/                   # datasets and evaluators
└── tests/ (unit/, integration/, conftest.py)
```

## Review checklist (top mistakes)

| Mistake | Fix |
|-|-|
| Model ID literal in an agent | Model factory with tiers |
| Exceptions, clients or Pydantic objects in state | `last_error` message + `ErrorSnapshot`, IDs, `model_dump(mode="json")` |
| Validation inside the generator | Separate validator node, then fixer |
| Trusting structured output | Client-side Pydantic validation |
| Loop around `interrupt()` | One interrupt per node, loop via edges |
| Crew or agent reused across rounds | Frozen template, fresh instances per call |
| Blocking sync call inside an async node | Native async API or `asyncio.to_thread` |
| Shared callback handler across requests | One handler per invocation |
| Unlocked installs, no floor pins | `uv.lock` + floors + CI check |
| Prompt-only access control | Memory scopes, tool allowlists, approval gates |
| No retry or usage budget | `max_retries`, agent retry limits, usage limits |
| Unit test that calls a real model | Block real requests; test models |

Full list in `references/anti-patterns.md`.

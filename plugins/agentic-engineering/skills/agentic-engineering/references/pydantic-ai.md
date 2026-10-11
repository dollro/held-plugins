# Pydantic AI: single-agent nodes and the model factory

Patterns for the Pydantic AI 2.x line. Version 2 moved many constructor arguments into **capabilities** and changed model prefixes and several result APIs. Check the migration guide and changelog (`sources.md`) before using any API named here.

## 1. Division of labour with LangGraph

| Pydantic AI owns | LangGraph owns |
|-|-|
| The single-agent loop: instructions, tools, output type, output validation, retries inside one run | Cross-step state, checkpointing, routing, interrupts, fan-out |

Inside a LangGraph node, do not use Pydantic AI's own graph, durable execution or step persistence: they duplicate the checkpointer. Use them only for standalone agent services.

## 2. Model factory

```python
# pipeline/models.py: one factory, one config, one adapter per framework
import os

# Tier → (provider, model id). Defaults are examples; production values come from the
# environment. ID spelling differs by provider (dashes on the native API, dots on OpenRouter):
# check the provider's current model list and retirement dates.
TIERS: dict[str, tuple[str, str]] = {
    "brain":     (os.getenv("MODEL_PROVIDER", "anthropic"), os.getenv("MODEL_BRAIN", "claude-opus-5-5")),
    "workhorse": (os.getenv("MODEL_PROVIDER", "anthropic"), os.getenv("MODEL_WORKHORSE", "claude-sonnet-5-5")),
    "bolt":      (os.getenv("MODEL_PROVIDER", "anthropic"), os.getenv("MODEL_BOLT", "claude-haiku-5-5")),
}

def get_model(tier: str = "workhorse") -> str:
    """Pydantic AI adapter: "<provider>:<model>". A bare model name is an error."""
    provider, model_id = TIERS.get(tier, TIERS["workhorse"])
    return f"{provider}:{model_id}"
```

- Provider credentials come from the environment (`ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, …), never from code.
- When a project routes through a gateway (OpenRouter, a corporate proxy), only the strings and the provider change. Agents stay untouched.
- **Choose the provider extra with the CrewAI conflict in mind:** some extras pull a major SDK version that CrewAI caps (`operations.md`).
- **Durable agents** need their models at construction: register them via the factory, not as literals.
- `get_crewai_llm(tier)` in `crewai.md` reads the same `TIERS`, so a model change is one configuration change for both frameworks.

## 3. The adapter node

```python
# pipeline/research.py
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError
from langgraph.runtime import Runtime
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

@dataclass
class ResearchDeps:                       # dependency injection: config, clients, context
    search_client: "SearchClient"
    max_results: int = 10

class ResearchOutput(BaseModel):
    findings: list[str] = Field(min_length=1)
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_followup: str | None = None

research_agent = Agent(
    name="research",                      # stable span and activity names
    deps_type=ResearchDeps,
    output_type=ResearchOutput,
    instructions=(
        "You are a senior research analyst. Analyse the query, search, synthesise findings "
        "with source attribution and give a confidence score. Be explicit about uncertainty."
    ),
    retries={"output": 2},                # in-agent self-correction budget (check current form)
)

@research_agent.tool
async def web_search(ctx: RunContext[ResearchDeps], query: str) -> str:
    """Search the web for information."""
    return await ctx.deps.search_client.search(query, limit=ctx.deps.max_results)

@research_agent.output_validator
async def check_sources(ctx: RunContext[ResearchDeps], out: ResearchOutput) -> ResearchOutput:
    if not out.sources:
        raise ModelRetry("Cite at least one source for your findings.")
    return out

async def research_node(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict:
    deps = ResearchDeps(search_client=runtime.context.search_client)   # injected, not hardcoded
    prompt = state["query"]
    if state.get("correction"):                       # set by the fixer after a failed validation
        prompt += f"\n\n{state['correction']}"
    try:
        result = await research_agent.run(
            prompt,
            model=get_model("workhorse"),
            deps=deps,
            usage_limits=UsageLimits(request_limit=10),   # cost guard per node
            conversation_id=runtime.context.run_id,       # traces line up with the graph run (check name)
        )
        artifact = ResearchArtifact(                      # inside the try: a bad URL is a ValidationError
            artifact_id=uuid4(), url=result.output.sources[0],
            summary="\n".join(result.output.findings),
            relevance_score=result.output.confidence, source_type="web",
            timestamp=datetime.now(timezone.utc))
    except (UnexpectedModelBehavior, UsageLimitExceeded, ValidationError) as e:
        return {"last_error": f"{type(e).__name__}: {e}", "current_step": "research",
                "retry_count": state.get("retry_count", 0) + 1}
    return {"artifacts": [artifact.model_dump(mode="json")],
            "current_step": "research", "last_error": None, "correction": None}
```

### Analyzer: inflate earlier artifacts

```python
class AnalysisOutput(BaseModel):
    key_insights: list[str] = Field(min_length=1)
    risk_factors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    executive_summary: str = Field(min_length=100)

analyzer_agent = Agent(name="analyzer", output_type=AnalysisOutput,
                       instructions="Synthesise insights, identify risks, recommend actions.")

async def analyzer_node(state: PipelineState) -> dict:
    artifacts = inflate_list(state.get("artifacts", []), ResearchArtifact)
    if not artifacts:
        return {"last_error": "No artifacts to analyze", "current_step": "analyzer",
                "retry_count": state.get("retry_count", 0) + 1}   # every failure spends budget
    digest = "\n\n".join(f"Source: {a.url}\nRelevance: {a.relevance_score}\n{a.summary}"
                         for a in artifacts)
    try:
        result = await analyzer_agent.run(f"Analyze:\n\n{digest}", model=get_model("brain"),
                                          usage_limits=UsageLimits(request_limit=5))
    except (UnexpectedModelBehavior, UsageLimitExceeded) as e:
        return {"last_error": str(e), "current_step": "analyzer",
                "retry_count": state.get("retry_count", 0) + 1}
    out = result.output
    task = TaskResult(task_id=uuid4(), status="completed", output=out.executive_summary,
                      confidence=out.confidence,
                      metadata={"insights": len(out.key_insights), "risks": len(out.risk_factors),
                                "recommendations": out.recommendations})
    return {"task_results": [task.model_dump(mode="json")],
            "current_step": "analyzer", "last_error": None, "correction": None}
```

### Rules for adapter nodes

1. **Inflate** payloads at entry. They may be dicts after deserialization.
2. **Deflate** with `model_dump(mode="json")` at exit.
3. **Catch the framework's specific exceptions** and store them as a `last_error` string. Let unexpected exceptions reach the graph's retry and error-handler policies instead of swallowing them.
4. **Increment `retry_count`** on every failure (otherwise the retry loop never ends), and set `current_step` so the validator and fixer know the source.
5. **Name every agent, inject its dependencies, and give it a usage limit.** Read `correction` into the prompt when set, and clear it on success.
6. **Pass the run's business ID** as the agent's conversation ID or metadata, so traces line up with the graph thread.

## 4. Version 2 idioms

Behaviour that used to be configured with constructor arguments is now added as capabilities (`capabilities=[...]`). Typical mapping (check the capabilities overview for current names):

| Concern | v2 form |
|-|-|
| Trimming or summarising message history | History-processing capability |
| Tracing per agent | Instrumentation capability (with a content-capture switch for privacy); globally `Agent.instrument_all()` |
| Filtering or preparing tools per step | Prepare-tools capability (return an empty list, never `None`) |
| Thinking or reasoning effort | Thinking capability or model settings |
| Hooks around runs and tool calls | Hooks capability (can raise `ModelRetry`) |
| Provider-native tools (web search, fetch) | Native tools |
| Durable execution | Durability capability for the chosen engine (standalone services only) |

Other changes to keep in mind:

- **Model prefixes:** `openai:` now means the Responses API (`openai-chat:` is Chat Completions), and bare names fail.
- **`end_strategy`:** the default is now graceful, so tool calls returned alongside a final output still run.
- **Usage:** usage and timestamps are properties on the result, and token fields are named input and output tokens.
- **Retries:** use one `retries` setting with separate budgets for tools and output.
- **Message history from untrusted sources** (a browser, a stored conversation) is sanitized before it is passed to `run()`.

## 5. Tool approval mapped to LangGraph interrupts

When a tool is consequential, the agent should not decide alone:

1. Mark the tool as requiring approval. The run then ends with **deferred tool requests** instead of executing it.
2. The adapter node stores those requests in state and routes to an interrupt node.
3. The human answers. The next run of the agent receives the approval or denial results and continues.

Check the deferred-tools docs for the current types and parameters. The rule stays: **the agent defers, the graph interrupts, a person decides.**

## 6. MCP and other integrations

- **MCP servers** are added as toolsets (`toolsets=[...]`). Manage their lifecycle with `async with agent:`. Filter each server down to the tools the agent needs.
- **A2A:** expose an agent to other services through the A2A adapter (now maintained outside Pydantic AI).
- **AG-UI / UI adapters:** stream an agent to a front-end. Sanitize incoming history.
- **Agent specs (YAML/JSON):** prompts and configuration as data, reviewable in pull requests. Models still resolve through the factory.
- **Pydantic AI Harness:** ready-made memory, guardrails, subagents and compaction. Evaluate it before building these by hand for a standalone agent.

## 7. Testing hooks

- `Agent.override(model=..., deps=..., toolsets=..., instructions=...)` swaps parts of an agent for tests.
- `TestModel` and `FunctionModel` replace the LLM. `capture_run_messages()` shows the exchange.
- `models.ALLOW_MODEL_REQUESTS = False` blocks real calls.

Details in `testing-and-evals.md`.

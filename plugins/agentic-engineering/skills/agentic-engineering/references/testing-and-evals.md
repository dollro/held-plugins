# Testing and evals

Testing has two layers:

- **Tests** check that the harness is correct: structure, routing, serialization, error paths. They are deterministic, fast and free.
- **Evals** check that agent behaviour is good enough: quality, faithfulness, tool use. They are statistical, run on real models, and are tracked over time.

Both are part of the definition of done for agent work.

## 1. Block real model calls in tests

```python
# tests/conftest.py
import pytest
from pydantic_ai import models

models.ALLOW_MODEL_REQUESTS = False      # any real Pydantic AI model call raises

@pytest.fixture
def anyio_backend():
    return "asyncio"

class FakeSearch:
    async def search(self, query: str, limit: int = 10) -> str:
        return f"results for {query}"

@pytest.fixture
def ctx_runtime():
    """Stand-in for LangGraph's Runtime: nodes only read .context."""
    from types import SimpleNamespace
    return SimpleNamespace(context=PipelineContext(tenant="test", run_id="t",
                                                   search_client=FakeSearch()))

@pytest.fixture
def test_models():
    """Every Pydantic AI agent in the graph answers from TestModel."""
    from contextlib import ExitStack
    from pydantic_ai.models.test import TestModel
    with ExitStack() as stack:
        for agent in (router_agent, research_agent, analyzer_agent):
            stack.enter_context(agent.override(model=TestModel()))
        yield
```

Use `pytest.mark.anyio` for async tests, as the Pydantic AI docs do. CrewAI and other SDK calls are mocked at the adapter boundary.

## 2. Unit tests for Pydantic AI nodes

Test **structure, not wording**. LLM content is non-deterministic.

```python
import pytest
from pydantic_ai.models.test import TestModel

@pytest.mark.anyio
async def test_research_node_produces_valid_artifact(ctx_runtime):
    mock = ResearchOutput(findings=["F1", "F2"], sources=["https://example.com/a"],
                          confidence=0.85)
    with research_agent.override(model=TestModel(custom_output_args=mock.model_dump())):
        result = await research_node({"query": "AI safety"}, ctx_runtime)

    assert result["last_error"] is None
    artifact = ResearchArtifact.model_validate(result["artifacts"][0])
    assert artifact.relevance_score == 0.85
```

### Error path: force invalid output

`TestModel(custom_output_text=...)` is the wrong tool for an agent with a structured output type: it fails for an internal reason, and a broad `except` hides that. Use a `FunctionModel` that keeps returning invalid output, so the agent really exhausts its output retries.

```python
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

def always_invalid(messages, info: AgentInfo) -> ModelResponse:
    tool = info.output_tools[0]
    return ModelResponse(parts=[ToolCallPart(tool.name, {"findings": []})])   # violates min_length

@pytest.mark.anyio
async def test_research_node_reports_exhausted_retries(ctx_runtime):
    with research_agent.override(model=FunctionModel(always_invalid)):
        result = await research_node({"query": "x", "retry_count": 0}, ctx_runtime)
    assert "UnexpectedModelBehavior" in result["last_error"]
    assert result["retry_count"] == 1
```

### Inspect the exchange

```python
from pydantic_ai import capture_run_messages
from pydantic_ai.messages import ToolCallPart

@pytest.mark.anyio
async def test_research_agent_calls_search(ctx_runtime):
    with capture_run_messages() as messages:
        with research_agent.override(model=TestModel()):
            await research_node({"query": "AI safety"}, ctx_runtime)
    assert any(isinstance(p, ToolCallPart) and p.tool_name == "web_search"
               for m in messages for p in getattr(m, "parts", []))
```

`capture_run_messages` also records interrupted partial messages, so assert on content rather than exact counts. Instructions travel separately from system-prompt parts, so check where your version puts them before you assert on them.

## 3. Unit tests for CrewAI nodes

Test the adapter (state in, state out, deflation, fallback), not the crew.

```python
import json
from unittest.mock import AsyncMock, patch

@pytest.mark.anyio
async def test_refinement_node_deflates_and_falls_back():
    state = {"current_draft": "d", "latest_rationale": "", "iteration_count": 0,
             "max_iterations": 2, "document_id": "doc-1"}
    with patch("crewai.Crew.akickoff", new_callable=AsyncMock), \
         patch("pipeline.refinement.loop.create_pipeline_memory"), \
         patch("pipeline.refinement.loop.create_scoped_agents", return_value={}), \
         patch("pipeline.refinement.loop.Crew"), \
         patch("pipeline.refinement.loop.build_tasks", return_value=fake_tasks(pydantic=None)):
        result = await refinement_round_node(state)
    json.dumps(result)                                   # everything JSON-serializable
    assert result["latest_rationale"] == "raw moderator text"   # raw fallback used
    assert result["iteration_count"] == 1
```

## 4. Integration tests for the graph

Run the compiled graph with an in-memory checkpointer and test models.

```python
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

@pytest.fixture
def app():
    return compile_graph(checkpointer=InMemorySaver())

@pytest.mark.anyio
async def test_workflow_ends_or_reports(app, test_models, ctx_runtime):
    config = {"configurable": {"thread_id": "t-1"}}
    out = await app.ainvoke({"query": "renewables", "max_retries": 2}, config,
                            context=ctx_runtime.context, version="v2")
    assert out.value.get("next_action") == "end" or out.value.get("last_error")

@pytest.mark.anyio
async def test_workflow_persists_state(app, test_models, ctx_runtime):
    config = {"configurable": {"thread_id": "t-persist"}}
    await app.ainvoke({"query": "x", "max_retries": 1}, config, context=ctx_runtime.context)
    snapshot = await app.aget_state(config)
    assert snapshot.values.get("current_step")

@pytest.mark.anyio
async def test_human_review_resumes(app, test_models, ctx_runtime):
    config = {"configurable": {"thread_id": "t-2"}}
    out = await app.ainvoke({"query": "x", "requires_human_approval": True}, config,
                            context=ctx_runtime.context, version="v2")
    assert out.interrupts                      # the router honours requires_human_approval
    out = await app.ainvoke(Command(resume={"action": "approve"}), config,
                            context=ctx_runtime.context, version="v2")
    assert out.value["next_action"] == "end"   # approve routes straight to END

@pytest.mark.anyio
async def test_invalid_review_asks_again(app, test_models, ctx_runtime):
    config = {"configurable": {"thread_id": "t-3"}}
    await app.ainvoke({"query": "x", "requires_human_approval": True}, config,
                      context=ctx_runtime.context, version="v2")
    out = await app.ainvoke(Command(resume={"action": "revise"}), config,   # missing content
                            context=ctx_runtime.context, version="v2")
    assert out.interrupts and out.value["review_error"]
```

More LangGraph techniques:

- **Test a single node** through `compiled.nodes["name"]`.
- **Start mid-graph** by seeding state with `update_state(config, values, as_node=...)`.
- **Stop at a node** with compile-time `interrupt_after` to test partial execution.

## 5. Snapshot tests

```python
from dirty_equals import IsInt, IsStr

def test_initial_state_shape():
    assert create_initial_state(max_retries=3) == {
        "query": IsStr(), "artifacts": [], "task_results": [], "crew_outputs": [],
        "current_step": "entry", "retry_count": 0, "max_retries": 3,
        "last_error": None, "review_error": None, "next_action": None,
        "requires_human_approval": False, "cumulative_tokens": IsInt(ge=0),
    }
```

`dirty-equals` and `inline-snapshot` keep snapshot tests of complex state readable.

## 6. Evals

### What to evaluate

| Level | Question | Example evaluators |
|-|-|-|
| Output | Is the final result correct, complete, faithful to sources? | Type checks, contract validation, reference comparison, LLM judge with rubric |
| Trajectory | Did the agent take sensible steps? | Expected tool calls, routing path, number of retries, no forbidden tools |
| Operational | Is it affordable and fast enough? | Tokens, cost, latency, validation failure rate |

### Offline: a dataset per agent or pipeline

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, LLMJudge

dataset = Dataset(
    name="research-agent",
    cases=[
        Case(name="eu-ai-act", inputs="Obligations of deployers under the EU AI Act",
             metadata={"difficulty": "medium"}),
        # 20–100 cases from real traffic, edge cases and past failures
    ],
    evaluators=[
        IsInstance(type_name="ResearchOutput"),
        LLMJudge(rubric="Findings are supported by the cited sources; no invented facts.",
                 model=get_model("brain")),      # judge tier differs from generator tier
    ],
)

async def run_research(query: str) -> ResearchOutput:
    return (await research_agent.run(query, model=get_model("workhorse"))).output

async def main():
    report = await dataset.evaluate(run_research)
    report.print()
```

The Langfuse equivalent: datasets plus experiments (`run_experiment`) with observation-level LLM-as-judge evaluators. Results sit next to the production traces.

### Rules

- **Run evals in CI** when prompts, models, tools or contracts change. Fail the build on a regression beyond an agreed threshold. Langfuse provides a GitHub Action for experiments.
- **Calibrate LLM judges** against a set of human-labelled cases before trusting them, and re-check after changing the judge model.
- **Evaluate trajectories,** not only answers. A right answer reached by calling a forbidden tool is a failure.
- **Grow the dataset from production:** every incident and every bad trace becomes a case.
- **Online evals** score a sample of production traces continuously (Langfuse evaluators, pydantic-evals online evaluation via OTel). Alert on drift.
- **Track eval scores per prompt version and model tier,** so every change is a comparison, not a guess.

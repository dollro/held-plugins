# CrewAI: crews as nodes, templates, scoped memory

Patterns for the CrewAI 1.x line. CrewAI releases roughly weekly and its docs sometimes lag the code. Check the changelog and, where the docs and the behaviour disagree, the installed source (`sources.md`).

## 1. LLM factory for CrewAI

CrewAI has native clients for the major providers and treats LiteLLM as an optional extra. A wrong provider prefix silently falls back to LiteLLM and fails if that extra is missing.

```python
# pipeline/models.py: the CrewAI adapter of the one model factory (tiers in pydantic-ai.md)
from crewai import LLM

def get_crewai_llm(tier: str = "workhorse") -> LLM:
    provider, model_id = TIERS.get(tier, TIERS["workhorse"])
    # CrewAI spells it "<provider>/<model>". Native Anthropic needs the anthropic extra and
    # an explicit max_tokens. Gateway: provider "openrouter" (reads OPENROUTER_API_KEY), or an
    # OpenAI-compatible base_url with the native OpenAI client forced.
    return LLM(model=f"{provider}/{model_id}", max_tokens=4096, temperature=0.3)
```

- Use cheaper tiers for experts and memory analysis, and stronger tiers for moderator and writer.
- Never let CrewAI fall back to its default model. Pass an LLM to every agent and to the memory.

## 2. Agent templates: frozen, cloned per call

CrewAI `Agent` and `Crew` objects mutate during `kickoff()`. Define immutable templates and build fresh instances on every call.

```python
# pipeline/refinement/crews.py
from dataclasses import dataclass
from crewai import Agent

@dataclass(frozen=True)
class AgentTemplate:
    """Immutable definition: no LLM coupling, no per-run state. Safe at module level."""
    role: str
    goal: str
    backstory: str
    tier: str = "workhorse"
    max_iter: int = 8

expert_technical = AgentTemplate(
    role="Technical Reviewer",
    goal="Check technical soundness, depth and correctness",
    backstory="You review technical documents for precision and missing evidence...",
    tier="bolt")
expert_growth = AgentTemplate(role="Growth Reviewer", goal="...", backstory="...", tier="bolt")
expert_legal = AgentTemplate(role="Compliance Reviewer", goal="...", backstory="...", tier="bolt")
moderator = AgentTemplate(
    role="Editorial Chief",
    goal="Resolve conflicting expert feedback into one coherent revision plan",
    backstory="You synthesise competing perspectives and make editorial decisions...",
    tier="brain")
writer = AgentTemplate(
    role="Professional Writer",
    goal="Execute revision instructions precisely while preserving voice",
    backstory="You apply targeted revisions...",
    tier="brain")

EXPERTS = {"technical": expert_technical, "growth": expert_growth, "legal": expert_legal}

def clone_agent(t: AgentTemplate, memory=None) -> Agent:
    return Agent(role=t.role, goal=t.goal, backstory=t.backstory,
                 llm=get_crewai_llm(t.tier), memory=memory, max_iter=t.max_iter,
                 allow_delegation=False, verbose=False)
```

Tuning:

- **`backstory`** shapes personality. Make it specific and opinionated to get diverse feedback.
- **`allow_delegation=False`** prevents sub-agent spawning and saves calls.
- **`max_iter`:** the default is high (around 20–25). Use 5–10 to control cost.
- **Per-agent `llm`:** cheap tiers for experts, strong tiers for moderator and writer.
- A **single agent** without a crew can run via `Agent.kickoff(..., response_format=Model)`. In this stack, Pydantic AI stays the default for single agents.

## 3. Tasks

```python
from crewai import Task

def build_tasks(agents: dict, draft: str, prior_context: str) -> dict[str, Task]:
    experts = {
        name: Task(
            description=(f"Review this draft for {name} quality:\n---\n{draft}\n---\n"
                         f"Give exactly 3 strengths and 3 weaknesses.\n\n{prior_context}"),
            expected_output="A structured list of 3 pros and 3 cons.",
            agent=agents[name])
        for name in EXPERTS
    }
    moderation = Task(
        description=MODERATOR_PROMPT,
        expected_output="JSON with conflict_resolution_rationale and consolidated_revision_plan",
        agent=agents["moderator"],
        context=list(experts.values()),            # waits for all experts
        output_pydantic=ModerationResult,           # contract (contracts-and-validation.md)
        guardrail=require_actionable_plan,          # hard check with its own retry budget
    )
    revision = Task(description=WRITER_PROMPT, expected_output="The complete revised document",
                    agent=agents["writer"], context=[moderation])
    return {**experts, "moderator": moderation, "writer": revision}
```

```python
def require_actionable_plan(output) -> tuple[bool, object]:
    """Guardrail: returns (True, output) or (False, feedback the agent retries with)."""
    plan = output.pydantic.consolidated_revision_plan if output.pydantic else ""
    if len([line for line in plan.splitlines() if line.strip()]) < 2:
        return False, "The revision plan must be a numbered list of at least two concrete steps."
    return True, output
```

- **Use `context=`** to express dependencies (a classic chain: research → strategy → writing → editing, each task listing its predecessors). A task sees the outputs of the tasks in its context.
- **Bound the output** ("exactly 3 strengths and 3 weaknesses") so the moderator gets clear signals.
- **Guardrails** (a function or an LLM-judged description) are CrewAI's hard-validation layer. They retry the task up to their own limit.
- **Parallel tasks inside a crew (`async_execution=True`):**
  - Current versions propagate context variables (and with them the tracing context) into worker threads. Very old versions did not, and their spans showed up as orphan traces.
  - Never give two async tasks the same agent; this is a known crash.
  - When you need parallelism across independent work, prefer LangGraph fan-out.

## 4. Crew as a LangGraph node: fresh per call, native async

```python
from crewai import Crew, Process

async def refinement_round_node(state: DocumentRefinementState) -> dict:
    """One expert → moderator → writer cycle. Fresh memory, agents, tasks and crew per call."""
    round_no = state["iteration_count"] + 1
    memory = create_pipeline_memory(state["document_id"])
    agents = create_scoped_agents(memory)
    tasks = build_tasks(agents, state["current_draft"],
                        nudge(round_no, state["latest_rationale"]))
    crew = Crew(agents=list(agents.values()), tasks=list(tasks.values()),
                process=Process.sequential, memory=memory)
    try:
        await crew.akickoff()            # native async; never call blocking kickoff() in an async node
    except Exception as e:               # crew errors vary by provider: map them to state
        return {"last_error": f"Crew failed: {e}",
                "retry_count": state.get("retry_count", 0) + 1}   # should_continue stops at the budget
    finally:
        memory.drain_writes()            # make background memory saves durable (check current name)

    mod = tasks["moderator"].output.pydantic       # may be None if parsing failed
    rationale = (mod.conflict_resolution_rationale if mod
                 else tasks["moderator"].output.raw or "Moderator output unavailable.")
    return {"current_draft": tasks["writer"].output.raw, "latest_rationale": rationale,
            "iteration_count": round_no, "last_error": None}
```

### Crew as one node among others (`PipelineState`)

```python
import time

async def crew_node(state: PipelineState) -> dict:
    """Content crew inside the main graph: fresh crew, contract out, errors into state."""
    agents = {name: clone_agent(t) for name, t in CONTENT_TEAM.items()}   # templates like EXPERTS
    tasks = build_content_tasks(agents, topic=state["query"], correction=state.get("correction"))
    crew = Crew(agents=list(agents.values()), tasks=list(tasks.values()),
                process=Process.sequential)
    started = time.monotonic()
    try:
        result = await crew.akickoff()
    except Exception as e:
        return {"last_error": f"Crew failed: {e}",
                "error_detail": ErrorSnapshot.from_exception(e).model_dump(mode="json"),
                "current_step": "content_crew", "retry_count": state.get("retry_count", 0) + 1}
    output = CrewOutput(crew_name="content", tasks_completed=len(tasks),
                        final_output=result.raw,
                        execution_time_seconds=time.monotonic() - started)
    return {"crew_outputs": [output.model_dump(mode="json")], "current_step": "content_crew",
            "last_error": None, "correction": None}
```

- **Never keep a crew or agents in a module-level singleton.** Build them inside the node.
- **On older versions without native async, use `await asyncio.to_thread(crew.kickoff)`.** This also keeps the event loop free.
- **Set a rate limit (`max_rpm`) on the crew** when several crews share an API key.
- **Leave CrewAI's own checkpointing off inside nodes.** LangGraph persists. Use CrewAI checkpoints only for long crews that must resume on their own.
- **Set `CREWAI_DISABLE_TELEMETRY=true`** where outbound telemetry is not allowed. It uses its own tracer and does not mix with your OTel setup.

### Concurrency

| Scenario | Safe? | Notes |
|-|-|-|
| Parallel workers, different documents | ✅ | Memory scoped by document ID |
| Parallel workers, same document | ⚠️ | Distributed lock (for example Redis `SET NX`) |
| Reusing a crew or agents across rounds | ❌ | Always fresh instances |
| Module-level frozen templates | ✅ | Read-only configuration |

## 5. Scoped memory

CrewAI's unified memory gives:

- **A hierarchical scope tree:** memories organised like a filesystem.
- **Composite scoring:** semantic match, recency and importance.
- **LLM consolidation** of near-duplicates.
- **Non-blocking saves** with async variants, and a read barrier: recall waits for pending saves.
- **Graceful degradation** when the memory LLM fails.

### Memory factory per pipeline run

```python
# pipeline/refinement/memory.py
from crewai import Memory

def create_pipeline_memory(document_id: str) -> Memory:
    """One memory per run, rooted at the document; storage shared across rounds."""
    return Memory(
        root_scope=f"/pipeline/{document_id}",   # native isolation between runs
        # composite scoring: library defaults are recency 0.3 / semantic 0.5 / importance 0.2
        # and a 30-day half-life (integer days, minimum 1). For pipelines that run in minutes,
        # recency is nearly uniform: lower its weight instead of shrinking the half-life.
        recency_weight=0.1, semantic_weight=0.6, importance_weight=0.3,
        consolidation_threshold=0.85,            # 1.0 disables consolidation (saves LLM calls)
        llm=get_crewai_llm("bolt"),              # memory analysis: cheap tier, never the default
        embedder={"provider": "openai",          # pin the embedder: the vector dimension follows it
                  "config": {"model_name": "text-embedding-3-small"}},
        # local alternative, no API cost:
        # embedder={"provider": "huggingface",
        #           "config": {"model_name": "sentence-transformers/all-MiniLM-L6-v2"}},
    )
```

Parameter names and defaults change between releases, so check the memory docs before you tune anything.

| Setting | Library default | Fast pipeline (minutes) | Long-running (weeks) |
|-|-|-|-|
| Recency half-life (days, integer ≥ 1) | 30 | 1 (recency barely matters) | 7–30 |
| Recency / semantic / importance weights | 0.3 / 0.5 / 0.2 | 0.1 / 0.6 / 0.3 | 0.2 / 0.5 / 0.3 |
| Consolidation threshold | 0.85 | 0.85 | 0.90 |

Further recall knobs: the query length above which recall runs an LLM query analysis, high and low confidence thresholds, an exploration budget, and how many existing records consolidation compares against. Short queries skip the analysis, which makes recall fast.

Consolidation in action, and why the moderator can escalate:

```
Round 1: expert technical stores "The draft has no encryption for health data."
Round 2: expert technical stores "Encryption is still missing for health data."
→ similarity above threshold → LLM merge → one record:
  "Encryption for health data flagged in rounds 1 and 2, still unresolved."
``` Changing the embedder makes existing stores unreadable: reset the memory, or keep the embedder pinned.

### Scoped agents: access enforced in the memory layer

| Agent | Can read | Can write |
|-|-|-|
| Expert (each) | Its own scope `/expert/<name>` | Its own scope |
| Moderator | All expert scopes + `/moderator` (panoramic view) | `/moderator` |
| Writer | `/moderator` only (context-fenced) | Nothing (read-only) |

```python
def create_scoped_agents(memory: Memory) -> dict[str, Agent]:
    # Paths below assume they resolve under root_scope. If your version treats them as
    # absolute, prefix f"/pipeline/{document_id}" and check isolation with a test.
    agents = {name: clone_agent(t, memory.scope(f"/expert/{name}"))
              for name, t in EXPERTS.items()}
    agents["moderator"] = clone_agent(moderator, memory.slice(
        scopes=[f"/expert/{n}" for n in EXPERTS] + ["/moderator"], read_only=False))
    agents["writer"] = clone_agent(writer, memory.slice(scopes=["/moderator"], read_only=True))
    return agents
```

- `memory.scope(path)` covers one subtree, read and write.
- `memory.slice(scopes, read_only)` covers several subtrees and is read-only by default.

**Why:** without scoping, the writer recalls raw expert critique and starts hedging. With scoping, it sees only the moderator's plan.

### Dual context: nudge plus memory

| | Nudge (prompt injection) | Memory (scoped recall) |
|-|-|-|
| Type | Push, deterministic | Pull, semantic |
| Purpose | Break argument loops | Deep historical recall |
| Content | Latest ruling only | All stored facts, ranked |
| Reliability | 100%, always in the prompt | Probabilistic |
| Cost | None | Embeddings + LLM calls |
| Scales to | One round of history | Unlimited history |

The nudge carries the weight of loop prevention; memory adds consolidation, access control and depth.

```python
def nudge(round_no: int, latest_rationale: str) -> str:
    if round_no == 1:
        return ""
    return (f"**PRIOR RULING (round {round_no - 1}):** The Editorial Chief decided: "
            f"'{latest_rationale}'\nDo NOT re-argue settled points. Focus on issues in the "
            "CURRENT draft. Your memory may hold more context from earlier rounds.")
```

### Memory lifecycle per round

1. Create the memory (same storage, new instance).
2. Create the scoped agents.
3. Build the tasks with the nudge.
4. `akickoff()`. Before each task: recall from the agent's scope into the prompt. After each task: extract atomic facts and remember them in the agent's scope (non-blocking).
5. Drain pending writes.
6. Return the state update.

The next round's memory instance sees all persisted, consolidated records.

### Storage

- **Local workers:** the default local store under `CREWAI_STORAGE_DIR`.
- **Several workers sharing memory:** a server-backed or pluggable storage backend. Shared file systems (NFS/EFS) for embedded vector stores are fragile.
- **Optimisation levers:**
  - Shallow recall skips the LLM query analysis.
  - A local embedder costs nothing per call.
  - Disable consolidation when duplicates don't matter.

## 6. MCP tools in CrewAI

Agents take MCP servers directly (stdio or HTTP), with a tool filter. Filter every server down to the tools the role needs. Treat MCP servers as dependencies: pinned, reviewed, and never handed credentials beyond what they need.

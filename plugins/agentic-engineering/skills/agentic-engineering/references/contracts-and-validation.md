# Contracts and validation

## 1. Pydantic contracts between agents

When one agent's output feeds another, define a strict Pydantic schema. It is the "semantic firewall": parseable output instead of free text leaking between stages.

```python
from pydantic import BaseModel, Field

class ModerationResult(BaseModel):
    """Output the moderator MUST produce. Two fields, deliberately separated:
    the writer receives the revision plan but NOT the rationale (context fencing)."""
    conflict_resolution_rationale: str = Field(
        description="How contradictions between experts were resolved, citing their points.")
    consolidated_revision_plan: str = Field(
        description="Final, harmonised, step-by-step instructions for the writer. "
                    "Self-contained: the writer sees ONLY this.")
```

How each framework enforces the contract:

- **Pydantic AI:** `output_type=ModerationResult`, plus output validators for semantic rules.
- **CrewAI:** `output_pydantic=ModerationResult` on the task (mapped to native structured output where the provider supports it), plus a guardrail for semantic rules. If parsing fails after the converter's retries, `.pydantic` is `None`: always keep a raw fallback.

**Structured-output modes guarantee JSON syntax, not semantic validity.** Client-side validation is mandatory.

## 2. Moderator shield

```
Expert A --+
Expert B --+--> Moderator --> Writer
Expert C --+
```

Experts never talk to downstream consumers directly. Without the shield, the writer gets contradictory instructions and hedges; the moderator makes the editorial calls and produces one coherent plan.

### Context fencing on two layers

- **Layer 1, the prompt:** "Follow ONLY `consolidated_revision_plan`; ignore `conflict_resolution_rationale`." Better still, pass only that field.
- **Layer 2, memory:** the writer's memory slice reads only `/moderator`, read-only (`crewai.md`).

**Why both:** LLMs sometimes ignore "ignore X". The memory layer is a control; the prompt is a hint.

### Moderator: panoramic view and escalation

```python
MODERATOR_PROMPT = (
    "You have received feedback from three domain experts.\n"
    "1. Identify contradictions between their recommendations.\n"
    "2. Decide how to resolve each one and explain why.\n"
    "3. Produce one unified, step-by-step revision plan for the writer.\n\n"
    "Your memory holds findings and rulings from earlier rounds. Issues flagged repeatedly "
    "must be escalated in priority.\n"
    "Output MUST match the ModerationResult schema.")

WRITER_PROMPT = (
    "Rewrite the draft following the Editorial Chief's consolidated_revision_plan step by step. "
    "Produce the complete updated document, not a summary of changes.")
```

The moderator can spot a pattern such as "expert A flagged encryption three times" through consolidated memory and raise its priority.

### Contract fallback

```python
mod: ModerationResult | None = tasks["moderator"].output.pydantic
if mod is None:
    logger.warning("Moderator contract parse failed, falling back to raw output")
    rationale = tasks["moderator"].output.raw or "Moderator output unavailable."
else:
    rationale = mod.conflict_resolution_rationale
```

## 3. Validation in three layers

| Layer | Where | Mechanism | Budget |
|-|-|-|-|
| 1. Self-correction | Inside the agent | Pydantic AI output validator raising `ModelRetry`; CrewAI guardrail | Agent output retries, guardrail retries |
| 2. Validator node | Graph | Pydantic validation of the deflated payload, plus business rules | — |
| 3. Fixer node | Graph | Precise errors turned into a correction prompt, routed back to the source | `max_retries` in state |

```
Generator -> Validator -> Router -+- success -> next phase
                                  +- retry   -> Fixer -> Generator
                                  +- fatal   -> END (or human review)
```

Rules:

- **Never validate inside the generator.** Separate nodes keep concerns apart and make the trace readable.
- **Every loop is bounded.** On exhaustion, route to a defined end or to a human.
- **Soft plus hard:** the prompt states the constraint, and code enforces it.

### Validator node

```python
from pydantic import ValidationError

CONTRACTS = {"research": ("artifacts", ResearchArtifact),
             "analyzer": ("task_results", TaskResult),
             "content_crew": ("crew_outputs", CrewOutput)}

def validator_node(state: PipelineState) -> dict:
    if state.get("last_error"):                  # the adapter already failed: keep its error
        return {}                                # (it already incremented retry_count)
    step = state.get("current_step", "unknown")
    if step not in CONTRACTS:
        return {"last_error": None}
    key, model = CONTRACTS[step]
    errors = []
    for raw in state.get(key, [])[-1:]:          # validate the latest output only
        try:
            model.model_validate(raw)
        except ValidationError as e:
            errors.append(f"{model.__name__} invalid:\n{format_validation_error(e)}")
    if errors:
        return {"last_error": "\n".join(errors), "retry_count": state.get("retry_count", 0) + 1}
    return {"last_error": None}   # add "retry_count": 0 here for a per-step instead of per-run budget
```

Adapters set `last_error` on failure and clear it (`"last_error": None`) on success, so a stale error never survives a successful retry.

### Error messages an LLM can act on

Granular feedback cuts retry cycles. "The first dependency of the third task: field required" beats "validation failed".

```python
def format_validation_error(e: ValidationError) -> str:
    return "\n".join(f"  • {humanise(err['loc'])}: {err['msg']}" for err in e.errors())

def humanise(loc: tuple) -> str:
    """('tasks', 2, 'dependencies', 0) → 'the 1st dependency of the 3rd task'"""
    parts = []
    for i, part in enumerate(loc):
        if isinstance(part, int) and i > 0 and isinstance(loc[i - 1], str):
            parts.append(f"the {ordinal(part + 1)} {loc[i - 1].rstrip('s')}")
        elif isinstance(part, str) and i == len(loc) - 1:
            parts.append(f"field '{part}'")
    return " of ".join(reversed(parts)) or ".".join(map(str, loc))

def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
```

### Fixer node

```python
def fixer_node(state: PipelineState) -> dict:
    """Store a correction instruction for the source node; the source reads it on its next run."""
    error = state.get("last_error") or "Unknown validation error"
    return {
        "correction": (
            "Your previous output failed validation:\n"
            f"{error}\n\n"
            "Regenerate it, correcting ONLY these issues. Required fields must be present, "
            "numeric bounds respected, enumerations matched exactly, URLs valid."),
        "current_step": state.get("current_step"),   # keeps routing back to the source
    }
```

The source node appends `state["correction"]` to its prompt when it is set, and clears it after a successful run. Task pipelines don't need LangChain messages for this.

## 4. Validation health

Track per node:

- `validation_failure_rate > 0.3` is a warning sign of model drift or a broken prompt.
- `avg_retry_depth > 1.5` means cost efficiency is degrading.

A node that tops these lists needs a better contract, a better prompt or a stronger tier, not more retries. Metrics code is in `observability.md`.

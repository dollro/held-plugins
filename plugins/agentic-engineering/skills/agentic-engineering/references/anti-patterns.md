# Anti-patterns and review checklist

Use this file as the review checklist for agentic code. Each row names the mistake, why it hurts, and the fix.

## Architecture and state

| Anti-pattern | Problem | Fix |
|---|---|---|
| Two engines owning the same concern (Pydantic AI graph or CrewAI Flow inside a LangGraph node, two durable engines) | They disagree after a crash or retry | One owner per concern (`architecture.md`) |
| Framework objects in state (agents, results, clients) | Not serializable, breaks checkpoints | Adapter nodes deflate to JSON |
| `TypedDict` for complex values | No runtime validation | Pydantic payloads in a TypedDict envelope |
| Storing `Exception` in state | Not JSON, pushes toward unsafe serialization | `ErrorSnapshot` |
| Forgetting `mode="json"` in `model_dump()` | UUID and datetime break checkpoints | Always `model_dump(mode="json")` |
| Modifying state in place | Graph integrity issues | Return a new partial dict |
| `TypedDict` without `total=False` | Verbose initialisation, nodes return everything | `total=False`, return only changed keys |
| Missing reducer on keys written by parallel branches | Last writer wins, data lost | `Annotated[..., operator.add]` or a merge function |
| LangChain messages in task pipelines | Overhead, unclear state | Domain fields; messages only for conversational graphs |
| Huge state (full histories, documents) | Slow checkpoints, cost, context bloat | IDs and references, summaries |
| Renaming or removing state keys in one deploy | Old threads fail on resume | Add first, remove after all old threads have finished |
| Iteration logic in the parent graph | Cluttered topology | Subgraph with its own state |
| Clients or secrets in state | Leak into checkpoints and traces | Runtime context or dependencies |

## Models and agents

| Anti-pattern | Problem | Fix |
|---|---|---|
| Model ID literal in `Agent(...)` or `LLM(...)` | Can't swap per environment, test or retirement date | Model factory with tiers from configuration |
| Prefix-less or wrong-prefix model strings | Errors, or the wrong API (e.g. Responses vs Chat Completions) | Provider-qualified strings from the factory |
| CrewAI model with a wrong provider prefix | Silent LiteLLM fallback, then an ImportError | Native provider prefix or explicit gateway configuration |
| Letting CrewAI memory or agents use the default model | Unplanned provider, cost and data flow | Pass an LLM from the factory everywhere |
| Unnamed agents | Unstable span names, hard debugging | `name=` on every agent |
| Hardcoded dependencies inside nodes (`api_key="sk-..."`) | Secrets in code, untestable | Inject through deps or runtime context |
| Broad `except Exception` around agent runs | Hides bugs and passes tests for the wrong reason | Catch the framework's specific exceptions; let the rest reach node policies |
| Reusing `Crew` or `Agent` across rounds | They mutate during kickoff | Frozen templates, fresh instances per call |
| Crew in a module-level singleton | Shared mutable state across requests | Build inside the node |
| Blocking `kickoff()` inside an async node | Blocks the event loop | Native async kickoff or `asyncio.to_thread` |
| Two async CrewAI tasks on the same agent | Known crash | One agent per async task, or LangGraph fan-out |
| `max_iter` left at the default | Expensive reasoning loops | 5–10 |

## Validation and control flow

| Anti-pattern | Problem | Fix |
|---|---|---|
| Validating inside the generator node | Mixed concerns, unreadable traces | Validator node, then fixer node |
| Trusting structured output | Guarantees syntax, not meaning | Client-side Pydantic validation and business rules |
| Prompt-only constraints | LLMs break them regularly | Soft (prompt) plus hard (code) |
| No retry limit | Infinite loops on persistent errors | `max_retries` in state, agent retry budgets, usage limits |
| Vague validation errors | More retries | Granular, located error messages |
| Contract parse failure not handled | `None` crashes downstream | Raw fallback and a logged warning |
| Writer reading expert critiques | Hedging, apologetic output | Moderator shield, prompt and memory fencing |
| Nudge-only context | Loses earlier rulings | Nudge plus memory |
| Memory-only context | Probabilistic, misses critical rulings | Nudge plus memory |

## Human-in-the-loop and persistence

| Anti-pattern | Problem | Fix |
|---|---|---|
| `while True` around `interrupt()` | Every resume replays all earlier passes | One interrupt per node, loop via an edge |
| try/except around `interrupt()` | Swallows the pause mechanism | Validate the answer, not the call |
| Non-deterministic interrupt order | Resume values land in the wrong place | Fixed order |
| Side effects before an interrupt | Run again on resume | Idempotent effects or a separate node |
| Applying manual state edits unvalidated | Corrupted schema | Validate against contracts first |
| In-memory checkpointer in workers | Per process, useless across workers | Async Postgres, Redis or none |
| Returning `from_conn_string(...)` as the saver | It is a context manager, not a saver | `with ... as saver:` or construct with a pool |
| Pickle or permissive deserialization | RCE risk | Pickle off, strict msgpack allowlist, encryption at rest |
| Deprecated checkpoint flags or config schema | Removed in a coming major | Durability mode, context schema |
| Dict access on typed invoke output | Deprecated | Attribute access on the v2 output |
| `create_react_agent` | Deprecated | `create_agent` with middleware, or a Pydantic AI node |

## Observability

| Anti-pattern | Problem | Fix |
|---|---|---|
| Shared callback handler across requests or threads | Cross-contaminated traces | One handler per invocation |
| Handler created outside `propagate_attributes` | Spans without a session | Create it inside the context |
| No flush in short-lived processes | Lost spans | `flush()` before exit or acknowledgement |
| v3 Langfuse span APIs (`update_trace`, `start_as_current_span`) | AttributeError on v4 | `start_as_current_observation`, `propagate_attributes`, `update()` |
| Ignoring the default export filter | Worker and HTTP spans dropped, orphaned children | Configure the export filter |
| Dashboards on `gen_ai.*` names | Conventions still change | Langfuse fields, or a version-pinned mapping |
| Prompts with personal data captured in traces | Data protection risk | Content capture off, masking |
| Langfuse with only `langchain-core` installed | The callback imports `langchain` | Install full `langchain` |

## Dependencies and operations

| Anti-pattern | Problem | Fix |
|---|---|---|
| Relying on install order | Non-reproducible, silently wrong versions | `uv.lock` and `uv sync --frozen` |
| No floor pins | The resolver silently downgrades a framework | Floors plus a CI drift check |
| Full `pydantic-ai` next to Langfuse | Pulls logfire, downgrades Langfuse | `pydantic-ai-slim[<provider>]` |
| Provider extras that clash with CrewAI's caps | Silent fallback to old Pydantic AI | Conflict-free extras, or isolate the crews in their own process |
| Floors below security fixes | Known vulnerabilities | Floors from the advisories (`operations.md`) |
| `eventlet`/`gevent` worker pools with CrewAI | Conflicts with CrewAI threads | `prefork` |
| `module.__version__` in audit scripts | Missing on namespace packages | `importlib.metadata.version()` |
| Upgrading all frameworks at once | Unattributable breakage | One framework per change, eval suite before merge |

## Testing

| Anti-pattern | Problem | Fix |
|---|---|---|
| Unit tests that call real models | Cost, flakiness, leaks | Block real requests; test models |
| Asserting on LLM wording | Flaky | Assert structure, contracts, routing |
| `TestModel(custom_output_text=...)` for structured agents | Fails for the wrong reason | `FunctionModel` returning invalid output |
| Testing the crew instead of the adapter | Slow, non-deterministic | Mock kickoff, test state in and out |
| No evals | Quality regressions go unnoticed | Eval dataset per agent, run in CI |
| Uncalibrated LLM judge, same tier as the generator | Biased scores | Calibrate against human labels, use a different tier |

## Performance guidelines

1. **Minimise state size.** Summarise older context and keep references instead of objects.
2. **Use LangGraph fan-out** for independent work: deterministic, checkpointed, traced. Keep parallelism inside a crew for tightly coupled expert panels.
3. **Track tokens with reducers.** Each node returns only its own delta (`cumulative_tokens`, `phase_token_usage`).
4. **Cache:**
   - LangGraph node cache policies for deterministic, expensive nodes.
   - Provider prompt caching for stable prefixes.
   - Opt-in tool-result caching in CrewAI.
   - Semantic-similarity caching for repeated, near-identical LLM requests (with a TTL and a quality check).
5. **Batch** validation checks in one Pydantic call, and batch LLM requests where the API supports it.
6. **Tier models:** cheap tiers for experts, routing and memory analysis; the strongest tier for moderator, writer and judges.
7. **Tune memory:** low recency weight for short pipelines, consolidation off when not needed, a local embedder for zero API cost.
8. **Cap reasoning:** `max_iter` 5–10 on agents, and usage limits per node.

# Security

The organising idea is **least agency**: an agent gets only the knowledge, tools and permissions its task needs, and anything consequential passes through a person. Use the OWASP Top 10 for Agentic Applications as a review checklist (goal hijacking, tool misuse, privilege abuse, memory poisoning, cascading failures and the rest). Read the official OWASP text for the current categories.

## 1. Untrusted content never becomes instructions

Everything an agent did not get from its own code is data: user input, uploaded documents, web pages, retrieved chunks, tool results, MCP responses and other agents' output.

- **Structural defences first:**
  - Separate system instructions from data (clear delimiters, data passed as fields rather than spliced into instructions).
  - Use typed tool arguments.
  - Validate output contracts.
  - Keep tool allowlists.
  - Put human approval in front of consequential actions.
- **Filters are a weak extra layer.** A regex blocklist catches only the clumsiest injections:

```python
import re
from pydantic import BaseModel, Field, field_validator

class SanitizedUserInput(BaseModel):
    """Length limits plus a weak pattern filter. Defence in depth, never the only defence."""
    content: str = Field(min_length=1, max_length=10_000)

    @field_validator("content")
    @classmethod
    def sanitize(cls, v: str) -> str:
        v = v.strip()
        for pattern in (r"ignore\s+previous\s+instructions", r"disregard\s+all\s+prior",
                        r"system\s*:\s*"):
            v = re.sub(pattern, "[FILTERED]", v, flags=re.IGNORECASE)
        return v
```

- **Message history from browsers or storage is sanitized** before it is passed to an agent: framework sanitizers, role checks, and no forged tool results.

## 2. Tools: allowlists, sandboxes, approval

- **Scope tools per agent.** Pass a filtered toolset, never "all tools of this server".
- **Allowlists** for commands, paths, hosts and SQL operations:

```python
from typing import ClassVar
from pydantic import BaseModel, Field, field_validator

class CodeExecutionRequest(BaseModel):
    """Never execute LLM-generated commands blindly."""
    ALLOWED: ClassVar[set[str]] = {"ls", "cat", "echo", "grep", "find"}
    command: str
    arguments: list[str] = Field(default_factory=list)

    @field_validator("command")
    @classmethod
    def allowed(cls, v: str) -> str:
        if v not in cls.ALLOWED:
            raise ValueError(f"Command '{v}' not in allowlist")
        return v
```

- **Generated code runs only in a sandbox:** a container or a managed code-execution service, with no network or secrets by default. Never in the worker process.
- **Consequential or destructive tools require approval:** the agent defers the call, the graph interrupts, a person decides (`pydantic-ai.md`, `langgraph.md`). Respect destructive-action hints from MCP servers.
- **Rate-limit and budget-limit tools** (usage limits, `max_iter`, `max_rpm`) to contain runaway loops and cascading failures.

## 3. Serialization and persistence

- **No pickle, ever.** Keep pickle fallback off (the default in current LangGraph) and never put objects in state that would need it. Exceptions become `ErrorSnapshot` (`langgraph.md`).
- **Strict deserialization:** turn on LangGraph's strict msgpack mode or pass an explicit module allowlist. The default only warns about unknown types.
- **Encrypt checkpoints at rest** when they contain personal, confidential or NDA data. Keep the key in a secrets manager.
- **Keep namespaces and stores isolated per tenant.** Long-term memory stores and checkpoint namespaces include the tenant or document ID in the key.
- **Patch levels:** several 2026 advisories hit LangGraph checkpoint deserialization, caches and store namespace matching. Keep the floors in `operations.md` current and watch the frameworks' security advisories.

## 4. Memory

- **Enforce access in the memory layer, not in prompts.** The writer never gets a scope containing raw expert critique.
- **Mark slices read-only** where an agent must not write.
- **Scope paths include the run or document ID**, so memory never leaks between runs or tenants.
- **Treat memory as an injection vector.** Content written by one agent and recalled by another is untrusted data too (memory poisoning). Keep scopes narrow and consolidation conservative.

## 5. Secrets and personal data

- **Secrets come from the environment or a secrets manager.** They never appear in code, agent definitions, state, prompts, memory or trace metadata.
- **Inject configuration and clients through dependencies** (Pydantic AI `deps`, LangGraph runtime context), not through module globals with keys.
- **Keep credentials separate per purpose:** agent LLM, memory LLM, embeddings, tools. Then a leaked key has a small blast radius.
- **Personal data in prompts:** minimise it, pseudonymise where possible, switch off content capture in traces and apply masking. Follow the organisation's AI and data protection policy for which use cases may process which data.

## 6. MCP, A2A and other protocols

- **MCP servers are dependencies:** pinned version, reviewed source or a trusted vendor, filtered tools and least-privilege credentials. Remote servers use the spec's OAuth flow. Local servers bind to localhost, with DNS-rebinding protection.
- **A2A peers are other organisations' agents.** Authenticate them, validate everything against contracts, and never forward secrets or raw internal state.
- **AG-UI and browser front-ends:** the browser is untrusted. Sanitize history and validate every tool result the UI sends back.

## 7. Review checklist

- [ ] Every tool is allowlisted for the agent that uses it. Destructive tools go through approval.
- [ ] No LLM-generated code or command runs outside a sandbox or allowlist.
- [ ] Untrusted content is passed as data, and outputs are validated against contracts.
- [ ] State is JSON-only, the serializer is strict, and checkpoints with sensitive data are encrypted.
- [ ] Memory scopes are enforced, and writer-type agents are read-only.
- [ ] No secrets in code, state, prompts or traces. Content capture is off where personal data flows.
- [ ] Dependency floors are at or above the latest security fixes.
- [ ] Loops, tools and runs have budgets.

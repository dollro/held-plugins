# Sources: where the current truth lives

The snippets in this skill show patterns. Exact signatures, defaults and package extras live in the official sources below. Before writing or upgrading framework code, read the changelog entries since the version in the lockfile, and the migration guide when a major version changed.

**Ways to read them:**

- a docs MCP server (for example context7), when available;
- fetching the page directly (many docs sites also serve raw `.md`);
- the installed package source in `.venv`;
- PyPI metadata (`https://pypi.org/pypi/<package>/json`) for versions and dependency pins.

## LangGraph and LangChain

| What | Where |
|-|-|
| Docs (Python) | https://docs.langchain.com/oss/python/langgraph/overview |
| Changelog (LangChain + LangGraph) | https://docs.langchain.com/oss/python/releases/changelog |
| Interrupts (human-in-the-loop) | https://docs.langchain.com/oss/python/langgraph/interrupts |
| Persistence, checkpointers, durability | https://docs.langchain.com/oss/python/langgraph/checkpointers |
| Fault tolerance (retry, timeout, error handler, drain) | https://docs.langchain.com/oss/python/langgraph/fault-tolerance |
| Subgraphs | https://docs.langchain.com/oss/python/langgraph/use-subgraphs |
| Testing | https://docs.langchain.com/oss/python/langgraph/test |
| Backward compatibility of state | https://docs.langchain.com/oss/python/langgraph/backward-compatibility |
| `create_agent` middleware | https://docs.langchain.com/oss/python/langchain/middleware/built-in |
| Releases | https://github.com/langchain-ai/langgraph/releases |
| Security advisories | https://github.com/langchain-ai/langgraph/security/advisories |
| LangSmith Deployment | https://docs.langchain.com/langsmith/deployment |

## Pydantic AI and Pydantic

| What | Where |
|-|-|
| Docs | https://pydantic.dev/docs/ai/ |
| Changelog | https://pydantic.dev/docs/ai/project/changelog/ |
| Migration guide (major versions) | https://pydantic.dev/docs/ai/overview/migration/ |
| Capabilities | https://pydantic.dev/docs/ai/capabilities/overview/ |
| Output and output validators | https://pydantic.dev/docs/ai/core-concepts/output/ |
| Deferred tools (approval) | https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/ |
| Testing | https://pydantic.dev/docs/ai/guides/testing/ |
| Evals (pydantic-evals) | https://pydantic.dev/docs/ai/evals/evals/ |
| Durable execution | https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/ |
| Releases | https://github.com/pydantic/pydantic-ai/releases |
| Pydantic (validation library) | https://pydantic.dev/docs/validation/latest/ and https://github.com/pydantic/pydantic/releases |

## CrewAI

| What | Where |
|-|-|
| Docs | https://docs.crewai.com/ |
| Changelog | https://docs.crewai.com/en/changelog |
| Crews, agents, tasks, guardrails | https://docs.crewai.com/en/concepts/crews, https://docs.crewai.com/en/concepts/agents, https://docs.crewai.com/en/concepts/tasks |
| Memory | https://docs.crewai.com/en/concepts/memory |
| LLM configuration | https://docs.crewai.com/en/concepts/llms |
| MCP | https://docs.crewai.com/en/mcp/overview |
| Flows | https://docs.crewai.com/en/concepts/flows |
| Releases and source (the docs sometimes lag) | https://github.com/crewAIInc/crewAI/releases |

## Observability

| What | Where |
|-|-|
| Langfuse Python SDK | https://langfuse.com/docs/observability/sdk/python/overview |
| Langfuse SDK upgrade guide (v3 → v4) | https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4 |
| Langfuse + LangChain/LangGraph | https://langfuse.com/integrations/frameworks/langchain |
| Langfuse + CrewAI | https://langfuse.com/integrations/frameworks/crewai |
| Langfuse evaluation | https://langfuse.com/docs/evaluation/overview |
| Langfuse self-hosting versions | https://langfuse.com/self-hosting/upgrade/versioning |
| OpenInference instrumentations | https://github.com/Arize-ai/openinference |
| OTel GenAI semantic conventions | https://github.com/open-telemetry/semantic-conventions-genai |

## Models

| What | Where |
|-|-|
| Claude models overview | https://platform.claude.com/docs/en/about-claude/models/overview |
| Claude model deprecations (retirement dates) | https://platform.claude.com/docs/en/about-claude/model-deprecations |
| Claude pricing | https://platform.claude.com/docs/en/about-claude/pricing |
| OpenRouter model list (gateway IDs) | https://openrouter.ai/api/v1/models |

## Protocols, SDKs, durable execution

| What | Where |
|-|-|
| MCP specification and changelog | https://modelcontextprotocol.io/specification |
| A2A protocol | https://a2a-protocol.org |
| AG-UI | https://docs.ag-ui.com |
| Claude Agent SDK | https://code.claude.com/docs/en/agent-sdk/overview |
| Temporal + LangGraph | https://docs.temporal.io/develop/python/integrations/langgraph |
| DBOS | https://docs.dbos.dev |

## Security

| What | Where |
|-|-|
| OWASP GenAI Security Project (Agentic Top 10, LLM Top 10) | https://genai.owasp.org |

## Tooling

| What | Where |
|-|-|
| uv (locking, sync, tree) | https://docs.astral.sh/uv/ |

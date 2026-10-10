# Sources

Official pages behind `agent-sandbox.md`, checked October 2026 (sbx 0.47, MCP spec 2026-07-28). Re-check them when a tool's major or minor version moves; `sbx kit` and `sbx env` are experimental.

## Docker Sandboxes (`sbx`)

- Releases and known issues: https://github.com/docker/sbx-releases/releases, issue #48 (`mkfs.ext4`, fixed in 0.47)
- Architecture (microVM, virtiofs workspace): https://docs.docker.com/ai/sandboxes/architecture/
- Development workflow (Docker inside, ports, host services): https://docs.docker.com/ai/sandboxes/workflows/development/
- Git and clone mode: https://docs.docker.com/ai/sandboxes/workflows/git/
- Kits, version compatibility: https://docs.docker.com/ai/sandboxes/customize/ and https://docs.docker.com/ai/sandboxes/customize/kits-v2/
- Network policy concepts: https://docs.docker.com/ai/sandboxes/governance/concepts/
- MCP gateway and secrets: https://docs.docker.com/ai/sandboxes/mcp-gateway/
- Environment files (`sbxenv.yaml`): https://docs.docker.com/ai/sandboxes/configuration/environment-files/

## Claude Code

- Native sandbox (bubblewrap/Seatbelt, network proxy, `excludedCommands`, Docker incompatibility): https://code.claude.com/docs/en/sandboxing
- Sandbox environments overview: https://code.claude.com/docs/en/sandbox-environments
- Reference dev container (firewall, `CLAUDE_CONFIG_DIR`): https://code.claude.com/docs/en/devcontainer
- MCP configuration and `${VAR}` expansion, `headersHelper`: https://code.claude.com/docs/en/mcp
- Settings `env`, environment variables: https://code.claude.com/docs/en/settings-reference and https://code.claude.com/docs/en/env-vars

## MCP

- Authorization (OAuth 2.1, client ID metadata documents): https://modelcontextprotocol.io/specification/latest/basic/authorization
- Playwright MCP options (`--output-dir`, `--isolated`): https://github.com/microsoft/playwright-mcp
- Serena configuration (`project_serena_folder_location`): https://oraios.github.io/serena/02-usage/050_configuration.html

## Containers and ownership

- Compose variable interpolation: https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/
- Compose file watch: https://docs.docker.com/compose/how-tos/file-watch/
- Bind mounts: https://docs.docker.com/engine/storage/bind-mounts/
- Docker Desktop for Linux file sharing: https://docs.docker.com/desktop/troubleshoot-and-support/faqs/linuxfaqs/
- uv in Docker (venv outside the mount): https://docs.astral.sh/uv/guides/integration/docker/
- pnpm in Docker: https://pnpm.io/docker
- Dev container `updateRemoteUserUID`: https://containers.dev/implementors/json_reference/
- Podman `--userns=keep-id`: https://docs.podman.io/en/latest/markdown/podman-run.1.html

## Other agent sandboxes

- OpenAI Codex sandboxing: https://developers.openai.com/codex/security
- Gemini CLI sandbox: https://geminicli.com/docs/cli/sandbox/
- Docker socket mounts as sandbox escape (July 2026): https://akitaonrails.com/en/2026/07/25/ai-jail-security-update-docker-opt-in/

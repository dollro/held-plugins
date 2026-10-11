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
- Credentials (service secrets, `github` service, `gh auth token`, SSH agent forwarding for git): https://docs.docker.com/ai/sandboxes/security/credentials/
- Contributed kits: https://github.com/docker/sbx-kits-contrib (`gitlab-ssh/README.md`, `github-ssh/README.md`, `gitlab/README.md`, `gitea/README.md`)
- GitLab git-over-HTTP auth (Basic with the token as password, or Kerberos): https://docs.gitlab.com/user/profile/personal_access_tokens/ and `app/controllers/repositories/git_http_client_controller.rb` in https://gitlab.com/gitlab-org/gitlab

### Git push from a sandbox: notes as of 2026-10-10 (sbx 0.47)

- Observed: a self-hosted GitLab `git@` remote failed inside with `Host key verification failed`; the sandbox has no SSH key by design. `gitlab-ssh` kit added with `sbx kit add <sandbox> "git+https://github.com/docker/sbx-kits-contrib.git#dir=gitlab-ssh" --kit-arg host=<host> --kit-arg "hostKey=…"` fixed it; `ssh -T` and `git push` worked with the existing remote and `.git/config`.
- Observed: `kit.allowedSources` defaults to `["docker.io/"]` (`sbx settings get --json kit.allowedSources`); the git kit needed `github.com/docker/` added. `sbx settings set <key> <value>` takes raw JSON for json settings; `["*"]` allows every source; env `DOCKER_SANDBOXES_KIT_ALLOWED_SOURCES` overrides.
- Observed: `ssh.agentForwardingEnabled` defaults to `true` (daemon restart after a change); `ssh.agentSocketPath` can fix the host socket.
- `sbx kit add --help`: recreates the container with the kit appended, keeps kit-owned volumes; sandboxes created before the recreate feature are refused. `--kit-arg name=value` applies to every kit declaring `name`, `kit.name=value` to one.
- `gitlab-ssh` spec: args `host` (default `gitlab.com`) and `hostKey` (`<alg> <base64>`, required for other hosts; no scanning by design, to avoid trust on first use); allows `host` in the network policy; appends `host <key>` to `/home/agent/.ssh/known_hosts` (port 22 only).
- `github-ssh` spec: no args; fetches keys from `api.github.com/meta` at install.
- `gitlab` kit README: git-over-HTTPS Basic auth cannot be injected for GitLab (one host for API and git, inject rules not told apart by scheme); use SSH. Its `glab` token covers the API only.
- `sbx secret set github` (examples: `--command 'gh auth token'`): Docker's docs list `github.com` as an injection domain but do not state git-over-HTTPS push; the `gitlab` kit README says GitHub works because git goes to `github.com` and the API to `api.github.com`. Not tested here.
- Kits are also published as `docker.io/sbx/<kit>-kit:latest` per the READMEs; not tested here.

### Claude Code harness in a sandbox: notes as of 2026-10-11 (sbx 0.47, Claude Code 2.1)

- Kits v2 (https://docs.docker.com/ai/sandboxes/customize/kits-v2/): `setup.install` runs at creation or `sbx kit add`, `sh -c`, default user `"0"`; static `files/home/` and `setup.files` exist, but `sbx kit add` rejects kits that declare static files, `setup.startup` or `setup.files`. Order: network and environment, static files, install, `setup.files`, startup.
- `sbx skills --help`: the shared store is linked read-only into every sandbox at start (`skills.defaultMode` `readonly`); `--skills off|readonly|readwrite` at create. `sbx skills import` copies from `~/.agents/skills`, `~/.claude/skills` and others, follows top-level symlinks, cannot select single skills.
- `sbx mcp add` registers a server for `sbx create/run --static-mcp`; `sbx mcp ls -q` lists names.
- `claude plugin marketplace add <owner/repo|url|path> --scope user`, `claude plugin install <plugin>@<marketplace> --scope user`; `-y` accepts a marketplace-declared install command and is required for those without a TTY.
- Observed: inside the `claude` agent image `CLAUDE_CONFIG_DIR` is unset (config in `/home/agent/.claude`), `python3` and `jq` are present, `settings.json` already holds keys (`permissions`, `themeId`, …) that a harness merge must keep. 23 plugins from three public GitHub marketplaces installed in about 95–150 s at creation with only the GitHub hosts allowed.
- Observed: a public marketplace whose repo has nested git submodules on another host failed: Claude Code clones recursively, the submodule host was denied by the policy, and the retry over SSH failed on host-key verification. Allowing the submodule host alone did not fix it in the test (large clone); leaving that marketplace off did.

## Claude Code

- Native sandbox (bubblewrap/Seatbelt, network proxy, `excludedCommands`, Docker incompatibility): https://code.claude.com/docs/en/sandboxing
- Sandbox environments overview: https://code.claude.com/docs/en/sandbox-environments
- Reference dev container (firewall, `CLAUDE_CONFIG_DIR`): https://code.claude.com/docs/en/devcontainer
- MCP configuration and `${VAR}` expansion, `headersHelper`: https://code.claude.com/docs/en/mcp
- Settings `env`, environment variables: https://code.claude.com/docs/en/settings-reference and https://code.claude.com/docs/en/env-vars

## Claude Code practices behind `claude-md.md` and `autonomous-runs.md` (read 2026-10-11)

- Best practices (verification, explore-plan-code, CLAUDE.md pruning test, hooks vs CLAUDE.md, writer/reviewer, fan-out, adversarial review): https://code.claude.com/docs/en/best-practices
- Skills (frontmatter, `disable-model-invocation`, description cap and listing budget): https://code.claude.com/docs/en/skills
- Hooks (Stop event, exit codes, `stop_hook_active`, block cap): https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/hooks-guide
- Memory (CLAUDE.md size, `@path` imports, `.claude/rules/`): https://code.claude.com/docs/en/memory
- `/goal`: https://code.claude.com/docs/en/goal
- Permission modes (auto, `dontAsk`, `bypassPermissions`): https://code.claude.com/docs/en/permission-modes
- Non-interactive mode (`-p`, `--bare`, `--permission-prompts`): https://code.claude.com/docs/en/headless
- CLI flags (`--max-turns`, `--max-budget-usd`, `-w`): https://code.claude.com/docs/en/cli-reference
- Checkpointing: https://code.claude.com/docs/en/checkpointing
- Sandboxing: https://code.claude.com/docs/en/sandboxing
- Docker Sandboxes, Claude Code agent (default `--dangerously-skip-permissions`, `--` argument rules): https://docs.docker.com/ai/sandboxes/agents/claude-code/

### Version notes as of 2026-10-11 (docs as read that day)

- Skill listing: each entry's `description` + `when_to_use` is capped at 1,536 characters; the whole listing has a budget of 1% of the context window (`skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`). On overflow, descriptions of the least-used skills are dropped first, names stay. `disable-model-invocation: true` removes the description from context entirely.
- Stop hook: exit 0 allows the stop, exit 2 blocks with stderr as reason, other codes are non-blocking errors; JSON `{"decision":"block","reason":…}`; 8 consecutive blocks cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`), reset when Claude calls a tool.
- `/goal`: condition up to 4,000 characters; evaluator is the small fast model (`ANTHROPIC_DEFAULT_HAIKU_MODEL` changes it everywhere); check-in interval 30 min (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`); restored on every resume route since v2.1.239; idle check-ins capped at three since v2.1.246.
- Auto mode is the built-in starting mode for interactive terminal and VS Code sessions since v2.1.283; `auto` and `bypassPermissions` set in project settings files don't take effect. `--permission-prompts none` needs v2.1.259.
- `--bare` will become the default for `-p` in a future release; it needs `ANTHROPIC_API_KEY` (no subscription login).
- Not verified here: that `$SANDBOX_NAME` is set inside every `sbx` sandbox, and the headless `sbx run --name <name> -- -p "/goal …"` form.

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

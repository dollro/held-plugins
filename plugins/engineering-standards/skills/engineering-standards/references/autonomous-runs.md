# Autonomous and long-running agent work

How to let a coding agent work without someone watching every step, and still trust the result. Based on Anthropic's Claude Code best practices and the linked docs (sources and version notes in `sources.md`, read 2026-10-11). Flags and limits move between releases: check `claude --help` and the docs before writing them into a repo.

## When to let it run

An agent can run unattended when all of these hold:

| Precondition | Why |
|-|-|
| **A check it can run itself** (tests, lint, type check, build exit code, a script that diffs output against a fixture, a screenshot compared with a design) | Without a pass/fail signal, "looks done" is the only stop signal, and the human becomes the verification loop |
| **A self-contained spec, written first** | The run cannot ask; the spec answers the questions before they come up |
| **Isolation** (sandbox or worktree, network allowlist, no production secrets) | Mistakes stay inside a boundary you can throw away |
| **A rollback point** (a branch, commits per step) | Undo is `git reset`, not archaeology |

Keep it interactive instead when the work is exploratory, the end state cannot be checked by a command, or it needs production access or decisions only a person can make.

## 0. The human decides where it runs

Before any unattended run (setting a `/goal`, switching to auto mode or skipped permissions, a headless `claude -p` loop, a fan-out), ask the human with AskUserQuestion where it runs. Never decide alone, also when a skill or plan suggests autonomous execution (agent-team, prd2issues hand-offs). Options, recommended first:

1. **`sbx` sandbox on a worktree branch** (recommended for unattended runs): full permissions, but contained; network allowlist; no production secrets.
2. **This host session, supervised:** auto mode or Manual, the human watching. No unattended `/goal` outside a sandbox unless explicitly chosen.
3. **Host, unattended, auto mode:** only if the human explicitly accepts the risks: real host files, the user's credentials, the host network.
4. **Not autonomously:** a plan, or supervised steps only.

Record the choice in the handover and in the goal text, as one line: `Autonomous run approved by <human> on <date>: sandbox <name>, branch <branch>`.

**Asked once, at launch,** in the interactive session that starts the run; never again inside it. Inside a run, skip the gate when any of these holds: the session is in an `sbx` sandbox (`$SANDBOX_NAME` set) launched for an autonomous task; it is non-interactive (`claude -p`); a `/goal` is active; or the handover or goal text carries the approval line.

**During the run, never ask or wait.** No AskUserQuestion, no "shall I…?": a question stalls the loop until the stall or check-in logic stops it. Make the reasonable choice within the spec's constraints, note it, and list open questions and decisions in the final report. If blocked on something only a human can decide, stop cleanly and report. Skills that normally interview or confirm (design-first, braindump2prd, prd2issues confirmation tables, `/sbx harness` selection) use their defaults and record assumptions instead of asking.

## 1. Write the spec, then start fresh

Interview or plan in one session (plan mode, `design-first`, `braindump2prd`), write the result to the issue or a spec file, then start the run in a **fresh session** with clean context. A useful spec:

- names the files and interfaces involved and the existing pattern to follow (`file:line`);
- says what is out of scope;
- ends with an **end-to-end check command** that proves the feature works;
- states constraints that must not change on the way (no edits to tests to make them pass, no new dependencies without a note).

## 2. Make "done" enforceable

Pick how hard the check gates the stop. Each step trades setup for attention:

| Gate | What it is | Use when |
|-|-|-|
| In the prompt | "Run `task check` and iterate until it passes; show the output" | Any task, today |
| `/goal <condition>` | A session-scoped completion condition, judged after every turn | One substantial task with a verifiable end state |
| Stop hook | A script in settings that blocks the turn from ending until it passes | Every session in the repo (or user scope) must pass the same check |
| Reviewer subagent | A fresh context checks the diff against the spec | Before counting the work as done |

### `/goal`

`/goal <condition>` sets one completion condition per session and immediately starts a turn with it as the directive. After each turn a small fast model judges the condition **met**, **not yet met** (Claude keeps going, the reason is its guidance) or **impossible** (goal cleared, failure recorded). The evaluator **reads only the transcript and runs no tools**, so the condition must be provable by Claude's own printed output: "`npm test` exits 0", "`git status` is clean".

```text
/goal all tests in test/auth pass (`task test -- test/auth` exits 0, output shown), lint is clean, no other test file is modified. Stop after 20 turns.
```

- **Condition** up to 4,000 characters: one measurable end state, the stated check, the constraints. Bound it with "or stop after N turns".
- **Permissions:** a goal doesn't change the permission mode. Unattended needs auto mode (or a sandbox with permissions skipped): auto mode removes per-tool prompts, `/goal` removes per-turn prompts.
- **Status and stop:** `/goal` alone shows condition, turns, spend and last reason; `/goal clear` stops it; `/clear` also removes it. It survives `claude --continue` / `--resume` (turn count and spend reset).
- **Stalls:** no tool use for several turns ends the loop with the goal still set. Auth failure, exhausted credit, unrecoverable context overflow or an unavailable model **clear** it; rate or usage limits **pause** it; transient errors retry.
- **Background work** (subagents, background shells) defers evaluation; check-ins come every 30 minutes by default, backing off (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`, `0` turns check-ins and retries off).
- **Headless:** `claude -p "/goal …" --output-format stream-json --verbose > goal.log` runs the loop to completion; plain text output looks stuck until the end.
- **Needs hooks:** `/goal` is a prompt-based Stop hook, so it needs workspace trust and is unavailable with `disableAllHooks` or `allowManagedHooksOnly`.

### Stop hook: a deterministic gate

`.claude/settings.json` in the repo (committed) or `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-before-stop.sh", "timeout": 600 } ] }
    ]
  }
}
```

`.claude/hooks/check-before-stop.sh`:

```bash
#!/usr/bin/env bash
# Blocks the end of a turn until the repo's check passes.
input=$(cat)
# Already continuing because of this hook: let Claude stop once it has tried, avoid loops.
[ "$(jq -r '.stop_hook_active' <<<"$input")" = "true" ] && exit 0
# Nothing changed: nothing to check.
git diff --quiet HEAD && git diff --cached --quiet && exit 0
if ! out=$(task check 2>&1); then
  printf 'task check failed. Fix the cause, do not weaken the check:\n%s\n' "$(tail -n 40 <<<"$out")" >&2
  exit 2
fi
exit 0
```

Exit codes for Stop: **0** lets Claude stop (stdout JSON is applied if present); **2** blocks the stop and feeds stderr to Claude as the reason; **any other** code is a non-blocking error and Claude stops. Instead of exit 2 you can print `{"decision": "block", "reason": "…"}` and exit 0. `stop_hook_active` is `true` when Claude is already continuing because of a Stop hook; after 8 consecutive blocks Claude Code ends the turn anyway (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). Keep the check fast (lint and unit tests, not the full end-to-end suite), or the hook dominates every turn.

Choose: `/goal` for one task's end state, typed per session; a Stop hook for a rule every session must meet; `/loop` for re-running on a time interval; scheduled tasks or cloud routines for work independent of an open session.

## 3. Isolate the run

- **Sandbox first.** A Docker Sandbox (`sbx`) on a worktree branch: its own Docker engine so the agent runs the stack and integration tests itself, a network allowlist from the repo's kit, no production secrets, never the host Docker socket. Setup and audit in `agent-sandbox.md`; start it with `/sbx <type>/<name>`, and hand over the task with its "Hand over an autonomous task" section. `sbx run claude` starts Claude with `--dangerously-skip-permissions` by default, which is why the boundary matters. The workspace is a bind mount of real host files: what the agent deletes is gone on the host too.
- **Worktree without a sandbox:** `claude -w <name>` gives an isolated checkout; edits don't collide with your own work, but the agent still has your machine's network and credentials.
- **No production credentials** in the sandbox, the env or MCP configs used by the run. Deploys stay with CI and people.

## 4. Permissions for unattended runs

| Setup | Command | Where |
|-|-|-|
| Auto mode | `claude --permission-mode auto` | Interactive or `-p`; a classifier reviews actions and blocks risky ones. A sandbox adds defence in depth |
| Exact allowlist | `claude -p "…" --permission-mode dontAsk --allowedTools "Read" "Edit" "Bash(task check)"` | CI and scripts: anything not pre-approved is denied, the run never waits |
| Permissions skipped | `--dangerously-skip-permissions` (= `bypassPermissions`) | Only inside a container, VM or sandbox, as a non-root user. Never on the host |

Deny rules apply in every mode. Add `--permission-prompts none` when nobody can answer prompts in a `-p` run, so blocked actions are denied rather than waited on.

## 5. Headless runs and fan-out

`claude -p` runs one prompt non-interactively and exits non-zero on failure:

```bash
claude --bare -p "Fix the failing test in tests/test_auth.py; run it and show the output" \
  --permission-mode dontAsk --allowedTools "Read" "Edit" "Bash(uv run pytest *)" \
  --max-turns 30 --max-budget-usd 5 --output-format json | jq -r '.result'
```

`--bare` skips local hooks, plugins, CLAUDE.md and MCP config, so CI gets the same result on every machine (it needs `ANTHROPIC_API_KEY`). `--max-turns` and `--max-budget-usd` bound the run (print mode only).

**Fan-out over many files:** `/batch <instruction>` splits a change across subagents in their own worktrees. To drive it from a script, generate the task list first, then loop with scoped tools:

```bash
while read -r f; do
  claude -p "Migrate $f to the new API per docs/migration.md. Run its tests. Reply OK or FAIL: <reason>." \
    --permission-mode dontAsk --allowedTools "Read" "Edit" "Bash(uv run pytest $f*)" --max-turns 15
done < files.txt
```

Run it on 2-3 items, fix the prompt from what goes wrong, then run the rest.

## 6. Rollback points and context hygiene

- **Commit per finished step** on the run's branch. Checkpoints (`Esc Esc`, `/rewind`) restore file edits made by Claude's edit tools only; changes made through Bash or other processes are not captured. Git is the rollback.
- **One task per session.** `/clear` between unrelated tasks; after two failed corrections, clear and restart with a better prompt.
- **Subagents for research,** so reading many files doesn't fill the main context. Put "when compacting, keep the list of modified files and the check command" in CLAUDE.md for long runs.

## 7. Bounded loops

Every unattended loop has an explicit end: a turn or time clause in the `/goal` condition, `--max-turns` and `--max-budget-usd` for `-p`, the Stop hook's `stop_hook_active` early exit, a fixed item list for fan-out. Ask for a final report: what is done, the evidence (command and output), what is open.

## 8. Review before merge

- **Small pull requests** (profile size guide); a long run commits in slices that can become separate pull requests.
- **Writer/reviewer split.** A fresh context reviews the diff against the spec; the writer doesn't grade its own work. Bundled: `/code-review`. Against a spec:

```text
Use a subagent to review the diff on this branch against <spec or issue>. Report only gaps that
affect correctness or the stated requirements: bugs, missing requirements, broken contracts,
security issues. No style preferences, no speculative hardening.
```

  A reviewer asked for gaps will find some; chasing every one leads to over-engineering. Fix correctness gaps, treat the rest as optional.
- **A person reads the evidence and the diff** and runs the check once outside the run before merging. Evidence is faster to review than re-running everything; it does not replace reading the diff.

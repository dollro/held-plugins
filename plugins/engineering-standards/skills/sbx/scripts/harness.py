#!/usr/bin/env python3
"""Build a personal sbx kit (v2 mixin) that gives a sandboxed Claude Code the
user-level harness of the host: marketplaces, plugins, user skills, CLAUDE.md,
user agents/commands/output styles, an allowlist of settings, the status line
script, and the list of MCP servers to pass as --static-mcp. Called by
sandbox.sh; reads the host config at run time. Never copies credentials,
~/.claude.json, history, projects, memory, sessions, permissions, env, hooks,
or MCP server configs (names and transport only).

The user decides what goes in: <kit-dir>/harness.selection.json lists every
candidate with "enabled": true|false. Earlier decisions are kept; new
candidates get a default and are marked "new": true until reviewed.

  harness.py select   <kit-dir>          write/refresh the selection, print it;
                                         exit 5 when it needs review
  harness.py generate <kit-dir>          build spec.yaml from the selection
  harness.py status   <kit-dir>          drift: stale kit, new candidates
  harness.py hash     <kit-dir>          hash of what the kit would contain now

Output lines start with OK, WARN, INFO or FAIL (like sandbox.sh).
"""
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.parse import urlparse

VERSION = "3"  # bump when the generated kit changes shape (forces "stale")
# Appended to the sandbox's user CLAUDE.md: the agent inside never sees the
# host's memory and rarely opens the reference unless something points at it.
SANDBOX_NOTE = """
## Inside a Docker Sandbox (added by the sbx harness kit)

You run inside an `sbx` sandbox (`$SANDBOX_NAME` is set). Before working around a missing tool or a failing command, read engineering-standards `references/agent-sandbox.md` (Test loop, Troubleshooting).

- Use the repo's sandbox-aware tasks (CLAUDE.md, Taskfile) before composing commands by hand. If the repo's CLAUDE.md names tasks this branch lacks, the branch predates them: say so, and merge the base branch only with the user's agreement.
- Tools the sandbox lacks (pnpm, Playwright browsers, a newer runtime) run in containers, not installed here: the image CI uses, pinned to the project's version. Node tools already installed run from `node_modules/.bin/<tool>`.
- Tools installed with uv or pipx land in `~/.local/bin`; git hooks and non-login shells may not have it on PATH. Call them by full path and tell the user the kit should link them into `/usr/local/bin`.
- The host's auto-memory does not exist here. A fact you had to rediscover belongs in the repo's CLAUDE.md: propose the line.
"""
KIT_NAME = "claude-harness"
HOME = Path.home()
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude")
CLAUDE_JSON = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME) / ".claude.json"
AGENT_CLAUDE = "/home/agent/.claude"
SEL_FILE = "harness.selection.json"
NEEDS_REVIEW = 5
SKILLS_MAX_BYTES = 5 * 1024 * 1024

# Settings keys that shape the harness and hold no secrets or host paths.
SETTINGS_ALLOW = [
    "model", "effortLevel", "alwaysThinkingEnabled", "autoCompactEnabled",
    "attribution", "includeCoAuthoredBy", "outputStyle", "language", "theme",
    "spinnerTipsEnabled", "cleanupPeriodDays", "autoUpdates",
]
# Never copied, named in the output so the user sees what stayed behind.
SETTINGS_DENY = ["env", "permissions", "hooks", "apiKeyHelper", "awsAuthRefresh",
                 "awsCredentialExport", "otelHeadersHelper", "mcpServers",
                 "enableAllProjectMcpServers", "enabledMcpjsonServers"]
GITHUB_HOSTS = ["github.com", "codeload.github.com", "api.github.com",
                "objects.githubusercontent.com", "raw.githubusercontent.com"]
COPY_DIRS = ["agents", "commands", "output-styles"]  # *.md, user level
HOST_ONLY_PLUGIN = re.compile(r"chrome|browser|computer-use|playwright|devtools|desktop", re.I)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}
SECRET_RE = re.compile(
    r"(ghp_|gho_|ghu_|ghs_|github_pat_|glpat-|sk-ant-|sk-[A-Za-z0-9]{20,}|xox[abpr]-|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
CATEGORIES = ["marketplaces", "plugins", "skills", "mcpServers", "files", "settings"]
QUIET = False
HOST_RE = re.compile(r"^(\*\.)?[A-Za-z0-9.-]+(:[0-9]+)?$")


def out(tag, msg):
    if not QUIET:
        print(f"{tag:<5} {msg}")


def load_json(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def has_secret(text):
    m = SECRET_RE.search(text)
    return m.group(0)[:6] + "…" if m else None


def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def mk_source(src):
    """marketplace source -> (arg for `marketplace add`, host, None) or (None, None, reason)."""
    kind = src.get("source")
    if kind == "github" and src.get("repo"):
        if src.get("ref") or src.get("path"):
            return None, None, "github source with ref/path; add it by hand"
        return src["repo"], "github.com", None
    if kind in ("git", "url") and src.get("url"):
        host = urlparse(src["url"]).hostname
        return (src["url"], host, None) if host else (None, None, "unparsable url")
    if kind in ("directory", "file"):
        return None, None, "local path on the host, unreachable from the sandbox; publish it to a git host"
    return None, None, f"unsupported source type {kind!r}"


def submodule_hosts(install_location):
    """Hosts of git submodules in the host's clone of a marketplace (cloned inside too)."""
    hosts = set()
    gm = Path(install_location or "/nonexistent") / ".gitmodules"
    if gm.is_file():
        for m in re.finditer(r"url\s*=\s*(\S+)", gm.read_text()):
            u = m.group(1)
            h = urlparse(u).hostname if "://" in u else (u.split("@")[-1].split(":")[0] if ":" in u else None)
            if h:
                hosts.add(h.lower())
    return hosts


def skill_dirs():
    """name -> (host dir, origin) for user skills and the sbx skills store."""
    found = {}
    sk = CLAUDE / "skills"
    if sk.is_dir():
        for e in sorted(sk.iterdir()):
            if e.is_dir() and (e / "SKILL.md").is_file():
                found[e.name] = (e.resolve(), "~/.claude/skills")
    rc, txt = run(["sbx", "skills", "ls"])
    if rc == 0:
        for line in txt.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in found:
                d = Path(parts[1]) / parts[0]
                if (d / "SKILL.md").is_file():
                    found[parts[0]] = (d, "sbx skills store")
    return found


def sbx_mcp_names():
    rc, txt = run(["sbx", "mcp", "ls", "-q"])
    return {l.strip() for l in txt.splitlines() if l.strip()} if rc == 0 else set()


def candidates():
    """Every item that could go into the sandbox, with a default and a reason.
    Returns (cands, ctx); cands[category][name] = {"enabled", "reason", ...}."""
    settings = load_json(CLAUDE / "settings.json")
    known = load_json(CLAUDE / "plugins" / "known_marketplaces.json")
    extra = settings.get("extraKnownMarketplaces") or {}
    enabled = [p for p, on in (settings.get("enabledPlugins") or {}).items() if on is True and "@" in p]
    c = {k: {} for k in CATEGORIES}
    ctx = {"markets": {}, "skills": {}, "files": {}, "settings": settings, "mcp_registered": set()}

    for name in sorted(set(extra) | {p.rsplit("@", 1)[1] for p in enabled}):
        entry = extra.get(name) or known.get(name) or {}
        src = entry.get("source") if isinstance(entry.get("source"), dict) else {}
        arg, host, why = mk_source(src) if src else (None, None, "not in known_marketplaces.json")
        used = any(p.rsplit("@", 1)[1] == name for p in enabled)
        if arg and not used:
            why = "no enabled plugin comes from it"
        c["marketplaces"][name] = {"enabled": arg is not None and used, "source": arg or src.get("path") or "?",
                                   "reason": why or ""}
        if arg:
            hosts = {host} | submodule_hosts((known.get(name) or {}).get("installLocation"))
            ctx["markets"][name] = {"add": arg, "hosts": sorted(hosts), "source": src, "entry": entry}

    for p in sorted(enabled):
        reason = "drives a browser or desktop on the host" if HOST_ONLY_PLUGIN.search(p) else ""
        c["plugins"][p] = {"enabled": not reason, "reason": reason}

    for name, (d, origin) in skill_dirs().items():
        c["skills"][name] = {"enabled": True, "reason": "", "from": origin}
        ctx["skills"][name] = d

    cj = load_json(CLAUDE_JSON)
    registered = sbx_mcp_names()
    ctx["mcp_registered"] = registered
    for name, v in sorted((cj.get("mcpServers") or {}).items()):
        transport = v.get("type") or ("http" if v.get("url") else "stdio")
        host = (urlparse(v["url"]).hostname or "") if v.get("url") else ""
        if name in registered:
            reason = ""
        elif host.lower() in LOCAL_HOSTS:
            reason = "points at a service on the host"
        elif v.get("env") or v.get("headers"):
            reason = "needs credentials; register it with sbx mcp add so they stay on the host"
        else:
            reason = "not registered with sbx mcp; register it to use it"
        c["mcpServers"][name] = {"enabled": not reason, "transport": transport,
                                 "sbx": name in registered, "reason": reason}
    for name in sorted(registered - set(c["mcpServers"])):
        c["mcpServers"][name] = {"enabled": True, "transport": "sbx", "sbx": True, "reason": ""}

    def add_file(rel, path):
        t = path.read_text(errors="replace")
        s = has_secret(t)
        c["files"][rel] = {"enabled": not s, "reason": f"looks like a secret ({s}); never copied" if s else ""}
        if not s:
            ctx["files"][rel] = t
    if (CLAUDE / "CLAUDE.md").is_file():
        add_file("CLAUDE.md", CLAUDE / "CLAUDE.md")
    for d in COPY_DIRS:
        if (CLAUDE / d).is_dir():
            for f in sorted((CLAUDE / d).glob("*.md")):
                add_file(f"{d}/{f.name}", f)
    sl = settings.get("statusLine")
    ctx["statusline"] = None
    if isinstance(sl, dict) and sl.get("type") == "command" and str(sl.get("command", "")).strip():
        first = str(sl["command"]).split()[0]
        script = Path(os.path.expanduser(first))
        if script.is_file() and CLAUDE.resolve() in script.resolve().parents:
            rel = script.resolve().relative_to(CLAUDE.resolve()).as_posix()
            add_file(rel, script)
            ctx["statusline"] = (rel, sl, str(sl["command"])[len(first):])

    for k in SETTINGS_ALLOW:
        if k in settings:
            c["settings"][k] = {"enabled": True, "reason": ""}
    if ctx["statusline"]:
        c["settings"]["statusLine"] = {"enabled": True, "reason": "with its script"}
    elif "statusLine" in settings:
        c["settings"]["statusLine"] = {"enabled": False, "reason": "command is not a script under ~/.claude"}
    ctx["denied"] = [k for k in SETTINGS_DENY if k in settings]
    return c, ctx


def merge_selection(cands, old):
    """Keep earlier decisions; mark new candidates. Returns (selection, new_items)."""
    sel, new = {"_help": "Set enabled to false for anything the sandbox must not get, "
                         "then run: sandbox.sh harness --yes. networkAllow: extra hosts for the kit "
                         "(e.g. git submodule hosts of a marketplace, from sbx policy log). "
                         "No secrets live in this file.",
                "networkAllow": [h for h in old.get("networkAllow") or [] if HOST_RE.match(str(h))]}, []
    for cat in CATEGORIES:
        sel[cat] = {}
        for name, item in cands[cat].items():
            prev = (old.get(cat) or {}).get(name)
            it = dict(item)
            locked = cat == "files" and item["reason"].startswith("looks like a secret")
            if prev is not None and not locked:
                it["enabled"] = bool(prev.get("enabled"))
                if prev.get("new"):
                    it["new"] = True
            else:
                it["new"] = True
                new.append(f"{cat}/{name}")
            sel[cat][name] = it
    return sel, new


def effective(sel, ctx):
    """What the kit contains, from the selection and the host config."""
    on = lambda cat: [n for n, v in sel.get(cat, {}).items() if v.get("enabled")]
    markets = {n: ctx["markets"][n] for n in on("marketplaces") if n in ctx["markets"]}
    plugins = sorted(p for p in on("plugins") if p.rsplit("@", 1)[1] in markets)
    settings = ctx["settings"]
    harness = {k: settings[k] for k in on("settings") if k in SETTINGS_ALLOW and k in settings}
    harness["enabledPlugins"] = {p: True for p in plugins}
    ekm = {n: v for n, v in (settings.get("extraKnownMarketplaces") or {}).items() if n in markets}
    if ekm:
        harness["extraKnownMarketplaces"] = ekm
    files = {r: t for r, t in ctx["files"].items() if r in on("files")}
    files["CLAUDE.md"] = files.get("CLAUDE.md", "").rstrip("\n") + "\n" + SANDBOX_NOTE
    sl = ctx["statusline"]
    if sl and "statusLine" in on("settings") and sl[0] in files:
        harness["statusLine"] = {**sl[1], "command": f"{AGENT_CLAUDE}/{sl[0]}{sl[2]}"}
    elif sl and sl[0] in files and "statusLine" not in on("settings"):
        files.pop(sl[0])
    skills = {n: ctx["skills"][n] for n in on("skills") if n in ctx["skills"]}
    mcp_on = on("mcpServers")
    return {"version": VERSION, "markets": markets, "plugins": plugins, "settings": harness,
            "files": files, "skills": skills,
            "static_mcp": sorted(n for n in mcp_on if n in ctx["mcp_registered"]),
            "mcp_unregistered": sorted(n for n in mcp_on if n not in ctx["mcp_registered"]),
            "network": sorted(h for h in sel.get("networkAllow") or [] if HOST_RE.match(str(h))),
            "skipped_plugins": sorted(p for p in on("plugins") if p.rsplit("@", 1)[1] not in markets)}


def skills_tar(skills):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.PAX_FORMAT) as tf:
        for name, d in sorted(skills.items()):
            for f in sorted(Path(d).rglob("*")):
                if f.is_symlink() or not f.is_file():
                    continue
                if f.name.startswith(".env") or f.suffix in (".pem", ".key"):
                    continue
                ti = tf.gettarinfo(str(f), arcname=f"{name}/{f.relative_to(d).as_posix()}")
                ti.uid = ti.gid = 1000
                ti.uname = ti.gname = ""
                ti.mtime = 0
                with open(f, "rb") as fh:
                    tf.addfile(ti, fh)
    return buf.getvalue()


def digest(eff):
    core = {k: eff[k] for k in ("version", "plugins", "settings", "files", "static_mcp", "network")}
    core["markets"] = {n: m["add"] for n, m in eff["markets"].items()}
    core["skills"] = hashlib.sha256(skills_tar(eff["skills"])).hexdigest() if eff["skills"] else ""
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def b64_lines(data):
    b = base64.b64encode(data if isinstance(data, bytes) else data.encode()).decode()
    return [b[i:i + 76] for i in range(0, len(b), 76)]


def indent(lines, n):
    return "\n".join(" " * n + l if l else "" for l in lines)


def last_err(f="/tmp/sbx-h.out"):
    return f'$(grep -m1 -iE "error|fail|denied|not found" {f} || tail -1 {f})'


def spec_yaml(eff, sha):
    pre = ["set -u", 'CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"; mkdir -p "$CFG"', 'LOG="$CFG/.sbx-harness.log"']
    files_cmd = pre + [': > "$LOG"']
    for rel, text in sorted(eff["files"].items()):
        dest = f'"$CFG/{rel}"'
        files_cmd += [f'mkdir -p "$(dirname {dest})"', f"base64 -d > {dest} <<'SBX_EOF'"]
        files_cmd += b64_lines(text) + ["SBX_EOF", f"chmod {'755' if rel.endswith('.sh') else '644'} {dest}",
                                        f'echo "OK    file {rel}" >> "$LOG"']
    if eff["skills"]:
        files_cmd += ['mkdir -p "$CFG/skills"', "base64 -d <<'SBX_EOF' | tar -xzf - -C \"$CFG/skills\" --no-same-owner"]
        files_cmd += b64_lines(skills_tar(eff["skills"])) + ["SBX_EOF"]
        files_cmd += [f'[ -f "$CFG/skills/{n}/SKILL.md" ] && echo "OK    skill {n}" >> "$LOG" || echo "FAIL  skill {n}" >> "$LOG"'
                      for n in sorted(eff["skills"])]

    plug_cmd = pre + ['CL=$(command -v claude || echo "$HOME/.local/bin/claude")',
                      'if [ ! -x "$CL" ]; then echo "FAIL  claude CLI not found; no plugins installed" >> "$LOG"; exit 0; fi']
    for name, m in sorted(eff["markets"].items()):
        plug_cmd.append(f'if "$CL" plugin marketplace add "{m["add"]}" --scope user </dev/null >/tmp/sbx-h.out 2>&1; '
                        f'then echo "OK    marketplace {name}" >> "$LOG"; '
                        f'else echo "FAIL  marketplace {name} ({m["add"]}): {last_err()}" >> "$LOG"; fi')
    for p in eff["plugins"]:
        plug_cmd.append(f'if "$CL" plugin install "{p}" --scope user </dev/null >/tmp/sbx-h.out 2>&1; '
                        f'then echo "OK    plugin {p}" >> "$LOG"; '
                        f'else echo "FAIL  plugin {p}: {last_err()}" >> "$LOG"; fi')
    plug_cmd.append("exit 0")

    merge_py = ("import json,sys\n"
                "p,f=sys.argv[1],json.load(open(sys.argv[2]))\n"
                "try: s=json.load(open(p))\n"
                "except Exception: s={}\n"
                "for k,v in f.items():\n"
                "    s[k]={**s[k],**v} if isinstance(v,dict) and isinstance(s.get(k),dict) else v\n"
                "json.dump(s,open(p,'w'),indent=2)\n")
    mb = base64.b64encode(merge_py.encode()).decode()
    set_cmd = pre + ['S="$CFG/settings.json"', '[ -f "$S" ] || echo "{}" > "$S"', "base64 -d > /tmp/sbx-h.json <<'SBX_EOF'"]
    set_cmd += b64_lines(json.dumps(eff["settings"], sort_keys=True)) + ["SBX_EOF"]
    set_cmd += [
        f'if command -v python3 >/dev/null; then python3 -c "$(echo {mb} | base64 -d)" "$S" /tmp/sbx-h.json && M=python3',
        'elif command -v jq >/dev/null; then jq -s \'.[0] as $a | $a + (.[1] | with_entries(.value = (if (.value|type)=="object" and ($a[.key]|type)=="object" then $a[.key] + .value else .value end)))\' "$S" /tmp/sbx-h.json > "$S.new" && mv "$S.new" "$S" && M=jq',
        'else M=""; fi',
        'if [ -n "$M" ]; then echo "OK    settings merged ($M)" >> "$LOG"; else echo "FAIL  settings: no python3 or jq to merge" >> "$LOG"; fi',
        'rm -f /tmp/sbx-h.json /tmp/sbx-h.out',
        f'echo "{sha}" > "$CFG/.sbx-harness.sha256"',
        "exit 0",
    ]
    allow = sorted(set(GITHUB_HOSTS) | {h for m in eff["markets"].values() for h in m["hosts"]} | set(eff["network"]))
    y = ["# Generated by sandbox.sh harness from this machine's user-level Claude Code",
         "# setup and harness.selection.json. Personal: never commit. Regenerate: sandbox.sh harness",
         f"# source-sha256: {sha}",
         'schemaVersion: "2"', "kind: mixin", f"name: {KIT_NAME}",
         "description: Claude Code harness of the host user (plugins, skills, CLAUDE.md, settings)",
         "permissions:", "  network:", "    allow:"] + [f"      - {a}" for a in allow] + [
         "setup:", "  install:",
         "    - description: Claude Code user files (CLAUDE.md, agents, skills, status line)",
         '      user: "1000"', "      command: |", indent(files_cmd, 8),
         "    - description: Claude Code marketplaces and plugins",
         '      user: "1000"', "      command: |", indent(plug_cmd, 8),
         "    - description: Merge harness settings into the agent's settings.json",
         '      user: "1000"', "      command: |", indent(set_cmd, 8)]
    return "\n".join(y) + "\n"


def print_table(sel):
    for cat in CATEGORIES:
        items = sel.get(cat) or {}
        if not items:
            continue
        print(f"TABLE {cat}:")
        for name, v in items.items():
            mark = "on " if v.get("enabled") else "off"
            extra = "  NEW" if v.get("new") else ""
            why = f"  ({v['reason']})" if v.get("reason") else ""
            print(f"TABLE   [{mark}] {name}{extra}{why}")


def probe_public(repo):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
    try:
        r = subprocess.run(["git", "-c", "credential.helper=", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                           env=env, capture_output=True, timeout=20)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return None


def cmd_select(kit, yes):
    kit.mkdir(parents=True, exist_ok=True)
    os.chmod(kit, 0o700)
    cands, _ = candidates()
    sf = kit / SEL_FILE
    old = load_json(sf)
    sel, new = merge_selection(cands, old)
    if yes:  # reviewed: clear the NEW marks
        for cat in CATEGORIES:
            for v in sel[cat].values():
                v.pop("new", None)
    sf.write_text(json.dumps(sel, indent=2) + "\n")
    pending = [f"{c}/{n}" for c in CATEGORIES for n, v in sel[c].items() if v.get("new")]
    if pending:
        print_table(sel)
        out("WARN", f"selection needs review: {sf} ({len(pending)} new item(s)); set enabled:false for what the sandbox must not get, then: sandbox.sh harness --yes")
        return NEEDS_REVIEW
    return 0


def cmd_generate(kit):
    if not (CLAUDE / "settings.json").is_file():
        out("FAIL", f"no {CLAUDE}/settings.json; nothing to sync")
        return 1
    _, ctx = candidates()
    sel = load_json(kit / SEL_FILE)
    eff = effective(sel, ctx)
    size = len(skills_tar(eff["skills"])) if eff["skills"] else 0
    if size > SKILLS_MAX_BYTES:
        out("FAIL", f"selected skills are {size // 1024} KiB compressed (limit {SKILLS_MAX_BYTES // 1024} KiB); disable big ones")
        return 1
    sha = digest(eff)
    for old in (kit / "copies").rglob("*") if (kit / "copies").exists() else []:
        if old.is_file():
            old.unlink()
    (kit / "copies").mkdir(exist_ok=True)
    for rel, text in eff["files"].items():  # readable copies for review; spec.yaml embeds them
        p = kit / "copies" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    (kit / "copies" / "settings.harness.json").write_text(json.dumps(eff["settings"], indent=2, sort_keys=True) + "\n")
    (kit / "spec.yaml").write_text(spec_yaml(eff, sha))
    (kit / "harness.sha256").write_text(sha + "\n")
    (kit / "static-mcp.txt").write_text("".join(n + "\n" for n in eff["static_mcp"]))

    out("OK", f"harness kit {kit} (source-sha256 {sha[:12]})")
    out("OK", f"{len(eff['markets'])} marketplace(s), {len(eff['plugins'])} plugin(s), {len(eff['skills'])} skill(s), "
              f"{len(eff['files'])} file(s), settings: {', '.join(sorted(eff['settings']))}")
    off = {cat: [n for n, v in sel.get(cat, {}).items() if not v.get("enabled")] for cat in CATEGORIES}
    for cat, names in off.items():
        if names:
            out("INFO", f"{cat} left out: {', '.join(names)}")
    if eff["skipped_plugins"]:
        out("WARN", f"plugins left out because their marketplace is off or unreachable: {', '.join(eff['skipped_plugins'])}")
    if ctx["denied"]:
        out("INFO", f"never copied: {', '.join(ctx['denied'])} (secrets, host paths, per-machine trust)")
    if eff["static_mcp"]:
        out("OK", f"MCP servers through the sbx gateway (--static-mcp at create): {','.join(eff['static_mcp'])}")
    for n in eff["mcp_unregistered"]:
        out("WARN", f"MCP server {n} is selected but not registered with sbx: register it on the host (sbx mcp add {n} --url <endpoint or server manifest>; see sbx mcp add --help), then: sandbox.sh harness")
    private = []
    for n, m in eff["markets"].items():
        if m["source"].get("source") == "github":
            if probe_public(m["add"]) is False:
                private.append(f"{n} ({m['add']})")
        elif "github.com" not in m["hosts"]:
            out("WARN", f"marketplace {n} on {m['hosts'][0]}: a private repo there cannot authenticate from the sandbox")
        extra_hosts = [h for h in m["hosts"] if h not in GITHUB_HOSTS]
        if m["source"].get("source") == "github" and extra_hosts:
            out("INFO", f"marketplace {n} has git submodules on {', '.join(extra_hosts)}; allowed in the kit")
    if private:
        out("INFO", f"private (or unreachable) GitHub marketplaces: {', '.join(private)}")
        print("PRIVATE_GITHUB=1")
    return 0


def cmd_status(kit):
    """Exit 0 current, 1 stale kit, 2 missing, 5 new candidates to review."""
    global QUIET
    QUIET = True
    if not (kit / "spec.yaml").is_file():
        return 2
    cands, ctx = candidates()
    sel = load_json(kit / SEL_FILE)
    _, new = merge_selection(cands, sel)
    new += [f"{c}/{n}" for c in CATEGORIES for n, v in (sel.get(c) or {}).items() if v.get("new")]
    if new:
        print("NEW " + " ".join(sorted(set(new))))
        return NEEDS_REVIEW
    have = (kit / "harness.sha256").read_text().strip() if (kit / "harness.sha256").is_file() else ""
    return 0 if digest(effective(sel, ctx)) == have else 1


def main():
    global QUIET
    a = sys.argv[1:]
    if len(a) >= 2:
        kit = Path(a[1]).expanduser()
        if a[0] == "select":
            return cmd_select(kit, "--yes" in a)
        if a[0] == "generate":
            return cmd_generate(kit)
        if a[0] == "status":
            return cmd_status(kit)
        if a[0] == "hash":
            QUIET = True
            _, ctx = candidates()
            print(digest(effective(load_json(kit / SEL_FILE), ctx)))
            return 0
    print(__doc__.strip().split("\n\n")[2])
    return 1


if __name__ == "__main__":
    sys.exit(main())

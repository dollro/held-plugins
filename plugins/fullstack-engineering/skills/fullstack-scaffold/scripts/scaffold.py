#!/usr/bin/env python3
"""Generate a new repo on the fullstack reference stack.

    python scaffold.py <target-dir> --name atlas-portal [--title "Atlas Portal"]
        [--app-host app.example.com] [--no-realtime] [--ci github|gitlab|both|none]
        [--audience internal|external|mixed] [--age-recipient age1...] [--skip-install]

The template holds no dependency versions. Unless --skip-install is given, the
script resolves the packages in stack.json to their current releases with
`uv add` and `pnpm add`, so the new repo starts with fresh lockfiles.
Requires: uv and pnpm on PATH (and sops, if --age-recipient is given).
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "template"
STACK = json.loads((SKILL_DIR / "stack.json").read_text())
# Optional parts are fenced by markers named after a feature: line markers
# (`>>> sso` ... `<<< sso`, in any comment syntax, may nest; `!sso` = without)
# and inline HTML markers (`<!-- >>> sso -->...<!-- <<< sso -->`).
# A line marker is a whole comment line, so `>>> x` in ordinary text (doctests,
# shell here-strings, upstream files) is never mistaken for one.
LINE_MARKER = re.compile(
    r"^\s*(?:#|//|\{#|<!--)\s*(>>>|<<<) (!?[a-z]+)\s*(?:#\}|-->)?\s*$"
)
INLINE_BLOCK = re.compile(r"<!-- >>> (!?[a-z]+) -->(.*?)<!-- <<< \1 -->", re.S)
# Login audience -> features. sso: company SSO over OpenID Connect; accounts: local accounts
# with email verification and MFA; internal/external/mixed: audience-only parts.
AUDIENCES = {
    "internal": {"internal", "sso"},
    "external": {"external", "accounts"},
    "mixed": {"mixed", "sso", "accounts"},
}
TEXT_SUFFIXES = {
    "", ".py", ".ts", ".vue", ".json", ".yml", ".yaml", ".toml", ".md", ".html",
    ".css", ".ini", ".mako", ".hcl", ".sh", ".example", ".env", ".cfg", ".txt",
}
# Files that exist only with a feature.
FEATURE_PATHS = {
    "realtime": ["realtime", "docker/app/start-realtime", "docker/app/start-realtime-dev"],
    "sso": ["backend/users/tests/test_sso.py"],
    "accounts": ["backend/users/policy.py", "backend/users/tests/test_accounts.py"],
    "mixed": ["backend/users/backends.py", "backend/users/tests/test_mixed.py"],
}
SKIP_DIRS = {"node_modules", ".venv", ".git", ".ruff_cache", ".pytest_cache"}


def project_files(target: Path):
    for path in target.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and not SKIP_DIRS & set(path.parts):
            yield path


def log(message: str) -> None:
    print(f"==> {message}", file=sys.stderr)


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> str:
    log(" ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,  # never wait for an interactive prompt
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return result.stdout.strip()


def tool_version(cmd: list[str]) -> str:
    output = subprocess.run(cmd, text=True, capture_output=True).stdout
    match = re.search(r"\d+\.\d+\.\d+", output)
    if not match:
        raise SystemExit(f"could not read version from: {' '.join(cmd)}")
    return match.group(0)


def enabled(tag: str, features: set[str]) -> bool:
    return (tag[1:] not in features) if tag.startswith("!") else (tag in features)


def strip_markers(text: str, features: set[str]) -> str:
    """Keep the parts whose markers are enabled; drop the marker lines themselves."""
    while (inline := INLINE_BLOCK.search(text)) is not None:
        kept = inline[2] if enabled(inline[1], features) else ""
        text = text[: inline.start()] + kept + text[inline.end() :]
    out, stack = [], []
    for line in text.splitlines(keepends=True):
        marker = LINE_MARKER.search(line)
        if marker and marker[1] == ">>>":
            stack.append(marker[2])
        elif marker:
            if not stack or stack[-1] != marker[2]:
                raise SystemExit(f"unbalanced marker '{marker[0]}' in line: {line.strip()}")
            stack.pop()
        elif all(enabled(tag, features) for tag in stack):
            out.append(line)
    if stack:
        raise SystemExit(f"unclosed markers: {stack}")
    return "".join(out)


def key_prefix(name: str) -> str:
    initials = "".join(part[0] for part in name.split("-") if part)
    return (initials if len(initials) >= 2 else name[:3]).lower()


def copy_template(target: Path, ci: str, features: set[str]) -> None:
    shutil.copytree(
        TEMPLATE, target, dirs_exist_ok=True,  # an existing empty target is fine
        ignore=shutil.ignore_patterns("ci", "__pycache__", ".ruff_cache", ".pytest_cache", "node_modules"),
    )
    ci_root = TEMPLATE / "ci"
    if ci in ("github", "both"):
        shutil.copytree(ci_root / "github", target, dirs_exist_ok=True)
    if ci in ("gitlab", "both"):
        shutil.copytree(ci_root / "gitlab", target, dirs_exist_ok=True)
    for feature, paths in FEATURE_PATHS.items():
        if feature not in features:
            for rel in paths:
                path = target / rel
                shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)


def render(target: Path, values: dict[str, str], features: set[str] | None) -> None:
    """Substitute placeholders; strip markers only on the first pass (features
    given), never in files that create-vue or pnpm wrote later."""
    for path in project_files(target):
        text = path.read_text()
        new = text
        if features is not None:
            try:
                new = strip_markers(text, features)
            except SystemExit as exc:
                raise SystemExit(f"{path.relative_to(target)}: {exc}") from None
        for key, value in values.items():
            new = new.replace(key, value)
        # Marker stripping can leave whitespace-only lines; pre-commit would flag them.
        new = "\n".join(line.rstrip() for line in new.split("\n"))
        if new.strip():  # exactly one trailing newline, even after removed blocks
            new = new.rstrip("\n") + "\n"
        if new != text:
            path.write_text(new)

LATE_PLACEHOLDERS = {"__PLAYWRIGHT_VERSION__", "__PLAYWRIGHT_MCP_VERSION__"}  # known after install
# Real identifiers that look like placeholders.
LITERALS: set[str] = set()


def assert_rendered(target: Path, allow: set[str]) -> None:
    leftovers = []
    for path in project_files(target):
        found = set(re.findall(r"__[A-Z][A-Z_]+__", path.read_text())) - allow - LITERALS
        if found:
            leftovers.append(f"{path.relative_to(target)} {sorted(found)}")
    if leftovers:
        raise SystemExit("unreplaced placeholders:\n  " + "\n  ".join(leftovers))


def install_python(target: Path, features: set[str]) -> None:
    python = STACK["python"]
    extras = sorted(extra for feature, extra in python["allauth_extras"].items() if feature in features)
    core = [*python["core"], f"django-allauth[{','.join(extras)}]"]
    if "realtime" in features:
        core += python["realtime"]
    run(["uv", "add", "--no-sync", *core], target)
    run(["uv", "add", "--no-sync", "--dev", *python["dev"]], target)
    run(["uv", "add", "--no-sync", "--group", "docs", *python["docs"]], target)


def create_frontend(target: Path, name: str, pnpm_version: str) -> str:
    """Run create-vue for the tooling, then lay the project's own files over it.

    create-vue owns tsconfig, ESLint/Oxlint, Vitest and package.json, so they
    follow the current Vue recommendations; the template owns the Django
    integration (vite.config.ts), src/, the Playwright config and tests.
    """
    cfg = STACK["node"]
    frontend = target / "frontend"
    # The directory name becomes a package name: no leading dot.
    generated = target / "create-vue-output"
    run(["pnpm", "dlx", "create-vue@latest", generated.name, *cfg["create_vue_flags"]], target)
    if not (generated / "package.json").exists():
        raise SystemExit("create-vue produced no project; run it by hand to see why")
    for rel in cfg["create_vue_remove"]:
        path = generated / rel
        shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
    eslint_config = generated / "eslint.config.ts"
    if not eslint_config.exists():
        raise SystemExit("create-vue no longer writes eslint.config.ts; update create_frontend()")
    eslint_config.rename(generated / "eslint.config.base.ts")
    for path in sorted(generated.rglob("*")):
        dest = frontend / path.relative_to(generated)
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        elif not dest.exists():  # the template's overlay wins
            shutil.copy2(path, dest)
    shutil.rmtree(generated)

    package_file = frontend / "package.json"
    package = json.loads(package_file.read_text())
    package["name"] = f"{name}-frontend"
    package["packageManager"] = f"pnpm@{pnpm_version}"
    scripts = package.setdefault("scripts", {})
    scripts["build-only"] = "vite build"
    has_oxlint = "oxlint" in package.get("devDependencies", {})
    # ci:* rather than lint:ci, which create-vue's `lint` (run-s "lint:*") would run too.
    scripts["ci:lint"] = ("oxlint . --deny-warnings && " if has_oxlint else "") + (
        "eslint . --max-warnings 0"
    )
    scripts["ci:test-unit"] = "vitest run"
    package_file.write_text(json.dumps(package, indent=2) + "\n")

    run(["pnpm", "install"], frontend)
    installed = package.get("devDependencies", {}) | package.get("dependencies", {})
    if removable := [p for p in cfg["remove"] if p in installed]:
        run(["pnpm", "remove", *removable], frontend)
    run(["pnpm", "add", "--save-dev", *cfg["add_dev"]], frontend)
    # Pin exact versions (an existing caret range is not rewritten by `pnpm add -E`).
    package = json.loads(package_file.read_text())
    for name in cfg["exact"]:
        version = json.loads((frontend / "node_modules" / name / "package.json").read_text())["version"]
        for section in ("dependencies", "devDependencies"):
            if name in package.get(section, {}):
                package[section][name] = version
    package_file.write_text(json.dumps(package, indent=2) + "\n")
    run(["pnpm", "install"], frontend)
    manifest = frontend / "node_modules" / "@playwright" / "test" / "package.json"
    return json.loads(manifest.read_text())["version"]


# owner/repo[/subpath]@vX[.Y.Z]; the tag is looked up in owner/repo.
USES = re.compile(r"uses: ([\w.-]+/[\w.-]+)((?:/[\w./-]+)?)@(v\d+(?:\.\d+)*)\s*$", re.M)


def latest_tag_sha(repo: str, ref: str) -> tuple[str, str] | None:
    """Newest release tag within `ref`'s major (minor for 0.x) and its commit SHA."""
    try:
        out = subprocess.run(
            ["git", "ls-remote", "--tags", f"https://github.com/{repo}"],
            text=True, capture_output=True, timeout=60,
        ).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    parts = ref.split(".")
    # 0.x releases break between minors, so stay on the given minor.
    series = ".".join(parts[:2]) if parts[0] == "v0" and len(parts) > 1 else parts[0]
    tags: dict[str, str] = {}
    for line in out.splitlines():
        sha, name = line.split("\t")
        tag = name.removeprefix("refs/tags/")
        peeled = tag.endswith("^{}")
        tag = tag.removesuffix("^{}")
        if re.fullmatch(rf"{re.escape(series)}(\.\d+)*", tag) and (peeled or tag not in tags):
            tags[tag] = sha  # peeled entry (the commit) wins over the tag object
    if not tags:
        return None
    best = max(tags, key=lambda t: [int(x) for x in t[1:].split(".")])
    return best, tags[best]


def pin_actions(target: Path) -> None:
    """Pin GitHub Actions to commit SHAs (version kept as a comment)."""
    for workflow in (target / ".github" / "workflows").glob("*.yml"):
        text = workflow.read_text()

        def pin(match: re.Match) -> str:
            repo, subpath, ref = match[1], match[2], match[3]
            resolved = latest_tag_sha(repo, ref)
            if resolved is None:
                log(f"could not resolve {repo}@{ref}; left unpinned")
                return match[0]
            tag, sha = resolved
            return f"uses: {repo}{subpath}@{sha} # {tag}"

        text = USES.sub(pin, text)
        for line in text.splitlines():
            if "uses:" in line and not re.search(r"@[0-9a-f]{40}\b", line):
                log(f"{workflow.name}: not pinned to a SHA: {line.strip()}")
        workflow.write_text(text)


def initial_migrations(target: Path) -> None:
    env = {
        "DJANGO_SETTINGS_MODULE": "backend.config.settings.test",
        "DJANGO_SECRET_KEY": "scaffold",
        "DATABASE_URL": "sqlite:////tmp/scaffold.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "INTERNAL_API_SECRET": "scaffold",
    }
    run(["uv", "run", "python", "backend/manage.py", "makemigrations", "users"], target, env)
    for cache in target.glob("backend/**/__pycache__"):
        shutil.rmtree(cache)


def secrets(target: Path, recipients: list[str]) -> None:
    local = target / ".envs/local"
    shutil.copy(local / "app.env.example", local / "app.env")
    if recipients:
        encrypted = run(
            ["sops", "--encrypt", "--input-type", "dotenv", "--output-type", "dotenv",
             str(local / "app.env")],
            target,
        )
        (local / "app.env.enc").write_text(encrypted + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--name", required=True, help="kebab-case project slug, e.g. atlas-portal")
    parser.add_argument("--title", help="human name, default: from --name")
    parser.add_argument("--app-host", default="app.example.com", help="production hostname")
    parser.add_argument("--no-realtime", action="store_true", help="omit the FastAPI service")
    parser.add_argument("--ci", choices=["github", "gitlab", "both", "none"], default="github")
    parser.add_argument(
        "--audience", choices=sorted(AUDIENCES), default="internal",
        help="who logs in: internal (company SSO), external (accounts + MFA), mixed (both)",
    )
    parser.add_argument("--age-recipient", action="append", default=[], help="age public key (repeatable)")
    parser.add_argument("--skip-install", action="store_true", help="do not resolve dependencies")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", args.name):
        raise SystemExit("--name must be kebab-case, e.g. atlas-portal")
    # The title and host land in Python, YAML, TOML, HTML and Vue files unescaped.
    if args.title and not re.fullmatch(r"[\w][\w .&+-]*", args.title):
        raise SystemExit("--title may contain letters, digits, spaces and . & + - only")
    if not re.fullmatch(r"(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", args.app_host):
        raise SystemExit("--app-host must be a lowercase hostname, e.g. app.example.com")
    target: Path = args.target.resolve()
    if target.exists() and not target.is_dir():
        raise SystemExit(f"{target} exists and is not a directory")
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"{target} exists and is not empty")
    tools = ["git"] + (["sops"] if args.age_recipient else [])
    if not args.skip_install:
        tools += ["uv", "pnpm"]
    for tool in tools:
        if shutil.which(tool) is None:
            raise SystemExit(f"{tool} not found on PATH")

    features = set(AUDIENCES[args.audience]) | (set() if args.no_realtime else {"realtime"})
    runtimes = STACK["runtimes"]
    recipients = ",".join(args.age_recipient) or "age1REPLACE_WITH_RECIPIENT_PUBLIC_KEYS"
    values = {
        "__PROJECT_SNAKE__": args.name.replace("-", "_"),
        "__PROJECT_TITLE__": args.title or args.name.replace("-", " ").title(),
        "__PROJECT_KEY_PREFIX__": key_prefix(args.name),
        "__PROJECT__": args.name,
        "__APP_HOST__": args.app_host,
        "__PYTHON_VERSION__": runtimes["python"],
        "__NODE_VERSION__": runtimes["node"],
        "__POSTGRES_VERSION__": runtimes["postgres"],
        "__REDIS_VERSION__": runtimes["redis"],
        "__DEBIAN_SUITE__": runtimes["debian"],
        "__CADDY_VERSION__": runtimes["caddy"],
        "__MAILPIT_VERSION__": runtimes["mailpit"],
        "__DOCKER_VERSION__": runtimes["docker"],
        "__UV_VERSION__": tool_version(["uv", "--version"]) if shutil.which("uv") else "latest",
        "__PNPM_VERSION__": tool_version(["pnpm", "--version"]) if shutil.which("pnpm") else "10.0.0",
        "__REALTIME_ENABLED__": "" if args.no_realtime else "true",
        "__AUTH_AUDIENCE__": args.audience,
        "__AGE_RECIPIENTS_PRODUCTION__": recipients,
        "__AGE_RECIPIENTS_STAGING__": recipients,
        "__AGE_RECIPIENTS_LOCAL__": recipients,
    }

    log(f"copying template to {target}")
    copy_template(target, args.ci, features)
    render(target, values, features)
    assert_rendered(target, allow=LATE_PLACEHOLDERS)
    secrets(target, args.age_recipient)
    run(["git", "init", "-q", "-b", "main"], target)

    if args.skip_install:
        render(target, {"__PLAYWRIGHT_VERSION__": "REPLACE_WITH_PLAYWRIGHT_VERSION",
                        "__PLAYWRIGHT_MCP_VERSION__": "REPLACE_WITH_VERSION"}, None)
        log("skipped dependency resolution. The repo is NOT runnable yet: frontend/ lacks the "
            "create-vue tooling (package.json, tsconfig, eslint.config.base.ts). Prefer a full run; "
            "otherwise follow create_frontend() and install_python() in this script by hand.")
    else:
        install_python(target, features)
        playwright = create_frontend(target, args.name, values["__PNPM_VERSION__"])
        mcp = run(["pnpm", "view", "@playwright/mcp", "version"], target)  # pinned, never @latest
        render(target, {"__PLAYWRIGHT_VERSION__": playwright, "__PLAYWRIGHT_MCP_VERSION__": mcp}, None)
        initial_migrations(target)
        run(["uvx", "pre-commit", "autoupdate"], target)
        if (target / ".github" / "workflows").exists():
            log("pinning GitHub Actions to commit SHAs")
            pin_actions(target)
        # Canonical formatting with the new project's own Ruff config.
        run(["uv", "run", "ruff", "check", "--fix", "--quiet", "."], target)
        run(["uv", "run", "ruff", "format", "--quiet", "."], target)
    assert_rendered(target, allow=set())

    log("done. Next: cd into the repo, `task setup`, `task dev:up`, then `task ci`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Keep CI files thin and the CI platforms interchangeable.

1. Every command in .gitlab-ci.yml and .github/workflows/*.yml is a `task ...`
   call or a known setup step (installing tools, registry login, env example).
   Logic belongs in Taskfile.yml and scripts/, where developers can run it.
2. If both platforms are configured, both call the same Task targets.
3. Tools are installed from scripts/ci/tools.txt (pinned, SHA-256 checked,
   mirrored), not by setup actions that download from a release page: one
   place per tool, so the smoke test and the deploy cannot drift apart, and an
   outage of the original source does not stop every job.

Run by pre-commit; exits non-zero with the offending lines.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SETUP = [
    r"task( |$)",
    r"scripts/ci/",
    r"(apk add|apt-get) ",
    r"cp \.envs/local/app\.env\.example \.envs/local/app\.env$",
    r'echo "\$CI_REGISTRY_PASSWORD" \| docker login ',
    r"docker buildx create ",
]
COMMAND_KEYS = {"script", "before_script", "after_script", "run"}


class Loader(yaml.SafeLoader):
    """Safe loader that tolerates GitLab tags such as !reference."""


Loader.add_multi_constructor("!", lambda loader, suffix, node: None)


def commands(node, key=None):
    """Yield every shell line under script/before_script/after_script/run keys."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from commands(v, k)
    elif isinstance(node, list):
        for item in node:
            yield from commands(item, key)
    elif isinstance(node, str) and key in COMMAND_KEYS:
        text = re.sub(r"\\\n\s*", " ", node)
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                yield line


def check(files: list[Path]) -> tuple[list[str], set[str]]:
    errors, targets = [], set()
    for path in files:
        data = yaml.load(path.read_text(), Loader=Loader) or {}  # noqa: S506 (Loader is a SafeLoader)
        for line in commands(data):
            if not any(re.match(pattern, line) for pattern in SETUP):
                errors.append(
                    f"{path.relative_to(ROOT)}: logic in CI, move it to a Task target: {line}"
                )
            elif match := re.match(r"task ([\w:-]+)", line):
                targets.add(match[1])
    return errors, targets


# Setup actions that download a tool from its release page at run time.
DOWNLOADING_ACTIONS = ("go-task/setup-task", "docker/setup-compose-action")


def unpinned_tools(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        data = yaml.load(path.read_text(), Loader=Loader) or {}  # noqa: S506 (Loader is a SafeLoader)
        for job in (data.get("jobs") or {}).values():
            for step in (job or {}).get("steps") or []:
                uses = str(step.get("uses", ""))
                if uses.startswith(DOWNLOADING_ACTIONS):
                    errors.append(
                        f"{path.relative_to(ROOT)}: {uses.split('@')[0]} downloads at run time; "
                        "pin the tool in scripts/ci/tools.txt and use scripts/ci/install-tools.sh"
                    )
    return errors


def main() -> int:
    gitlab = [p for p in [ROOT / ".gitlab-ci.yml"] if p.exists()]
    github = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
    errors, gitlab_targets = check(gitlab)
    more, github_targets = check(github)
    errors += more
    if gitlab and github and gitlab_targets != github_targets:
        errors.append(
            "GitLab and GitHub call different Task targets: "
            f"only GitLab {sorted(gitlab_targets - github_targets)}, "
            f"only GitHub {sorted(github_targets - gitlab_targets)}"
        )
    errors += unpinned_tools(github)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

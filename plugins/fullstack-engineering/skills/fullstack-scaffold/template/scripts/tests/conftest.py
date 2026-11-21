import os
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent


def run(args, cwd, env=None, check=True):
    result = subprocess.run(
        args, cwd=cwd, env={**os.environ, **(env or {})}, text=True, capture_output=True
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"{args} failed ({result.returncode}):\n{result.stdout}{result.stderr}"
        )
    return result


@pytest.fixture
def git_repo(tmp_path):
    """An empty repo with a committer; no origin, so tag fetches are no-ops."""
    run(["git", "init", "-q", "-b", "main"], tmp_path)
    run(["git", "config", "user.email", "ci@example.com"], tmp_path)
    run(["git", "config", "user.name", "ci"], tmp_path)
    return tmp_path

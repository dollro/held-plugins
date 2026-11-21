"""scripts/ci/tested_images.sh against a stub registry (a directory per repository)."""

import pytest
from conftest import SCRIPTS, run

TESTED = str(SCRIPTS / "ci" / "tested_images.sh")
DJANGO, TEST, REALTIME = ("sha256:" + c * 64 for c in "abc")
STUB = r"""#!/bin/sh
db="$(dirname "$0")/db"
key() { echo "$1" | tr '/' '_'; }
resolve() {
  case "$1" in
    *@*) echo "${1#*@}" ;;
    *) cat "$db/$(key "${1%:*}")/${1##*:}" 2>/dev/null || { echo "not found: $1" >&2; exit 1; } ;;
  esac
}
case "$1 $2" in
  "tag ls") ls "$db/$(key "$3")" 2>/dev/null ;;
  "image digest") resolve "$3" ;;
  "image copy") d="$(resolve "$3")" || exit 1; mkdir -p "$db/$(key "${4%:*}")"
                echo "$d" > "$db/$(key "${4%:*}")/${4##*:}" ;;
esac
"""


@pytest.fixture
def registry(tmp_path):
    stub = tmp_path / "regctl"
    stub.write_text(STUB)
    stub.chmod(0o755)
    (tmp_path / "db").mkdir()
    env = {
        "REGCTL": str(stub),
        "IMAGE_BASE": "reg/acme/atlas",
        "COMMIT": "abc123",
        "AWAIT_INTERVAL": "1",
    }

    def call(*args, check=True, **extra):
        return run(["sh", TESTED, *args], tmp_path, {**env, **extra}, check=check)

    return tmp_path, call


def recorded(tmp_path, call):
    (tmp_path / "meta.json").write_text(
        "{\n"
        f'  "django": {{\n    "containerimage.digest": "{DJANGO}"\n  }},\n'
        f'  "django-test": {{\n    "containerimage.digest": "{TEST}"\n  }},\n'
        f'  "realtime": {{\n    "containerimage.digest": "{REALTIME}"\n  }}\n'
        "}\n"
    )
    call("record", "meta.json", "images.env")
    return dict(
        line.split("=", 1) for line in (tmp_path / "images.env").read_text().split()
    )


def test_an_untested_commit_is_built(registry):
    _, call = registry
    assert call("reuse", "out.env", check=False).returncode == 3


def test_mark_refuses_digests_a_test_job_did_not_run(registry):
    tmp_path, call = registry
    digests = recorded(tmp_path, call)
    call("ran", "ran-backend.env", **digests)
    (tmp_path / "ran-e2e.env").write_text("DIGEST_DJANGO=" + REALTIME + "\n")

    result = call("mark", "ran-backend.env", "ran-e2e.env", check=False, **digests)

    assert result.returncode != 0 and "other digests" in result.stderr


def test_marked_digests_are_reused_awaited_and_promoted(registry):
    tmp_path, call = registry
    digests = recorded(tmp_path, call)
    for ran in ("ran-backend.env", "ran-e2e.env"):
        call("ran", ran, **digests)
    call("mark", "ran-backend.env", "ran-e2e.env", **digests)

    assert call("reuse", "out.env").returncode == 0
    assert f"DIGEST_DJANGO_TEST={TEST}" in (tmp_path / "out.env").read_text()
    call("await", "1", "tested.env")
    assert (tmp_path / "tested.env").read_text().strip() == "TESTED=true"
    call("promote", "1.8")
    assert (
        tmp_path / "db" / "reg_acme_atlas-django" / "1.8"
    ).read_text().strip() == DJANGO


def test_await_reports_an_untested_commit_after_the_timeout(registry):
    tmp_path, call = registry
    (tmp_path / "db" / "reg_acme_atlas-django").mkdir()
    call("await", "1", "tested.env")
    assert (tmp_path / "tested.env").read_text().strip() == "TESTED=false"


def test_check_image_refuses_a_tag(registry):
    _, call = registry
    assert call("check-image", "reg/x@" + TEST, TEST).returncode == 0
    assert call("check-image", "reg/x:latest", TEST, check=False).returncode != 0

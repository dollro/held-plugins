"""scripts/release.sh: tag shape, validation and release preparation."""

import pytest
from conftest import SCRIPTS, run

RELEASE = str(SCRIPTS / "release.sh")


def commit(repo, message="change"):
    run(["git", "commit", "-q", "--allow-empty", "-m", message], repo)
    return run(["git", "rev-parse", "HEAD"], repo).stdout.strip()


@pytest.mark.parametrize(
    ("version", "kind"),
    [
        ("1.8", "release"),
        ("1.8.1", "release"),
        ("1.8a1", "prerelease"),
        ("1.8-rc1", "prerelease"),
    ],
)
def test_shape_accepts_releases_and_prereleases(git_repo, version, kind):
    assert run(["bash", RELEASE, "shape", version], git_repo).stdout.strip() == kind


@pytest.mark.parametrize("version", ["v1.8.0", "1.08", "latest", ""])
def test_shape_refuses_anything_else(git_repo, version):
    assert (
        run(["bash", RELEASE, "shape", version], git_repo, check=False).returncode != 0
    )


def test_prepare_writes_notes_for_a_newer_version(git_repo):
    commit(git_repo, "first")
    run(["git", "tag", "-a", "1.7", "-m", "r"], git_repo)
    head = commit(git_repo, "second")

    out = run(["bash", RELEASE, "prepare", "1.8", head], git_repo).stdout

    assert "ready to tag" in out
    assert "- second" in (git_repo / "release-notes.md").read_text()


@pytest.mark.parametrize("version", ["1.6", "1.7"])
def test_prepare_refuses_an_older_or_taken_version(git_repo, version):
    commit(git_repo)
    run(["git", "tag", "-a", "1.7", "-m", "r"], git_repo)
    head = commit(git_repo)
    assert (
        run(
            ["bash", RELEASE, "prepare", version, head], git_repo, check=False
        ).returncode
        != 0
    )


def test_prepare_refuses_a_commit_without_the_newest_release(git_repo):
    """The job stays playable in old pipelines; releasing such a commit rolls back."""
    base = commit(git_repo, "base")
    commit(git_repo, "released")
    run(["git", "tag", "-a", "1.8", "-m", "r"], git_repo)
    run(["git", "checkout", "-q", "-b", "old", base], git_repo)
    old = commit(git_repo, "old branch")

    result = run(["bash", RELEASE, "prepare", "1.9", old], git_repo, check=False)

    assert result.returncode != 0 and "does not contain release 1.8" in result.stderr


def test_validate_refuses_a_lightweight_tag(git_repo):
    commit(git_repo)
    run(["git", "tag", "1.8"], git_repo)
    result = run(["bash", RELEASE, "validate", "1.8"], git_repo, check=False)
    assert result.returncode != 0 and "lightweight" in result.stderr


def test_validate_takes_a_prerelease_only_when_allowed(git_repo):
    commit(git_repo)
    run(["git", "tag", "-a", "1.8a1", "-m", "p"], git_repo)
    assert (
        run(["bash", RELEASE, "validate", "1.8a1"], git_repo, check=False).returncode
        != 0
    )
    run(["bash", RELEASE, "validate", "1.8a1"], git_repo, env={"ALLOW_PRERELEASE": "1"})

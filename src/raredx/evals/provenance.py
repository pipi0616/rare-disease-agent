"""What produced a result: the code version a run records."""

import subprocess

RESULT_PATHS = ("src", "evals", "pyproject.toml", "uv.lock")


def code_version() -> str:
    """The last commit that changed anything a result depends on, as a short hash,
    with -dirty when such files are uncommitted.

    Only code, manifests and dependencies count: a notebook saved with its outputs,
    or a commit that only adds documentation, does not change what a run computes —
    so runs made before and after such a commit record the same version.
    """
    try:
        commit = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", *RESULT_PATHS],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", *RESULT_PATHS],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return (commit or "unknown") + ("-dirty" if dirty else "")

"""What produced a result: the code version a run records."""

import subprocess

RESULT_PATHS = ("src", "evals", "pyproject.toml", "uv.lock")


def code_version() -> str:
    """Short commit hash, with -dirty when files that affect results are uncommitted.

    Only code, manifests and dependencies count: a notebook saved with its
    outputs does not change what a run computes.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", *RESULT_PATHS],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return commit + ("-dirty" if dirty else "")

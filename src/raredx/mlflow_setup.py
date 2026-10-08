"""Process-wide MLflow settings, applied before mlflow is first imported.

Code imports mlflow from here (`from raredx.mlflow_setup import mlflow`), so
these defaults hold however a run starts. Each can still be overridden from the
environment.

Three of them work around problems found while building the evaluation; all
three show up only under evaluate()'s parallel threads:

- Telemetry is off. MLflow otherwise reports usage to its servers — nothing
  here should leave the machine — and its per-call bookkeeping imports modules
  lazily from every scorer thread at once, which deadlocked CPython 3.12's
  import locks during a 200-case model run.
- litellm is marked absent. evaluate() checks `import litellm` from every
  thread; it is not installed, and concurrent failed imports of one missing
  module deadlock the same import locks (seen from about 40 cases).
- The SQLite connection pool is larger. About 20 threads write traces and
  scores at once; with SQLAlchemy's default pool (5 + 10) some writes time out
  and MLflow drops those records with only a warning.
"""

import importlib.util
import os
import sys

os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # a setup hint printed on import
# evaluate() otherwise asks the system about the first case twice, to check it traces;
# the harness traces its predict function explicitly, so the check is not needed.
os.environ.setdefault("MLFLOW_GENAI_EVAL_SKIP_TRACE_VALIDATION", "True")
os.environ.setdefault("MLFLOW_SQLALCHEMYSTORE_POOL_SIZE", "40")
os.environ.setdefault("MLFLOW_SQLALCHEMYSTORE_MAX_OVERFLOW", "40")
if importlib.util.find_spec("litellm") is None:
    sys.modules.setdefault("litellm", None)  # type: ignore[arg-type]

import mlflow  # noqa: E402

__all__ = ["mlflow"]

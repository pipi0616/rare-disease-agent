"""MLflow's settings must be in place before mlflow is imported, by any route.

Each check runs in a fresh interpreter: this test process imported mlflow long
ago, and set the settings in its own environment, so the child gets a copy of
the environment without them.
"""

import os
import subprocess
import sys

# In the child: stop mlflow from loading at all if the settings are not there yet —
# a regression then fails the test without MLflow ever starting its telemetry.
GUARD = """
import os, sys
class Guard:
    def find_spec(self, name, path=None, target=None):
        if name == "mlflow":
            if os.environ.get("MLFLOW_DISABLE_TELEMETRY") != "true":
                raise ImportError("mlflow was imported before raredx.mlflow_setup ran")
            sys.meta_path.remove(self)
        return None
sys.meta_path.insert(0, Guard())
"""


def fresh_python(code: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("MLFLOW_")}
    return subprocess.run(
        [sys.executable, "-c", GUARD + code], env=env, capture_output=True, text=True
    )


def test_importing_the_package_applies_the_settings_without_loading_mlflow() -> None:
    result = fresh_python("import raredx; print('mlflow' in sys.modules)")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


def test_a_module_that_imports_mlflow_first_finds_the_settings_in_place() -> None:
    # harness.py imports mlflow before any raredx module, in the usual import order.
    result = fresh_python("import raredx.evals.harness")
    assert result.returncode == 0, result.stderr

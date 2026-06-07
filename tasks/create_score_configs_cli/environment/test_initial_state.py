import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_langfuse_cli_available():
    assert shutil.which("langfuse") is not None, (
        "The `langfuse` CLI binary is not on PATH. The langfuse-cli npm package must be globally installed."
    )


def test_langfuse_cli_can_load_schema():
    # The CLI dynamically wraps the OpenAPI spec; this confirms the binary runs.
    result = subprocess.run(
        ["langfuse", "api", "__schema"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`langfuse api __schema` failed with exit code {result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_langfuse_env_vars_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        value = os.environ.get(var)
        assert value, f"Required environment variable {var} is not set in the task environment."


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for parallel-run safety."

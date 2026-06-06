import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_node_binary_available():
    assert shutil.which("node") is not None, (
        "node binary not found in PATH; Node.js runtime is required for the Langfuse JS/TS SDK."
    )


def test_npm_binary_available():
    assert shutil.which("npm") is not None, (
        "npm binary not found in PATH; npm is required to install the Langfuse JS/TS SDK packages."
    )


def test_langfuse_credentials_in_env():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        value = os.environ.get(var)
        assert value, f"Environment variable {var} must be set before the task runs."


def test_run_id_in_env():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "Environment variable ZEALT_RUN_ID must be set so the task can produce run-id-scoped identifiers."
    )


def test_log_file_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Log file {log_path} should not exist before the task runs; the executor must create it."
    )

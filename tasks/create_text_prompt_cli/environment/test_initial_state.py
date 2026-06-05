import os
import shutil

PROJECT_DIR = "/home/user/langfuse-task"


def test_node_available():
    assert shutil.which("node") is not None, (
        "Node.js binary not found in PATH; required to run the langfuse-cli via npx."
    )


def test_npm_available():
    assert shutil.which("npm") is not None, (
        "npm binary not found in PATH; required to install the langfuse-cli."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Expected {log_path} to NOT exist before the task starts; the executor must create it."
    )


def test_langfuse_env_vars_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        assert os.environ.get(var), (
            f"Expected environment variable {var} to be set for Langfuse authentication."
        )


def test_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "Expected environment variable ZEALT_RUN_ID to be set for parallel-run safety."


def test_requests_importable():
    import requests  # noqa: F401

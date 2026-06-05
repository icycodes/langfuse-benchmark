import os
import shutil


PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task starts."
    )


def test_node_available():
    assert shutil.which("node") is not None, (
        "Node.js binary 'node' must be available in PATH for running the Langfuse CLI."
    )


def test_npx_available():
    assert shutil.which("npx") is not None, (
        "'npx' must be available in PATH so the Langfuse CLI can be invoked via npx."
    )


def test_langfuse_public_key_env():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set so the CLI can authenticate."
    )


def test_langfuse_secret_key_env():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set so the CLI can authenticate."
    )


def test_langfuse_base_url_env():
    base_url = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST")
    assert base_url, (
        "LANGFUSE_BASE_URL (or LANGFUSE_HOST) environment variable must be set."
    )


def test_zealt_run_id_env():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for run-id isolation."
    # The skill defines run-id as matching zr-[a-z0-9]+
    assert run_id.startswith("zr-"), (
        f"ZEALT_RUN_ID must start with 'zr-' to be a valid run-id, got: {run_id!r}"
    )

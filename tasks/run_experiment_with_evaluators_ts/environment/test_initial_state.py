import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, (
        "node binary not found in PATH; a Node.js runtime is required to run the Langfuse TS/JS SDK."
    )


def test_npm_binary_available():
    assert shutil.which("npm") is not None, (
        "npm binary not found in PATH; npm is required to install the Langfuse JS/TS SDK packages."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist as the starting working directory."
    )


def test_langfuse_public_key_env_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set so the Langfuse JS/TS SDK can authenticate."
    )


def test_langfuse_secret_key_env_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set so the Langfuse JS/TS SDK can authenticate."
    )


def test_langfuse_base_url_env_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable must be set so the Langfuse JS/TS SDK targets the correct host."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set; the task uses it to build a unique experiment name."
    )

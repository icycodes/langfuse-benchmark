import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_node_available():
    assert shutil.which("node") is not None, (
        "Node.js binary 'node' was not found in PATH; the TypeScript task requires Node.js."
    )


def test_npm_available():
    assert shutil.which("npm") is not None, (
        "'npm' was not found in PATH; the TypeScript task requires npm to install Langfuse SDK packages."
    )


def test_langfuse_public_key_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "Environment variable LANGFUSE_PUBLIC_KEY must be set so the Langfuse SDK can authenticate."
    )


def test_langfuse_secret_key_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "Environment variable LANGFUSE_SECRET_KEY must be set so the Langfuse SDK can authenticate."
    )


def test_langfuse_base_url_set():
    base_url = os.environ.get("LANGFUSE_BASE_URL", "")
    assert base_url.startswith("http"), (
        "Environment variable LANGFUSE_BASE_URL must be set to a valid http(s) URL for the Langfuse API."
    )


def test_zealt_run_id_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "Environment variable ZEALT_RUN_ID must be set so the task can produce run-isolated resource names."

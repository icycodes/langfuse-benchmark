import importlib
import os

PROJECT_DIR = "/home/user/langfuse_task"


def test_langfuse_python_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as e:
        raise AssertionError(
            "The Langfuse Python SDK is not importable. "
            "Install it with `pip install langfuse` in the task environment."
        ) from e


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist. "
        "The Dockerfile should create this directory before the task begins."
    )


def test_langfuse_public_key_env_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable is not set in the task environment."
    )


def test_langfuse_secret_key_env_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable is not set in the task environment."
    )


def test_langfuse_base_url_env_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable is not set in the task environment."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set in the task environment."

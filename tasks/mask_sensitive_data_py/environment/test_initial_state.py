import importlib.util
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_langfuse_python_sdk_importable():
    spec = importlib.util.find_spec("langfuse")
    assert spec is not None, (
        "The 'langfuse' Python SDK is not importable. "
        "It must be pre-installed in the task environment."
    )


def test_requests_library_importable():
    spec = importlib.util.find_spec("requests")
    assert spec is not None, (
        "The 'requests' library must be available so the verifier can call the "
        "Langfuse public API."
    )


def test_langfuse_public_key_env_var_set():
    value = os.environ.get("LANGFUSE_PUBLIC_KEY")
    assert value, "LANGFUSE_PUBLIC_KEY environment variable is not set."


def test_langfuse_secret_key_env_var_set():
    value = os.environ.get("LANGFUSE_SECRET_KEY")
    assert value, "LANGFUSE_SECRET_KEY environment variable is not set."


def test_langfuse_base_url_env_var_set():
    value = os.environ.get("LANGFUSE_BASE_URL")
    assert value, "LANGFUSE_BASE_URL environment variable is not set."


def test_zealt_run_id_env_var_set():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "ZEALT_RUN_ID environment variable is not set."

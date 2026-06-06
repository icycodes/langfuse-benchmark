import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} is expected to exist before the task starts."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except Exception as exc:  # pragma: no cover - import failure path
        pytest.fail(f"Failed to import the langfuse Python SDK: {exc}")


def test_requests_library_importable():
    try:
        importlib.import_module("requests")
    except Exception as exc:  # pragma: no cover - import failure path
        pytest.fail(f"Failed to import the requests library used for API verification: {exc}")


def test_langfuse_public_key_env_var_set():
    value = os.environ.get("LANGFUSE_PUBLIC_KEY")
    assert value, "LANGFUSE_PUBLIC_KEY environment variable must be set."


def test_langfuse_secret_key_env_var_set():
    value = os.environ.get("LANGFUSE_SECRET_KEY")
    assert value, "LANGFUSE_SECRET_KEY environment variable must be set."


def test_langfuse_base_url_env_var_set():
    value = os.environ.get("LANGFUSE_BASE_URL")
    assert value, "LANGFUSE_BASE_URL environment variable must be set."


def test_zealt_run_id_env_var_set():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "ZEALT_RUN_ID environment variable must be set for parallel-run safety."

import importlib
import os

import pytest

PROJECT_DIR = "/home/user/langfuse_task"


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_requests_library_importable():
    try:
        importlib.import_module("requests")
    except ImportError as exc:
        pytest.fail(f"`requests` library is not importable: {exc}")


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_langfuse_public_key_env_var_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set in the initial environment."
    )


def test_langfuse_secret_key_env_var_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set in the initial environment."
    )


def test_langfuse_base_url_env_var_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable must be set in the initial environment."
    )


def test_zealt_run_id_env_var_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable must be set in the initial environment."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Expected {log_path} to NOT exist before the task is executed."
    )

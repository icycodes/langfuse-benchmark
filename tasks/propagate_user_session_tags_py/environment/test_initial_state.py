import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to already exist."
    )


def test_langfuse_python_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as e:
        pytest.fail(f"The 'langfuse' Python SDK must be installed in the environment: {e}")


def test_langfuse_public_key_env_is_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY must be set in the environment."
    )


def test_langfuse_secret_key_env_is_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY must be set in the environment."
    )


def test_langfuse_base_url_env_is_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL must be set in the environment."
    )


def test_zealt_run_id_env_is_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID must be set in the environment for run-scoped resource isolation."


def test_output_log_does_not_exist_yet():
    # The executor is responsible for producing the log file.
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Expected {log_path} to NOT exist before the task is executed."
    )

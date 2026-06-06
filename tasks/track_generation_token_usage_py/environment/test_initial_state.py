import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - exercised only on failure
        pytest.fail(
            f"langfuse Python SDK is not installed or not importable: {exc}"
        )


def test_langfuse_public_key_env_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set in the task environment."
    )


def test_langfuse_secret_key_env_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set in the task environment."
    )


def test_langfuse_base_url_env_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable must be set in the task environment."
    )


def test_zealt_run_id_env_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable must be set for parallel-run isolation."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Output log {log_path} must not exist before the task runs; the executor is responsible for creating it."
    )

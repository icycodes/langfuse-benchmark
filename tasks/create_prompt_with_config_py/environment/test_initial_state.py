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
    except ImportError as exc:
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_requests_library_importable():
    try:
        importlib.import_module("requests")
    except ImportError as exc:
        pytest.fail(f"requests library is not importable: {exc}")


def test_langfuse_public_key_env_set():
    value = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    assert value.strip() != "", "LANGFUSE_PUBLIC_KEY environment variable is not set."


def test_langfuse_secret_key_env_set():
    value = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert value.strip() != "", "LANGFUSE_SECRET_KEY environment variable is not set."


def test_langfuse_base_url_env_set():
    value = os.environ.get("LANGFUSE_BASE_URL", "")
    assert value.strip() != "", "LANGFUSE_BASE_URL environment variable is not set."


def test_zealt_run_id_env_set():
    value = os.environ.get("ZEALT_RUN_ID", "")
    assert value.strip() != "", "ZEALT_RUN_ID environment variable is not set."


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Expected {log_path} to NOT exist before the task runs."
    )

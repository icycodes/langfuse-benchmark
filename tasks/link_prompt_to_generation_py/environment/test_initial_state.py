import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} should exist before the task starts."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - executed only on failure
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_langfuse_credentials_env_vars_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        value = os.environ.get(var)
        assert value, f"Environment variable {var} must be set in the task environment."


def test_zealt_run_id_env_var_present():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "Environment variable ZEALT_RUN_ID must be set in the task environment."


def test_output_log_not_created_yet():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"{log_path} should not exist before the task is executed."
    )

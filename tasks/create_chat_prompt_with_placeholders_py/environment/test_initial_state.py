import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - we want the clear message
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_langfuse_credentials_available():
    for env_var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        assert os.environ.get(env_var), (
            f"Required environment variable {env_var} is not set in the initial environment."
        )


def test_run_id_available():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable must be set in the initial environment."
    )

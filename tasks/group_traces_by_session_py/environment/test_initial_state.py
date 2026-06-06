import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "chat_session.py")
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")


def test_langfuse_sdk_importable():
    """The Langfuse Python SDK must be importable in the environment."""
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - explicit failure message
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_project_dir_exists():
    """The project directory referenced by the task must exist."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_script_not_yet_created():
    """The executor is responsible for creating chat_session.py; it must not exist yet."""
    assert not os.path.exists(SCRIPT_PATH), (
        f"Expected {SCRIPT_PATH} to NOT exist before the task starts (the executor must create it)."
    )


def test_log_file_not_yet_created():
    """The executor is responsible for writing output.log; it must not exist yet."""
    assert not os.path.exists(LOG_PATH), (
        f"Expected {LOG_PATH} to NOT exist before the task starts (the executor must create it)."
    )


def test_langfuse_credentials_present():
    """Langfuse credentials must be present in the environment for the executor."""
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"):
        assert os.environ.get(var), (
            f"Expected environment variable {var} to be set before the task starts."
        )


def test_run_id_present():
    """ZEALT_RUN_ID must be available so the executor can scope resource names."""
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "Expected ZEALT_RUN_ID to be set in the environment."

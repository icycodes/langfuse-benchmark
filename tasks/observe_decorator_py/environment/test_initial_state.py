import os
import importlib

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - diagnostic only
        pytest.fail(f"langfuse Python SDK is not importable: {exc}")


def test_langfuse_credentials_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        assert os.environ.get(var), f"Environment variable {var} is not set."


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."


def test_pipeline_script_not_yet_created():
    # The agent is expected to CREATE this file. It must not exist beforehand.
    script_path = os.path.join(PROJECT_DIR, "run_pipeline.py")
    assert not os.path.exists(script_path), (
        f"{script_path} should not exist before the task starts."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"{log_path} should not exist before the task starts."
    )

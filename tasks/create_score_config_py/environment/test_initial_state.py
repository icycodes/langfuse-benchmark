import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:
        pytest.fail(
            "Langfuse Python SDK is not importable in the task environment: "
            f"{exc!r}"
        )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_langfuse_public_key_env_present():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set."
    )


def test_langfuse_secret_key_env_present():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set."
    )


def test_langfuse_base_url_env_present():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable must be set."
    )


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set."

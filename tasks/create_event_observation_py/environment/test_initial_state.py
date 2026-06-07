import importlib.util
import os

import pytest


PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_langfuse_sdk_importable():
    spec = importlib.util.find_spec("langfuse")
    assert spec is not None, (
        "Expected the `langfuse` Python SDK to be installed in the environment "
        "(import langfuse should succeed)."
    )


def test_requests_library_available():
    # The verifier uses HTTP calls to the Langfuse Public API for validation.
    spec = importlib.util.find_spec("requests")
    assert spec is not None, (
        "Expected the `requests` Python package to be available for the "
        "verifier to call the Langfuse Public API."
    )


def test_langfuse_credentials_env_vars_set():
    for key in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        value = os.environ.get(key)
        assert value, (
            f"Expected environment variable {key} to be set so the Langfuse "
            "Python SDK and the verifier can authenticate against Langfuse Cloud."
        )


def test_zealt_run_id_env_var_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "Expected environment variable ZEALT_RUN_ID to be set; the task uses "
        "it as a suffix on Langfuse resource names to keep concurrent runs isolated."
    )


def test_output_log_not_yet_created():
    # The executor is expected to create this log file; it must not pre-exist.
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Expected {log_path} to not exist before the task runs; the executor "
        "must create it."
    )


def test_main_script_not_yet_created():
    script_path = os.path.join(PROJECT_DIR, "main.py")
    assert not os.path.exists(script_path), (
        f"Expected {script_path} to not exist before the task runs; the executor "
        "must create it."
    )

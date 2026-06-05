import os
import shutil

import pytest


PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, (
        "node binary is not available in PATH; required to run the TypeScript script."
    )


def test_npm_binary_available():
    assert shutil.which("npm") is not None, (
        "npm binary is not available in PATH; required to install dependencies and run scripts."
    )


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


def test_package_json_not_yet_created():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert not os.path.exists(pkg_path), (
        f"Expected {pkg_path} to NOT exist before the task is executed."
    )

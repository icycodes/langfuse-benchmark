import importlib
import os


PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - explicit failure message
        raise AssertionError(
            "The Langfuse Python SDK ('langfuse') must be installed in the environment "
            f"before the task starts, but importing it failed with: {exc}"
        )


def test_langfuse_public_key_env_var_present():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "Environment variable LANGFUSE_PUBLIC_KEY must be set before the task starts."
    )


def test_langfuse_secret_key_env_var_present():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "Environment variable LANGFUSE_SECRET_KEY must be set before the task starts."
    )


def test_langfuse_base_url_env_var_present():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "Environment variable LANGFUSE_BASE_URL must be set before the task starts."
    )


def test_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "Environment variable ZEALT_RUN_ID must be set before the task starts so the "
        "dataset name can be made unique per concurrent run."
    )


def test_output_log_not_present_yet():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Log file {log_path} must NOT exist before the task is executed; "
        "the executor is responsible for creating it."
    )


def test_seed_script_not_present_yet():
    script_path = os.path.join(PROJECT_DIR, "seed_dataset.py")
    assert not os.path.exists(script_path), (
        f"Script {script_path} must NOT exist before the task is executed; "
        "the executor is responsible for creating it."
    )

import os
import re
import shutil
import subprocess


PROJECT_DIR = "/home/user/langfuse-task"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_node_and_npx_available():
    assert shutil.which("node") is not None, (
        "node binary not found in PATH; required to run langfuse-cli via npx."
    )
    assert shutil.which("npx") is not None, (
        "npx binary not found in PATH; required to invoke langfuse-cli."
    )


def test_langfuse_cli_invokable():
    # The CLI should at minimum print its help text without requiring credentials.
    result = subprocess.run(
        ["npx", "--yes", "langfuse-cli", "--help"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        "langfuse-cli is not invokable via 'npx langfuse-cli --help'. "
        f"stderr: {result.stderr!r}"
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert "langfuse" in combined.lower(), (
        "langfuse-cli help output did not mention 'langfuse'."
    )


def test_langfuse_env_vars_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        assert os.environ.get(var), (
            f"Environment variable {var} is required but is not set in the task environment."
        )


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert re.fullmatch(r"zr-[a-z0-9]+", run_id), (
        f"ZEALT_RUN_ID must match the pattern 'zr-[a-z0-9]+'. Got: {run_id!r}"
    )


def test_output_log_does_not_exist_yet():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"{log_path} should not exist before the executor runs the task."
    )

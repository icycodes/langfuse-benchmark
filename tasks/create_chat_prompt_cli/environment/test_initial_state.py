import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH (required to run langfuse-cli)."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH (required to invoke langfuse-cli)."


def test_langfuse_cli_available():
    # The CLI may be installed globally as `langfuse` or be invocable via `npx langfuse-cli`.
    langfuse_bin = shutil.which("langfuse")
    if langfuse_bin is not None:
        return
    # Fall back to verifying that the package is resolvable through npx.
    result = subprocess.run(
        ["npx", "--no-install", "langfuse-cli", "--version"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        "langfuse-cli is not available. Expected either a global `langfuse` binary "
        f"or a resolvable `langfuse-cli` package. stderr: {result.stderr}"
    )


def test_langfuse_env_vars_present():
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        assert os.environ.get(var), f"Required environment variable {var} is not set."


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    assert run_id.startswith("zr-"), (
        f"ZEALT_RUN_ID has unexpected format: {run_id!r}. Expected to start with 'zr-'."
    )

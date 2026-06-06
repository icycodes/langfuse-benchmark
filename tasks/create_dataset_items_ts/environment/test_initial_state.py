import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_binary_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_project_package_json_exists():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json), (
        f"package.json not found at {package_json}."
    )


def test_langfuse_client_installed():
    package_dir = os.path.join(
        PROJECT_DIR, "node_modules", "@langfuse", "client"
    )
    assert os.path.isdir(package_dir), (
        f"@langfuse/client is not installed under {package_dir}."
    )


def test_langfuse_client_loadable_from_project():
    result = subprocess.run(
        [
            "node",
            "-e",
            "const m = require('@langfuse/client'); "
            "if (!m.LangfuseClient) { process.exit(2); } process.exit(0);",
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Failed to require('@langfuse/client') and access LangfuseClient from "
        f"the project directory. stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_langfuse_public_key_env_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable is not set."
    )


def test_langfuse_secret_key_env_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable is not set."
    )


def test_langfuse_base_url_env_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable is not set."
    )


def test_zealt_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    # Sanity-check the documented run-id format zr-[a-z0-9]+
    import re

    assert re.fullmatch(r"zr-[a-z0-9]+", run_id), (
        f"ZEALT_RUN_ID={run_id!r} does not match expected pattern zr-[a-z0-9]+."
    )

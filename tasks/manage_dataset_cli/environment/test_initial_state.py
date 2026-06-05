import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_node_available():
    assert shutil.which("node") is not None, (
        "Node.js (`node`) binary not found in PATH; it is required to run langfuse-cli."
    )


def test_npm_available():
    assert shutil.which("npm") is not None, (
        "`npm` binary not found in PATH; it is required to install langfuse-cli."
    )


def test_npx_available():
    assert shutil.which("npx") is not None, (
        "`npx` binary not found in PATH; it is required to invoke langfuse-cli one-off."
    )


def test_langfuse_public_key_env_set():
    value = os.environ.get("LANGFUSE_PUBLIC_KEY")
    assert value, "Environment variable LANGFUSE_PUBLIC_KEY must be set for the CLI to authenticate."


def test_langfuse_secret_key_env_set():
    value = os.environ.get("LANGFUSE_SECRET_KEY")
    assert value, "Environment variable LANGFUSE_SECRET_KEY must be set for the CLI to authenticate."


def test_langfuse_base_url_env_set():
    value = os.environ.get("LANGFUSE_BASE_URL")
    assert value, "Environment variable LANGFUSE_BASE_URL must be set to point the CLI at the Langfuse host."


def test_zealt_run_id_env_set():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "Environment variable ZEALT_RUN_ID must be set; the task uses it to namespace the dataset name."


def test_output_log_not_yet_created():
    output_log = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(output_log), (
        f"{output_log} should not exist before the executor runs the task."
    )

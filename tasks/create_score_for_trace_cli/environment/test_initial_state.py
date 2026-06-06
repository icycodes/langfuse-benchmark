import os
import re
import shutil

PROJECT_DIR = "/home/user/task"
TRACE_ID_FILE = "/home/user/task/trace_id.txt"


def test_langfuse_cli_available():
    assert shutil.which("langfuse") is not None, (
        "langfuse CLI binary not found in PATH. The Langfuse CLI must be installed "
        "and the `langfuse` command must be available."
    )


def test_jq_available():
    assert shutil.which("jq") is not None, (
        "jq is expected to be available for parsing JSON output from the Langfuse CLI."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_trace_id_file_exists():
    assert os.path.isfile(TRACE_ID_FILE), (
        f"Trace ID file {TRACE_ID_FILE} does not exist. The initial state must contain "
        "the pre-created Langfuse trace ID at this path."
    )


def test_trace_id_file_has_valid_id():
    with open(TRACE_ID_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content, f"Trace ID file {TRACE_ID_FILE} is empty."
    assert re.fullmatch(r"[0-9a-fA-F]{32}", content), (
        f"Trace ID file {TRACE_ID_FILE} does not contain a 32-character hex OTel trace "
        f"ID. Got: {content!r}."
    )


def test_langfuse_public_key_env_var_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "LANGFUSE_PUBLIC_KEY environment variable must be set for the Langfuse CLI."
    )


def test_langfuse_secret_key_env_var_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "LANGFUSE_SECRET_KEY environment variable must be set for the Langfuse CLI."
    )


def test_langfuse_base_url_env_var_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "LANGFUSE_BASE_URL environment variable must be set for the Langfuse CLI."
    )

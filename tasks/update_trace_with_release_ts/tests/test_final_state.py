import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

TRACE_ID_PATTERN = re.compile(r"^Trace ID:\s*([0-9a-f]{32})\s*$", re.MULTILINE)


def _get_run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is required for verification."
    return run_id


def _get_credentials() -> tuple[str, str, str]:
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    assert pk and sk, (
        "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables must be set for verification."
    )
    return pk, sk, base_url


def _extract_trace_id_from_log() -> str:
    assert os.path.isfile(LOG_PATH), (
        f"Expected log file {LOG_PATH} to exist after the task completes."
    )
    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()
    match = TRACE_ID_PATTERN.search(content)
    assert match, (
        f"Expected a line matching 'Trace ID: <32-hex-character trace id>' in {LOG_PATH}, "
        f"but got:\n{content}"
    )
    return match.group(1)


def _fetch_trace(trace_id: str) -> dict:
    pk, sk, base_url = _get_credentials()
    url = f"{base_url}/api/public/traces/{trace_id}"

    last_status = None
    last_body = None
    deadline = time.time() + 60.0
    while time.time() < deadline:
        resp = requests.get(url, auth=(pk, sk), timeout=15)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            return resp.json()
        time.sleep(5)

    pytest.fail(
        f"Timed out waiting for trace {trace_id} to be retrievable from Langfuse "
        f"({url}). Last status: {last_status}. Last body: {last_body}"
    )


def _is_non_empty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    return True


@pytest.fixture(scope="module")
def trace_payload() -> dict:
    trace_id = _extract_trace_id_from_log()
    return _fetch_trace(trace_id)


def test_log_file_contains_valid_trace_id():
    _extract_trace_id_from_log()


def test_trace_id_matches_log(trace_payload):
    logged_trace_id = _extract_trace_id_from_log()
    assert trace_payload.get("id") == logged_trace_id, (
        f"Trace ID returned by Langfuse API ({trace_payload.get('id')!r}) does not match "
        f"the trace ID written to the log ({logged_trace_id!r})."
    )


def test_trace_name_is_run_id_scoped(trace_payload):
    run_id = _get_run_id()
    expected_name = f"release-test-{run_id}"
    assert trace_payload.get("name") == expected_name, (
        f"Expected trace name {expected_name!r}, got {trace_payload.get('name')!r}."
    )


def test_trace_session_id(trace_payload):
    run_id = _get_run_id()
    expected_session = f"session-{run_id}"
    assert trace_payload.get("sessionId") == expected_session, (
        f"Expected sessionId {expected_session!r}, got {trace_payload.get('sessionId')!r}."
    )


def test_trace_user_id(trace_payload):
    run_id = _get_run_id()
    expected_user = f"user-{run_id}"
    assert trace_payload.get("userId") == expected_user, (
        f"Expected userId {expected_user!r}, got {trace_payload.get('userId')!r}."
    )


def test_trace_tags_include_staging_and_run_tag(trace_payload):
    run_id = _get_run_id()
    expected_run_tag = f"run-{run_id}"
    tags = trace_payload.get("tags")
    assert isinstance(tags, list), (
        f"Expected trace 'tags' to be a list, got {type(tags).__name__}: {tags!r}."
    )
    assert "staging" in tags, (
        f"Expected trace tags to include 'staging', got {tags!r}."
    )
    assert expected_run_tag in tags, (
        f"Expected trace tags to include {expected_run_tag!r}, got {tags!r}."
    )


def test_trace_release(trace_payload):
    assert trace_payload.get("release") == "v1.2.3", (
        f"Expected release 'v1.2.3', got {trace_payload.get('release')!r}."
    )


def test_trace_version(trace_payload):
    assert trace_payload.get("version") == "v1.0.0", (
        f"Expected version 'v1.0.0', got {trace_payload.get('version')!r}."
    )


def test_trace_public_flag(trace_payload):
    assert trace_payload.get("public") is True, (
        f"Expected trace public=true, got {trace_payload.get('public')!r}."
    )


def test_trace_input_non_empty(trace_payload):
    value = trace_payload.get("input")
    assert _is_non_empty(value), (
        f"Expected non-empty trace 'input', got {value!r}."
    )


def test_trace_output_non_empty(trace_payload):
    value = trace_payload.get("output")
    assert _is_non_empty(value), (
        f"Expected non-empty trace 'output', got {value!r}."
    )

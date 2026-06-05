import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

TRACE_ID_RE = re.compile(r"^Trace ID:\s*([A-Za-z0-9_\-]+)\s*$", re.MULTILINE)
TRACE_NAME_RE = re.compile(r"^Trace name:\s*(\S.*?)\s*$", re.MULTILINE)
USER_ID_RE = re.compile(r"^User ID:\s*(\S.*?)\s*$", re.MULTILINE)
SESSION_ID_RE = re.compile(r"^Session ID:\s*(\S.*?)\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"^Status:\s*OK\s*$", re.MULTILINE)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    assert value, (
        f"Required environment variable {name} is not set in the verifier env."
    )
    return value


@pytest.fixture(scope="session")
def langfuse_config():
    base_url = _required_env("LANGFUSE_BASE_URL").rstrip("/")
    public_key = _required_env("LANGFUSE_PUBLIC_KEY")
    secret_key = _required_env("LANGFUSE_SECRET_KEY")
    return {
        "base_url": base_url,
        "auth": (public_key, secret_key),
    }


@pytest.fixture(scope="session")
def run_id() -> str:
    return _required_env("ZEALT_RUN_ID")


@pytest.fixture(scope="session")
def expected_trace_name(run_id: str) -> str:
    return f"langchain-fact-{run_id}"


@pytest.fixture(scope="session")
def expected_user_id(run_id: str) -> str:
    return f"lc-user-{run_id}"


@pytest.fixture(scope="session")
def expected_session_id(run_id: str) -> str:
    return f"lc-session-{run_id}"


@pytest.fixture(scope="session")
def expected_run_tag(run_id: str) -> str:
    return f"run-{run_id}"


@pytest.fixture(scope="session")
def log_contents() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task script ran."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="session")
def trace_id_from_log(log_contents: str) -> str:
    match = TRACE_ID_RE.search(log_contents)
    assert match, (
        f"Expected {LOG_FILE} to contain a line in the form 'Trace ID: <trace_id>'. "
        f"Got contents: {log_contents!r}"
    )
    trace_id = match.group(1).strip()
    assert trace_id, "Captured trace_id from log file is empty."
    return trace_id


def test_log_file_has_trace_id(trace_id_from_log: str):
    assert trace_id_from_log, "Log file did not contain a non-empty Trace ID line."


def test_log_file_has_expected_trace_name(log_contents: str, expected_trace_name: str):
    match = TRACE_NAME_RE.search(log_contents)
    assert match, (
        f"Expected {LOG_FILE} to contain a line in the form 'Trace name: <name>'. "
        f"Got contents: {log_contents!r}"
    )
    assert match.group(1).strip() == expected_trace_name, (
        f"Trace name in log file does not match expected '{expected_trace_name}'. "
        f"Got: {match.group(1).strip()!r}"
    )


def test_log_file_has_expected_user_id(log_contents: str, expected_user_id: str):
    match = USER_ID_RE.search(log_contents)
    assert match, (
        f"Expected {LOG_FILE} to contain a line in the form 'User ID: <user>'. "
        f"Got contents: {log_contents!r}"
    )
    assert match.group(1).strip() == expected_user_id, (
        f"User ID in log file does not match expected '{expected_user_id}'. "
        f"Got: {match.group(1).strip()!r}"
    )


def test_log_file_has_expected_session_id(log_contents: str, expected_session_id: str):
    match = SESSION_ID_RE.search(log_contents)
    assert match, (
        f"Expected {LOG_FILE} to contain a line in the form 'Session ID: <session>'. "
        f"Got contents: {log_contents!r}"
    )
    assert match.group(1).strip() == expected_session_id, (
        f"Session ID in log file does not match expected '{expected_session_id}'. "
        f"Got: {match.group(1).strip()!r}"
    )


def test_log_file_has_status_ok(log_contents: str):
    assert STATUS_RE.search(log_contents), (
        f"Expected {LOG_FILE} to contain a line 'Status: OK'. Got: {log_contents!r}"
    )


@pytest.fixture(scope="session")
def trace_detail(langfuse_config, trace_id_from_log):
    detail_url = (
        f"{langfuse_config['base_url']}/api/public/traces/{trace_id_from_log}"
    )
    detail = None
    last_status = None
    last_body = None
    for _ in range(12):
        resp = requests.get(
            detail_url, auth=langfuse_config["auth"], timeout=30
        )
        last_status = resp.status_code
        try:
            last_body = resp.text[:500]
        except Exception:  # pragma: no cover - defensive
            last_body = None
        if resp.status_code == 200:
            payload = resp.json()
            if (
                payload
                and payload.get("id") == trace_id_from_log
                and payload.get("observations") is not None
            ):
                detail = payload
                break
        time.sleep(5)

    assert detail is not None, (
        f"Could not retrieve trace detail from {detail_url}. "
        f"Last status: {last_status}. Last body: {last_body!r}"
    )
    return detail


def test_trace_name_matches_expected(trace_detail, expected_trace_name):
    assert trace_detail.get("name") == expected_trace_name, (
        f"Trace name mismatch. Expected '{expected_trace_name}', "
        f"got {trace_detail.get('name')!r}."
    )


def test_trace_user_id_matches_expected(trace_detail, expected_user_id):
    assert trace_detail.get("userId") == expected_user_id, (
        f"Trace userId mismatch. Expected '{expected_user_id}', "
        f"got {trace_detail.get('userId')!r}."
    )


def test_trace_session_id_matches_expected(trace_detail, expected_session_id):
    assert trace_detail.get("sessionId") == expected_session_id, (
        f"Trace sessionId mismatch. Expected '{expected_session_id}', "
        f"got {trace_detail.get('sessionId')!r}."
    )


def test_trace_tags_contain_expected(trace_detail, expected_run_tag):
    tags = trace_detail.get("tags") or []
    assert isinstance(tags, list), (
        f"Trace tags must be a list of strings. Got: {tags!r}"
    )
    assert "harbor-langchain" in tags, (
        f"Trace tags must contain 'harbor-langchain'. Got: {tags!r}"
    )
    assert expected_run_tag in tags, (
        f"Trace tags must contain '{expected_run_tag}'. Got: {tags!r}"
    )


def test_trace_observations_include_generation(trace_detail):
    observations = trace_detail.get("observations") or []
    assert observations, (
        "Trace detail must include at least one observation. "
        f"Got: {observations!r}"
    )
    generations = [
        obs
        for obs in observations
        if (obs.get("type") or "").upper() == "GENERATION"
    ]
    assert generations, (
        "Expected at least one observation with type GENERATION. "
        f"Got observation types: {[o.get('type') for o in observations]}"
    )

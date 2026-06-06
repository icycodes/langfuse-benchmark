import os
import re
import time

import pytest
import requests
from requests.auth import HTTPBasicAuth

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

TRACE_ID_RE = re.compile(r"Trace ID:\s*([0-9a-fA-F]{32})")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID must be set in the verifier environment."
    return run_id


def _langfuse_base_url() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set in the verifier environment."
    return base.rstrip("/")


def _auth() -> HTTPBasicAuth:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    assert public_key, "LANGFUSE_PUBLIC_KEY must be set in the verifier environment."
    assert secret_key, "LANGFUSE_SECRET_KEY must be set in the verifier environment."
    return HTTPBasicAuth(public_key, secret_key)


@pytest.fixture(scope="session")
def trace_id() -> str:
    assert os.path.isfile(LOG_PATH), (
        f"Expected log file at {LOG_PATH}; the executor must write 'Trace ID: <trace_id>' there."
    )
    with open(LOG_PATH, "r") as f:
        content = f.read()
    match = TRACE_ID_RE.search(content)
    assert match, (
        f"Expected log file {LOG_PATH} to contain a line in the form "
        f"'Trace ID: <32-hex>'. Got file content: {content!r}"
    )
    return match.group(1)


@pytest.fixture(scope="session")
def trace_payload(trace_id: str) -> dict:
    """Fetch the trace from the Langfuse Public API with retry/backoff."""
    base = _langfuse_base_url()
    auth = _auth()
    url = f"{base}/api/public/traces/{trace_id}"

    deadline = time.time() + 90  # ingestion is async; retry for up to 90s
    last_status = None
    last_text = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, auth=auth, timeout=15)
        except requests.RequestException as e:  # pragma: no cover - network jitter
            last_text = str(e)
            time.sleep(3)
            continue
        last_status = resp.status_code
        last_text = resp.text
        if resp.status_code == 200:
            return resp.json()
        # 404 is expected while the trace is still being ingested
        if resp.status_code not in (404, 502, 503, 504):
            break
        time.sleep(3)
    pytest.fail(
        f"Failed to fetch trace {trace_id} from {url}. "
        f"Last status: {last_status}. Last response: {last_text!r}"
    )


def test_trace_name_is_chat_turn(trace_payload: dict) -> None:
    assert trace_payload.get("name") == "chat-turn", (
        f"Expected trace.name == 'chat-turn', got {trace_payload.get('name')!r}."
    )


def test_trace_user_id_matches_run_id(trace_payload: dict) -> None:
    expected = f"user-{_run_id()}"
    assert trace_payload.get("userId") == expected, (
        f"Expected trace.userId == {expected!r}, got {trace_payload.get('userId')!r}."
    )


def test_trace_session_id_matches_run_id(trace_payload: dict) -> None:
    expected = f"session-{_run_id()}"
    assert trace_payload.get("sessionId") == expected, (
        f"Expected trace.sessionId == {expected!r}, got {trace_payload.get('sessionId')!r}."
    )


def test_trace_tags_contain_both_required_tags(trace_payload: dict) -> None:
    expected_run_tag = f"demo-{_run_id()}"
    tags = trace_payload.get("tags") or []
    assert isinstance(tags, list), f"Expected trace.tags to be a list, got {type(tags).__name__}."
    assert expected_run_tag in tags, (
        f"Expected trace.tags to include {expected_run_tag!r}, got {tags!r}."
    )
    assert "python-sdk" in tags, (
        f"Expected trace.tags to include 'python-sdk', got {tags!r}."
    )


def test_trace_has_generation_named_assistant_reply(trace_payload: dict) -> None:
    observations = trace_payload.get("observations") or []
    assert isinstance(observations, list) and len(observations) > 0, (
        f"Expected at least one observation on the trace; got {observations!r}."
    )
    matches = [
        obs
        for obs in observations
        if (obs.get("type") or "").upper() == "GENERATION"
        and obs.get("name") == "assistant-reply"
    ]
    assert matches, (
        "Expected at least one observation with type == 'GENERATION' and "
        f"name == 'assistant-reply'. Got observations: "
        f"{[(o.get('type'), o.get('name')) for o in observations]!r}"
    )

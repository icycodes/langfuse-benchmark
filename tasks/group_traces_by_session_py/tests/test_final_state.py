import os
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "chat_session.py")
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_TRACE_NAMES = {"greeting-turn", "followup-turn", "farewell-turn"}


def _run_id():
    rid = os.environ.get("ZEALT_RUN_ID", "")
    assert rid, "ZEALT_RUN_ID environment variable must be set for verification."
    return rid


def _ids():
    rid = _run_id()
    return (
        f"chat-session-{rid}",
        f"chat-user-{rid}",
        f"harbor-demo-{rid}",
    )


def _auth():
    pub = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sec = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert pub and sec, (
        "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in the verifier environment."
    )
    return (pub, sec)


def _host():
    host = os.environ.get("LANGFUSE_HOST", "").rstrip("/")
    assert host, "LANGFUSE_HOST must be set in the verifier environment."
    return host


def _get_with_retry(url, **kwargs):
    """GET with simple retry-until-success up to ~60s to accommodate ingestion lag."""
    last_resp = None
    deadline = time.time() + 60
    backoff = 2.0
    while time.time() < deadline:
        resp = requests.get(url, timeout=30, **kwargs)
        last_resp = resp
        if resp.status_code == 200:
            return resp
        time.sleep(backoff)
        backoff = min(backoff * 1.5, 8.0)
    return last_resp


def _list_traces_by_session(session_id):
    """List traces with session filter, retrying until we see the expected three."""
    url = f"{_host()}/api/public/traces"
    params = {"sessionId": session_id, "limit": 50}
    deadline = time.time() + 90
    backoff = 2.0
    last_data = []
    last_status = None
    while time.time() < deadline:
        resp = requests.get(url, auth=_auth(), params=params, timeout=30)
        last_status = resp.status_code
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            last_data = data
            names = {t.get("name") for t in data}
            if EXPECTED_TRACE_NAMES.issubset(names):
                return data
        time.sleep(backoff)
        backoff = min(backoff * 1.5, 8.0)
    pytest.fail(
        f"Did not see all expected traces for session '{session_id}' within timeout. "
        f"Last status: {last_status}, last data sample names: "
        f"{[t.get('name') for t in last_data]}"
    )


def test_script_file_exists():
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected the executor to create {SCRIPT_PATH}, but it does not exist."
    )


def test_log_file_contains_session_id():
    session_id, _, _ = _ids()
    assert os.path.isfile(LOG_PATH), (
        f"Expected the executor to create {LOG_PATH}, but it does not exist."
    )
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]
    expected_line = f"Session ID: {session_id}"
    assert expected_line in lines, (
        f"Expected '{expected_line}' to appear as a line in {LOG_PATH}. Got lines: {lines}"
    )


def test_session_endpoint_returns_three_traces():
    session_id, _, _ = _ids()
    url = f"{_host()}/api/public/sessions/{session_id}"
    resp = _get_with_retry(url, auth=_auth())
    assert resp is not None and resp.status_code == 200, (
        f"GET {url} did not return 200; got "
        f"{getattr(resp, 'status_code', 'no-response')} body="
        f"{getattr(resp, 'text', '')[:500]}"
    )
    body = resp.json()
    traces = body.get("traces", [])
    # Allow a short follow-up window if the session exists but traces are still being ingested.
    deadline = time.time() + 60
    while len(traces) < 3 and time.time() < deadline:
        time.sleep(3)
        resp = requests.get(url, auth=_auth(), timeout=30)
        if resp.status_code == 200:
            traces = resp.json().get("traces", [])
    assert len(traces) >= 3, (
        f"Expected at least 3 traces under session '{session_id}', got {len(traces)}."
    )


def test_traces_have_expected_names_user_and_tag():
    session_id, user_id, tag = _ids()
    traces = _list_traces_by_session(session_id)
    matching = [t for t in traces if t.get("name") in EXPECTED_TRACE_NAMES]
    names = {t.get("name") for t in matching}
    assert names == EXPECTED_TRACE_NAMES, (
        f"Expected trace names {EXPECTED_TRACE_NAMES} in session '{session_id}', got {names}."
    )
    # Each matching trace must have the right userId and include the required tag.
    for t in matching:
        assert t.get("userId") == user_id, (
            f"Trace '{t.get('name')}' has userId={t.get('userId')!r}, expected {user_id!r}."
        )
        tags = t.get("tags") or []
        assert tag in tags, (
            f"Trace '{t.get('name')}' tags={tags!r} do not include required tag {tag!r}."
        )


def test_each_trace_has_a_generation_observation():
    session_id, _, _ = _ids()
    traces = _list_traces_by_session(session_id)
    relevant = [t for t in traces if t.get("name") in EXPECTED_TRACE_NAMES]
    assert len(relevant) >= 3, (
        f"Expected 3 matching traces for session '{session_id}', got {len(relevant)}."
    )
    for t in relevant:
        trace_id = t.get("id")
        assert trace_id, f"Trace missing id: {t}"
        url = f"{_host()}/api/public/traces/{trace_id}"
        resp = _get_with_retry(url, auth=_auth())
        assert resp is not None and resp.status_code == 200, (
            f"GET {url} did not return 200; got "
            f"{getattr(resp, 'status_code', 'no-response')}."
        )
        body = resp.json()
        observations = body.get("observations", [])
        types = [o.get("type") for o in observations]
        assert any(typ == "GENERATION" for typ in types), (
            f"Trace '{t.get('name')}' ({trace_id}) does not have any GENERATION "
            f"observation. Observation types: {types}"
        )

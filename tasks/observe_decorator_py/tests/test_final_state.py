import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

TRACE_ID_LINE_RE = re.compile(r"^Trace ID: (?P<trace_id>[A-Za-z0-9_\-]+)$", re.MULTILINE)


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id


def _langfuse_creds():
    pub = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sec = os.environ.get("LANGFUSE_SECRET_KEY")
    base = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    assert pub and sec and base, (
        "Langfuse credentials (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, "
        "LANGFUSE_BASE_URL) must be present in the environment."
    )
    return pub, sec, base


def _read_trace_id() -> str:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    matches = TRACE_ID_LINE_RE.findall(content)
    assert len(matches) == 1, (
        f"Expected exactly one line matching 'Trace ID: <trace_id>' in {LOG_FILE}, "
        f"got {len(matches)}. File content was:\n{content}"
    )
    trace_id = matches[0]
    assert trace_id, "Trace ID extracted from log file is empty."
    return trace_id


def _get_trace(trace_id: str) -> dict:
    pub, sec, base = _langfuse_creds()
    url = f"{base}/api/public/traces/{trace_id}"
    deadline = time.time() + 60
    last_status = None
    last_body = None
    while time.time() < deadline:
        resp = requests.get(url, auth=(pub, sec), timeout=20)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                data = None
            if data and data.get("observations"):
                return data
        time.sleep(3)
    pytest.fail(
        f"Timed out waiting for trace {trace_id} to appear in Langfuse. "
        f"Last status={last_status}, body={last_body!r}"
    )


def test_log_file_contains_trace_id():
    trace_id = _read_trace_id()
    assert trace_id


def test_trace_metadata_matches_expected():
    run_id = _run_id()
    expected_session_id = f"obs-deco-session-{run_id}"
    expected_user_id = f"obs-deco-user-{run_id}"
    expected_run_tag = f"harbor-{run_id}"

    trace_id = _read_trace_id()
    trace = _get_trace(trace_id)

    assert trace.get("userId") == expected_user_id, (
        f"Expected trace.userId == {expected_user_id!r}, got {trace.get('userId')!r}"
    )
    assert trace.get("sessionId") == expected_session_id, (
        f"Expected trace.sessionId == {expected_session_id!r}, "
        f"got {trace.get('sessionId')!r}"
    )
    tags = trace.get("tags") or []
    assert "obs-decorator" in tags, (
        f"Expected trace.tags to contain 'obs-decorator', got {tags!r}"
    )
    assert expected_run_tag in tags, (
        f"Expected trace.tags to contain {expected_run_tag!r}, got {tags!r}"
    )


def test_trace_has_nested_generation_observation():
    trace_id = _read_trace_id()
    trace = _get_trace(trace_id)

    observations = trace.get("observations") or []
    assert len(observations) >= 2, (
        f"Expected trace to contain at least 2 observations, got {len(observations)}: "
        f"{observations!r}"
    )

    generations = [o for o in observations if (o.get("type") or "").upper() == "GENERATION"]
    assert len(generations) == 1, (
        f"Expected exactly 1 GENERATION observation in trace, got {len(generations)}: "
        f"{[o.get('type') for o in observations]}"
    )
    generation = generations[0]
    model = generation.get("model")
    assert isinstance(model, str) and model.strip(), (
        f"Expected the generation observation to have a non-empty model field, "
        f"got {model!r}"
    )

    spans = [o for o in observations if (o.get("type") or "").upper() == "SPAN"]
    assert spans, (
        f"Expected at least 1 SPAN observation, got types "
        f"{[o.get('type') for o in observations]}"
    )

    parent_id = generation.get("parentObservationId")
    assert parent_id, (
        f"Expected the generation observation to have a parentObservationId, "
        f"got {generation!r}"
    )
    parent_ids_of_spans = {s.get("id") for s in spans}
    assert parent_id in parent_ids_of_spans, (
        f"Expected the generation's parentObservationId ({parent_id!r}) to match "
        f"the id of a SPAN observation. SPAN ids: {parent_ids_of_spans!r}"
    )


def test_trace_discoverable_via_list_endpoint():
    run_id = _run_id()
    expected_user_id = f"obs-deco-user-{run_id}"
    expected_run_tag = f"harbor-{run_id}"
    trace_id = _read_trace_id()

    pub, sec, base = _langfuse_creds()
    url = f"{base}/api/public/traces"
    params = {
        "tags": expected_run_tag,
        "userId": expected_user_id,
        "limit": 10,
    }

    deadline = time.time() + 60
    last_body = None
    while time.time() < deadline:
        resp = requests.get(url, params=params, auth=(pub, sec), timeout=20)
        last_body = resp.text
        if resp.status_code == 200:
            data = resp.json().get("data") or []
            if any(item.get("id") == trace_id for item in data):
                return
        time.sleep(3)

    pytest.fail(
        f"Trace {trace_id} did not appear in /api/public/traces filtered by "
        f"tags={expected_run_tag} and userId={expected_user_id}. "
        f"Last response body: {last_body!r}"
    )

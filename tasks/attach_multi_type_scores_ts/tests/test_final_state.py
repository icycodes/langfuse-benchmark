import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_BASE_URL = os.environ.get("LANGFUSE_BASE_URL", "").rstrip("/")
RUN_ID = os.environ.get("ZEALT_RUN_ID", "")
EXPECTED_TRACE_NAME = f"multi-score-demo-{RUN_ID}"

AUTH = (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)

# Allow ample time for the asynchronous ingestion pipeline.
POLL_TIMEOUT_SECS = 90
POLL_INTERVAL_SECS = 3


def _read_trace_id_from_log() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to be created by the script."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    match = re.search(
        r"^Trace ID:\s*(?P<trace_id>[A-Za-z0-9\-]+)\s*$", text, re.MULTILINE
    )
    assert match, (
        "Could not find a line in the format 'Trace ID: <trace_id>' in the log file. "
        f"Log content was: {text!r}"
    )
    trace_id = match.group("trace_id").strip()
    assert len(trace_id) >= 8, (
        f"Trace ID found in the log looks too short to be valid: {trace_id!r}"
    )
    return trace_id


@pytest.fixture(scope="module")
def trace_id() -> str:
    return _read_trace_id_from_log()


def _get_trace(trace_id_value: str):
    """Poll GET /api/public/traces/{traceId} until the trace is available."""
    url = f"{LANGFUSE_BASE_URL}/api/public/traces/{trace_id_value}"
    last_status = None
    last_body = None
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(url, auth=AUTH, timeout=30)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            return resp.json()
        time.sleep(POLL_INTERVAL_SECS)
    pytest.fail(
        f"Failed to fetch trace {trace_id_value} from Langfuse within "
        f"{POLL_TIMEOUT_SECS}s. Last status: {last_status}, body: {last_body!r}"
    )


def _get_scores(trace_id_value: str):
    """Poll GET /api/public/v2/scores?traceId=... until at least 3 scores are returned."""
    url = f"{LANGFUSE_BASE_URL}/api/public/v2/scores"
    last_status = None
    last_body = None
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(
            url,
            params={"traceId": trace_id_value, "limit": 100},
            auth=AUTH,
            timeout=30,
        )
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            target = [s for s in data if s.get("traceId") == trace_id_value]
            if len(target) >= 3:
                return target
        time.sleep(POLL_INTERVAL_SECS)
    pytest.fail(
        f"Did not see >=3 scores for trace {trace_id_value} within "
        f"{POLL_TIMEOUT_SECS}s. Last status: {last_status}, body: {last_body!r}"
    )


def test_log_file_contains_trace_id():
    trace_id_value = _read_trace_id_from_log()
    assert trace_id_value, "The log file must contain a non-empty Trace ID."


def test_run_id_is_set():
    assert RUN_ID, (
        "ZEALT_RUN_ID must be set in the verifier environment to derive the expected trace name."
    )


def test_trace_exists_with_expected_name(trace_id):
    trace = _get_trace(trace_id)
    assert trace.get("name") == EXPECTED_TRACE_NAME, (
        f"Expected trace name to be {EXPECTED_TRACE_NAME!r}, "
        f"but Langfuse returned name={trace.get('name')!r} for trace {trace}."
    )


def test_trace_has_generation_observation_named_llm_call(trace_id):
    trace = _get_trace(trace_id)
    observations = trace.get("observations") or []
    # The trace endpoint may return observations either as full objects or as
    # plain string IDs depending on the response shape. Handle both.
    matches = []
    for obs in observations:
        if isinstance(obs, dict):
            obs_type = (obs.get("type") or "").upper()
            obs_name = obs.get("name")
            if obs_type == "GENERATION" and obs_name == "llm-call":
                matches.append(obs)
    # Fallback: if observations is a list of IDs, query the observations API.
    if not matches and observations and all(
        isinstance(o, str) for o in observations
    ):
        for obs_id in observations:
            url = f"{LANGFUSE_BASE_URL}/api/public/observations/{obs_id}"
            r = requests.get(url, auth=AUTH, timeout=30)
            if r.status_code == 200:
                obs = r.json()
                if (
                    (obs.get("type") or "").upper() == "GENERATION"
                    and obs.get("name") == "llm-call"
                ):
                    matches.append(obs)
    assert matches, (
        "Expected the trace to include a nested observation with name='llm-call' and "
        f"type='GENERATION'. Observations: {observations!r}"
    )


def test_correctness_numeric_score_attached(trace_id):
    scores = _get_scores(trace_id)
    matches = [s for s in scores if s.get("name") == "correctness"]
    assert len(matches) >= 1, (
        f"Expected at least one score named 'correctness' on trace {trace_id}. "
        f"Found scores: {scores!r}"
    )
    score = matches[0]
    assert (score.get("dataType") or "").upper() == "NUMERIC", (
        f"Expected dataType=NUMERIC for the 'correctness' score, got {score!r}."
    )
    value = score.get("value")
    assert isinstance(value, (int, float)) and abs(float(value) - 0.92) < 1e-6, (
        f"Expected value=0.92 for the 'correctness' score, got {value!r} in {score!r}."
    )


def test_sentiment_categorical_score_attached(trace_id):
    scores = _get_scores(trace_id)
    matches = [s for s in scores if s.get("name") == "sentiment"]
    assert len(matches) >= 1, (
        f"Expected at least one score named 'sentiment' on trace {trace_id}. "
        f"Found scores: {scores!r}"
    )
    score = matches[0]
    assert (score.get("dataType") or "").upper() == "CATEGORICAL", (
        f"Expected dataType=CATEGORICAL for the 'sentiment' score, got {score!r}."
    )
    string_value = score.get("stringValue") or score.get("value")
    assert string_value == "positive", (
        f"Expected stringValue='positive' for the 'sentiment' score, got {string_value!r} in {score!r}."
    )


def test_helpfulness_boolean_score_attached(trace_id):
    scores = _get_scores(trace_id)
    matches = [s for s in scores if s.get("name") == "helpfulness"]
    assert len(matches) >= 1, (
        f"Expected at least one score named 'helpfulness' on trace {trace_id}. "
        f"Found scores: {scores!r}"
    )
    score = matches[0]
    assert (score.get("dataType") or "").upper() == "BOOLEAN", (
        f"Expected dataType=BOOLEAN for the 'helpfulness' score, got {score!r}."
    )
    value = score.get("value")
    # Boolean scores are stored numerically as 0/1.
    assert value in (1, 1.0, True), (
        f"Expected value=1 for the 'helpfulness' score, got {value!r} in {score!r}."
    )

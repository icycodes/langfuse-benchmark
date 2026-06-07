import os
import re

import pytest
import requests

LOG_PATH = "/home/user/langfuse_task/output.log"


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    assert value, f"Required environment variable {name} is not set in the verifier environment."
    return value


@pytest.fixture(scope="module")
def run_id() -> str:
    return _required_env("ZEALT_RUN_ID")


@pytest.fixture(scope="module")
def langfuse_base_url() -> str:
    return _required_env("LANGFUSE_BASE_URL").rstrip("/")


@pytest.fixture(scope="module")
def langfuse_auth():
    return (_required_env("LANGFUSE_PUBLIC_KEY"), _required_env("LANGFUSE_SECRET_KEY"))


@pytest.fixture(scope="module")
def log_lines():
    assert os.path.isfile(LOG_PATH), f"Expected log file {LOG_PATH} does not exist."
    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh.readlines()]


@pytest.fixture(scope="module")
def parsed_log(log_lines, run_id):
    trace_id = None
    generation_id = None
    user_id = None
    session_id = None
    status_seen = False
    for line in log_lines:
        m = re.match(r"^Trace ID:\s*(\S+)\s*$", line)
        if m:
            trace_id = m.group(1)
            continue
        m = re.match(r"^Generation ID:\s*(\S+)\s*$", line)
        if m:
            generation_id = m.group(1)
            continue
        m = re.match(r"^User ID:\s*(\S+)\s*$", line)
        if m:
            user_id = m.group(1)
            continue
        m = re.match(r"^Session ID:\s*(\S+)\s*$", line)
        if m:
            session_id = m.group(1)
            continue
        if line.strip() == "Status: OK":
            status_seen = True
    assert trace_id, f"Log file {LOG_PATH} is missing a 'Trace ID: <id>' line."
    assert generation_id, f"Log file {LOG_PATH} is missing a 'Generation ID: <id>' line."
    assert user_id, f"Log file {LOG_PATH} is missing a 'User ID: <id>' line."
    assert session_id, f"Log file {LOG_PATH} is missing a 'Session ID: <id>' line."
    assert status_seen, f"Log file {LOG_PATH} is missing the 'Status: OK' line."
    expected_user = f"user-{run_id}"
    expected_session = f"session-{run_id}"
    assert user_id == expected_user, (
        f"Logged User ID '{user_id}' does not match expected '{expected_user}'."
    )
    assert session_id == expected_session, (
        f"Logged Session ID '{session_id}' does not match expected '{expected_session}'."
    )
    return {
        "trace_id": trace_id,
        "generation_id": generation_id,
        "user_id": user_id,
        "session_id": session_id,
    }


@pytest.fixture(scope="module")
def trace_response(langfuse_base_url, langfuse_auth, parsed_log):
    url = f"{langfuse_base_url}/api/public/traces/{parsed_log['trace_id']}"
    resp = requests.get(url, auth=langfuse_auth, timeout=30)
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    return resp.json()


@pytest.fixture(scope="module")
def scores_response(langfuse_base_url, langfuse_auth, parsed_log):
    url = f"{langfuse_base_url}/api/public/v2/scores"
    params = {"traceId": parsed_log["trace_id"], "limit": 50}
    resp = requests.get(url, params=params, auth=langfuse_auth, timeout=30)
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    body = resp.json()
    assert isinstance(body.get("data"), list), (
        f"Scores response missing 'data' array: {body}"
    )
    return body["data"]


def test_log_file_well_formed(parsed_log):
    # Fixture validates structure; this test passes when parsing succeeded.
    assert parsed_log["trace_id"]
    assert parsed_log["generation_id"]


def test_trace_has_expected_user_and_session(trace_response, run_id):
    expected_user = f"user-{run_id}"
    expected_session = f"session-{run_id}"
    assert trace_response.get("userId") == expected_user, (
        f"Trace userId mismatch. Expected '{expected_user}', got: {trace_response.get('userId')!r}"
    )
    assert trace_response.get("sessionId") == expected_session, (
        f"Trace sessionId mismatch. Expected '{expected_session}', got: {trace_response.get('sessionId')!r}"
    )


def test_trace_contains_expected_generation_observation(trace_response, parsed_log, run_id):
    observations = trace_response.get("observations") or []
    assert isinstance(observations, list) and observations, (
        f"Trace has no observations; expected at least one generation. Trace: {trace_response}"
    )
    generation_id = parsed_log["generation_id"]
    expected_gen_name = f"summarize-{run_id}"
    matching = [obs for obs in observations if obs.get("id") == generation_id]
    assert matching, (
        f"No observation with id '{generation_id}' found on trace. "
        f"Observation ids: {[obs.get('id') for obs in observations]}"
    )
    gen_obs = matching[0]
    assert str(gen_obs.get("type", "")).upper() == "GENERATION", (
        f"Observation '{generation_id}' is not a GENERATION (got type: {gen_obs.get('type')!r})."
    )
    assert gen_obs.get("name") == expected_gen_name, (
        f"Generation observation name mismatch. Expected '{expected_gen_name}', got: {gen_obs.get('name')!r}."
    )
    assert gen_obs.get("model") == "gpt-3.5-turbo", (
        f"Generation observation model mismatch. Expected 'gpt-3.5-turbo', got: {gen_obs.get('model')!r}."
    )


def test_user_satisfaction_score_attached_to_trace(scores_response, parsed_log):
    matching = [s for s in scores_response if s.get("name") == "user_satisfaction"]
    assert len(matching) == 1, (
        f"Expected exactly 1 'user_satisfaction' score on the trace, found {len(matching)}: {matching}"
    )
    score = matching[0]
    data_type = str(score.get("dataType", "")).upper()
    assert data_type == "NUMERIC", (
        f"'user_satisfaction' score dataType expected NUMERIC, got: {score.get('dataType')!r}."
    )
    value = score.get("value")
    assert isinstance(value, (int, float)) and abs(float(value) - 0.8) <= 0.001, (
        f"'user_satisfaction' score value expected 0.8, got: {value!r}."
    )
    observation_id = score.get("observationId")
    assert observation_id in (None, "", "null"), (
        f"'user_satisfaction' must be a trace-level score (no observationId), got: {observation_id!r}."
    )


def test_hallucination_boolean_score_attached_to_generation(scores_response, parsed_log):
    matching = [s for s in scores_response if s.get("name") == "hallucination"]
    assert len(matching) == 1, (
        f"Expected exactly 1 'hallucination' score on the trace, found {len(matching)}: {matching}"
    )
    score = matching[0]
    data_type = str(score.get("dataType", "")).upper()
    assert data_type == "BOOLEAN", (
        f"'hallucination' score dataType expected BOOLEAN, got: {score.get('dataType')!r}."
    )
    value = score.get("value")
    assert isinstance(value, (int, float)) and float(value) == 0.0, (
        f"'hallucination' score numeric value expected 0, got: {value!r}."
    )
    assert score.get("observationId") == parsed_log["generation_id"], (
        f"'hallucination' score must be attached to the generation observation "
        f"'{parsed_log['generation_id']}', got: {score.get('observationId')!r}."
    )


def test_relevance_categorical_score_attached_to_generation(scores_response, parsed_log):
    matching = [s for s in scores_response if s.get("name") == "relevance"]
    assert len(matching) == 1, (
        f"Expected exactly 1 'relevance' score on the trace, found {len(matching)}: {matching}"
    )
    score = matching[0]
    data_type = str(score.get("dataType", "")).upper()
    assert data_type == "CATEGORICAL", (
        f"'relevance' score dataType expected CATEGORICAL, got: {score.get('dataType')!r}."
    )
    string_value = score.get("stringValue")
    assert string_value == "high", (
        f"'relevance' score stringValue expected 'high', got: {string_value!r}."
    )
    assert score.get("observationId") == parsed_log["generation_id"], (
        f"'relevance' score must be attached to the generation observation "
        f"'{parsed_log['generation_id']}', got: {score.get('observationId')!r}."
    )

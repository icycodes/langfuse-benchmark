import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/task"
TRACE_ID_FILE = os.path.join(PROJECT_DIR, "trace_id.txt")
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

NUMERIC_LINE_REGEX = re.compile(r"^Numeric score ID:\s+([A-Za-z0-9_-]+)\s*$")
CATEGORICAL_LINE_REGEX = re.compile(r"^Categorical score ID:\s+([A-Za-z0-9_-]+)\s*$")


def _langfuse_credentials():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip(
        "/"
    )
    assert public_key, "LANGFUSE_PUBLIC_KEY must be set in the verifier environment."
    assert secret_key, "LANGFUSE_SECRET_KEY must be set in the verifier environment."
    return public_key, secret_key, base_url


def _read_trace_id():
    assert os.path.isfile(TRACE_ID_FILE), (
        f"Trace ID file {TRACE_ID_FILE} does not exist."
    )
    with open(TRACE_ID_FILE, "r", encoding="utf-8") as f:
        trace_id = f.read().strip()
    assert trace_id, f"Trace ID file {TRACE_ID_FILE} is empty."
    return trace_id


def _parse_log_file():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    lines = [ln.strip() for ln in raw_lines if ln.strip()]
    assert len(lines) == 2, (
        f"Expected exactly 2 non-empty lines in {LOG_FILE}, got {len(lines)}: {lines}"
    )
    numeric_match = NUMERIC_LINE_REGEX.match(lines[0])
    assert numeric_match, (
        f"First non-empty line in {LOG_FILE} must match 'Numeric score ID: <id>', "
        f"got: {lines[0]!r}"
    )
    categorical_match = CATEGORICAL_LINE_REGEX.match(lines[1])
    assert categorical_match, (
        f"Second non-empty line in {LOG_FILE} must match 'Categorical score ID: <id>', "
        f"got: {lines[1]!r}"
    )
    return numeric_match.group(1), categorical_match.group(1)


def _fetch_scores_for_trace(trace_id, max_wait_seconds=60, poll_interval=5):
    public_key, secret_key, base_url = _langfuse_credentials()
    url = f"{base_url}/api/public/scores"
    auth = (public_key, secret_key)
    deadline = time.time() + max_wait_seconds
    last_response = None
    last_data = None
    while time.time() < deadline:
        response = requests.get(
            url,
            params={"traceId": trace_id, "limit": 100},
            auth=auth,
            timeout=30,
        )
        last_response = response
        assert response.status_code == 200, (
            f"GET {url}?traceId={trace_id} returned {response.status_code}: "
            f"{response.text}"
        )
        payload = response.json()
        data = payload.get("data", [])
        last_data = data
        if len(data) >= 2:
            return data
        time.sleep(poll_interval)
    raise AssertionError(
        "Timed out waiting for 2 scores to be ingested for trace "
        f"{trace_id}. Last data: {last_data!r}. Last status: "
        f"{getattr(last_response, 'status_code', None)}."
    )


def _find_score_by_name(scores, name):
    matches = [s for s in scores if s.get("name") == name]
    assert matches, (
        f"Expected to find a score with name {name!r} attached to the trace. "
        f"Got: {[s.get('name') for s in scores]}"
    )
    assert len(matches) == 1, (
        f"Expected exactly one score with name {name!r}, found {len(matches)}: {matches}"
    )
    return matches[0]


@pytest.fixture(scope="module")
def trace_id():
    return _read_trace_id()


@pytest.fixture(scope="module")
def log_score_ids():
    return _parse_log_file()


@pytest.fixture(scope="module")
def scores(trace_id):
    return _fetch_scores_for_trace(trace_id)


def test_log_file_has_two_score_id_lines(log_score_ids):
    numeric_id, categorical_id = log_score_ids
    assert numeric_id, "Numeric score ID line did not produce an ID value."
    assert categorical_id, "Categorical score ID line did not produce an ID value."


def test_total_score_count_is_two(scores):
    assert len(scores) == 2, (
        f"Expected exactly 2 scores attached to the trace, got {len(scores)}: "
        f"{[s.get('name') for s in scores]}"
    )


def test_numeric_score_qa_quality(scores, log_score_ids):
    numeric_id_from_log, _ = log_score_ids
    score = _find_score_by_name(scores, "qa_quality")
    assert score.get("dataType") == "NUMERIC", (
        f"Expected qa_quality dataType to be 'NUMERIC', got {score.get('dataType')!r}."
    )
    assert score.get("value") == 0.95, (
        f"Expected qa_quality value to be 0.95, got {score.get('value')!r}."
    )
    assert score.get("comment") == "Approved by QA team", (
        f"Expected qa_quality comment to be 'Approved by QA team', got "
        f"{score.get('comment')!r}."
    )
    assert score.get("id") == numeric_id_from_log, (
        f"Numeric score ID logged ({numeric_id_from_log!r}) does not match the score "
        f"ID returned by the Langfuse API ({score.get('id')!r})."
    )


def test_categorical_score_qa_verdict(scores, log_score_ids):
    _, categorical_id_from_log = log_score_ids
    score = _find_score_by_name(scores, "qa_verdict")
    assert score.get("dataType") == "CATEGORICAL", (
        f"Expected qa_verdict dataType to be 'CATEGORICAL', got "
        f"{score.get('dataType')!r}."
    )
    assert score.get("stringValue") == "approved", (
        f"Expected qa_verdict stringValue to be 'approved', got "
        f"{score.get('stringValue')!r}."
    )
    assert score.get("comment") == "Looks good", (
        f"Expected qa_verdict comment to be 'Looks good', got {score.get('comment')!r}."
    )
    assert score.get("id") == categorical_id_from_log, (
        f"Categorical score ID logged ({categorical_id_from_log!r}) does not match "
        f"the score ID returned by the Langfuse API ({score.get('id')!r})."
    )

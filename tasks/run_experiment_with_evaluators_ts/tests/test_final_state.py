import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

EXPERIMENT_LINE_RE = re.compile(r"^Experiment name:\s*(\S.*?)\s*$", re.MULTILINE)
TRACE_LINE_RE = re.compile(r"^Trace ID:\s*(\S+)\s*$", re.MULTILINE)


def _langfuse_base_url() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL", "").rstrip("/")
    assert base, "LANGFUSE_BASE_URL environment variable is not set."
    return base


def _langfuse_auth() -> tuple:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert public_key, "LANGFUSE_PUBLIC_KEY environment variable is not set."
    assert secret_key, "LANGFUSE_SECRET_KEY environment variable is not set."
    return (public_key, secret_key)


def _expected_experiment_name() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return f"harbor-experiment-{run_id}"


@pytest.fixture(scope="module")
def log_content() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file at {LOG_FILE} after the task script runs, but it does not exist."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def trace_ids(log_content) -> list:
    ids = TRACE_LINE_RE.findall(log_content)
    assert len(ids) == 3, (
        f"Expected exactly 3 lines of the form 'Trace ID: <id>' in {LOG_FILE}, "
        f"got {len(ids)}. Log content was:\n{log_content}"
    )
    for tid in ids:
        assert tid, f"Encountered empty trace ID in {LOG_FILE}."
    return ids


def test_log_file_contains_experiment_name(log_content):
    matches = EXPERIMENT_LINE_RE.findall(log_content)
    assert len(matches) == 1, (
        f"Expected exactly one 'Experiment name: <name>' line in {LOG_FILE}, found {len(matches)}. "
        f"Log content was:\n{log_content}"
    )
    expected = _expected_experiment_name()
    assert matches[0] == expected, (
        f"Expected experiment name '{expected}' in {LOG_FILE}, got '{matches[0]}'."
    )


def test_log_file_records_three_trace_ids(trace_ids):
    # The trace_ids fixture itself asserts that exactly 3 non-empty trace IDs are present.
    assert len(set(trace_ids)) == 3, (
        f"Expected the 3 logged trace IDs to be distinct, got duplicates: {trace_ids}"
    )


def _fetch_trace(trace_id: str) -> dict:
    base = _langfuse_base_url()
    auth = _langfuse_auth()
    url = f"{base}/api/public/traces/{trace_id}"
    # Trace ingestion is async; retry a few times to handle propagation delay.
    last_status = None
    last_body = None
    for _ in range(12):
        resp = requests.get(url, auth=auth, timeout=30)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            return resp.json()
        time.sleep(5)
    raise AssertionError(
        f"Failed to fetch trace {trace_id} from Langfuse at {url}. "
        f"Last status={last_status}, body={last_body[:500] if last_body else ''}"
    )


def _fetch_scores_for_trace(trace_id: str) -> list:
    base = _langfuse_base_url()
    auth = _langfuse_auth()
    url = f"{base}/api/public/v2/scores"
    last_status = None
    last_body = None
    for _ in range(12):
        resp = requests.get(
            url,
            params={"traceId": trace_id, "limit": 100},
            auth=auth,
            timeout=30,
        )
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            payload = resp.json()
            data = payload.get("data") or []
            names = {s.get("name") for s in data if isinstance(s, dict)}
            if "accuracy" in names and "response_length" in names:
                return data
        time.sleep(5)
    raise AssertionError(
        f"Did not observe both 'accuracy' and 'response_length' scores for trace {trace_id} "
        f"via {url}?traceId={trace_id}. Last status={last_status}, "
        f"body={last_body[:500] if last_body else ''}"
    )


def test_each_trace_exists_in_langfuse(trace_ids):
    for tid in trace_ids:
        body = _fetch_trace(tid)
        assert body.get("id") == tid, (
            f"Trace fetched from Langfuse has id '{body.get('id')}', expected '{tid}'."
        )


def test_each_trace_has_accuracy_and_response_length_scores(trace_ids):
    for tid in trace_ids:
        scores = _fetch_scores_for_trace(tid)
        names = [s.get("name") for s in scores if isinstance(s, dict)]
        assert "accuracy" in names, (
            f"Trace {tid} is missing a score named 'accuracy'. Got score names: {names}."
        )
        assert "response_length" in names, (
            f"Trace {tid} is missing a score named 'response_length'. Got score names: {names}."
        )

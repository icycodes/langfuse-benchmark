import math
import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_USAGE = {"input": 25, "output": 40, "total": 65}
EXPECTED_COST = {"input": 0.000125, "output": 0.00040, "total": 0.000525}
COST_TOLERANCE = 1e-9


def _basic_auth():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    assert public_key, "LANGFUSE_PUBLIC_KEY must be set for verification."
    assert secret_key, "LANGFUSE_SECRET_KEY must be set for verification."
    return (public_key, secret_key)


def _base_url():
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set for verification."
    return base.rstrip("/")


def _run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID must be set for parallel-run isolation."
    return run_id


def _read_trace_id_from_log():
    assert os.path.isfile(LOG_PATH), (
        f"Expected log file {LOG_PATH} to exist after the task ran."
    )
    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()
    matches = re.findall(r"^Trace ID:\s*([A-Za-z0-9_\-]+)\s*$", content, re.MULTILINE)
    assert matches, (
        f"Log file {LOG_PATH} must contain a line in the form 'Trace ID: <trace_id>'. "
        f"Got:\n{content!r}"
    )
    assert len(matches) == 1, (
        f"Log file {LOG_PATH} must contain exactly one 'Trace ID:' line, found {len(matches)}."
    )
    return matches[0]


def _fetch_trace(trace_id):
    url = f"{_base_url()}/api/public/traces/{trace_id}"
    auth = _basic_auth()
    deadline = time.time() + 90  # allow ~90s for async ingestion
    last_status = None
    last_body = None
    while time.time() < deadline:
        resp = requests.get(url, auth=auth, timeout=15)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (401, 403):
            pytest.fail(
                f"Authentication to Langfuse Public API failed (status {resp.status_code}). "
                f"Check LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY. Body: {resp.text}"
            )
        time.sleep(3)
    pytest.fail(
        f"Trace {trace_id} was not retrievable from {url} within timeout. "
        f"Last status: {last_status}, last body: {last_body!r}"
    )


@pytest.fixture(scope="module")
def trace_payload():
    trace_id = _read_trace_id_from_log()
    return _fetch_trace(trace_id)


def test_log_file_contains_trace_id():
    trace_id = _read_trace_id_from_log()
    assert trace_id, "Trace ID parsed from log file is empty."


def test_trace_contains_observations(trace_payload):
    observations = trace_payload.get("observations")
    assert isinstance(observations, list) and observations, (
        f"Trace response must include a non-empty 'observations' array. Got: {observations!r}"
    )


def test_parent_span_exists_with_run_id_name(trace_payload):
    run_id = _run_id()
    expected_name = f"chat-pipeline-{run_id}"
    observations = trace_payload.get("observations", [])
    spans = [
        o for o in observations
        if str(o.get("type", "")).upper() == "SPAN" and o.get("name") == expected_name
    ]
    assert len(spans) == 1, (
        f"Expected exactly one SPAN observation named {expected_name!r}, "
        f"found {len(spans)} (names seen: {[o.get('name') for o in observations]})."
    )


def test_generation_observation_exists_and_is_child_of_span(trace_payload):
    run_id = _run_id()
    expected_span_name = f"chat-pipeline-{run_id}"
    observations = trace_payload.get("observations", [])
    spans = [
        o for o in observations
        if str(o.get("type", "")).upper() == "SPAN" and o.get("name") == expected_span_name
    ]
    assert len(spans) == 1, "Parent span not found; cannot validate generation parentage."
    span_id = spans[0].get("id")

    generations = [
        o for o in observations
        if str(o.get("type", "")).upper() == "GENERATION" and o.get("name") == "chat-completion"
    ]
    assert len(generations) == 1, (
        f"Expected exactly one GENERATION named 'chat-completion', found {len(generations)} "
        f"(observations: {[(o.get('type'), o.get('name')) for o in observations]})."
    )
    gen = generations[0]
    assert gen.get("parentObservationId") == span_id, (
        f"Generation parentObservationId {gen.get('parentObservationId')!r} does not match "
        f"the SPAN id {span_id!r}."
    )


def _get_generation(trace_payload):
    observations = trace_payload.get("observations", [])
    for o in observations:
        if str(o.get("type", "")).upper() == "GENERATION" and o.get("name") == "chat-completion":
            return o
    pytest.fail("Generation observation named 'chat-completion' not present in trace.")


def test_generation_model_name(trace_payload):
    gen = _get_generation(trace_payload)
    provided = gen.get("providedModelName") or gen.get("model")
    assert provided == "gpt-4o-mini", (
        f"Generation providedModelName must be 'gpt-4o-mini', got {provided!r}."
    )


def test_generation_usage_details(trace_payload):
    gen = _get_generation(trace_payload)
    usage = gen.get("usageDetails") or {}
    for key, expected_value in EXPECTED_USAGE.items():
        assert key in usage, (
            f"usageDetails is missing key {key!r}. Got: {usage!r}"
        )
        actual = usage[key]
        assert int(actual) == expected_value, (
            f"usageDetails[{key!r}] should be {expected_value}, got {actual!r}."
        )


def test_generation_cost_details(trace_payload):
    gen = _get_generation(trace_payload)
    cost = gen.get("costDetails") or {}
    for key, expected_value in EXPECTED_COST.items():
        assert key in cost, (
            f"costDetails is missing key {key!r}. Got: {cost!r}"
        )
        actual = cost[key]
        assert isinstance(actual, (int, float)), (
            f"costDetails[{key!r}] must be numeric, got {type(actual).__name__}: {actual!r}."
        )
        assert math.isclose(float(actual), expected_value, abs_tol=COST_TOLERANCE), (
            f"costDetails[{key!r}] should be {expected_value} (±{COST_TOLERANCE}), "
            f"got {actual!r}."
        )

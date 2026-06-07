import json
import os
import re
import time

import pytest
import requests


PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

TRACE_LINE_RE = re.compile(r"^\s*Trace ID:\s*(\S+)\s*$", re.MULTILINE)
OBS_LINE_RE = re.compile(r"^\s*Observation ID:\s*(\S+)\s*$", re.MULTILINE)


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable is not set; cannot determine the "
        "expected Langfuse resource name suffix."
    )
    return run_id


def _auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, (
        "Langfuse credentials LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY must be "
        "set in the environment for verification."
    )
    return (pk, sk)


def _base_url() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set in the environment for verification."
    return base.rstrip("/")


def _maybe_json(value):
    """Langfuse may return input/output/metadata either as parsed JSON objects
    or as JSON-encoded strings. Normalize to a Python object when possible.
    """
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value


def _get_with_retry(url, auth, attempts=10, sleep_seconds=3.0):
    """Langfuse ingestion is asynchronous; retry GETs that 404 for a while."""
    last_response = None
    for _ in range(attempts):
        resp = requests.get(url, auth=auth, timeout=30)
        last_response = resp
        if resp.status_code == 200:
            return resp
        if resp.status_code != 404:
            return resp
        time.sleep(sleep_seconds)
    return last_response


@pytest.fixture(scope="module")
def log_ids():
    assert os.path.isfile(LOG_PATH), (
        f"Expected the output log file {LOG_PATH} to exist after the task is "
        "run; the executor must record the Langfuse IDs there."
    )
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    trace_matches = TRACE_LINE_RE.findall(content)
    obs_matches = OBS_LINE_RE.findall(content)

    assert len(trace_matches) == 1, (
        f"Expected exactly one 'Trace ID: <trace_id>' line in {LOG_PATH}, "
        f"found {len(trace_matches)}. File contents:\n{content!r}"
    )
    assert len(obs_matches) == 1, (
        f"Expected exactly one 'Observation ID: <observation_id>' line in "
        f"{LOG_PATH}, found {len(obs_matches)}. File contents:\n{content!r}"
    )

    trace_id = trace_matches[0].strip()
    observation_id = obs_matches[0].strip()

    assert trace_id, "Recorded trace ID is empty."
    assert observation_id, "Recorded observation ID is empty."

    return {"trace_id": trace_id, "observation_id": observation_id}


def test_log_file_contains_ids(log_ids):
    # log_ids fixture already enforces this; keep an explicit smoke test
    # so failures here surface a clear message.
    assert log_ids["trace_id"], "Trace ID parsed from log is empty."
    assert log_ids["observation_id"], "Observation ID parsed from log is empty."


def test_event_observation_via_langfuse_api(log_ids):
    run_id = _run_id()
    expected_event_name = f"user-login-event-{run_id}"
    auth = _auth()
    base = _base_url()

    url = f"{base}/api/public/observations/{log_ids['observation_id']}"
    resp = _get_with_retry(url, auth)
    assert resp is not None and resp.status_code == 200, (
        f"GET {url} failed; expected 200, got "
        f"{getattr(resp, 'status_code', 'no-response')} body="
        f"{getattr(resp, 'text', '')!r}. The event observation was not "
        "found in Langfuse Cloud."
    )

    obs = resp.json()

    obs_type = obs.get("type")
    assert obs_type == "EVENT", (
        f"Expected observation type 'EVENT' for the recorded observation, "
        f"got {obs_type!r}. Full observation: {obs!r}"
    )

    name = obs.get("name")
    assert name == expected_event_name, (
        f"Expected observation name {expected_event_name!r}, got {name!r}."
    )

    trace_id_on_obs = obs.get("traceId")
    assert trace_id_on_obs == log_ids["trace_id"], (
        f"Expected observation.traceId to equal the recorded trace ID "
        f"{log_ids['trace_id']!r}, got {trace_id_on_obs!r}."
    )

    input_value = _maybe_json(obs.get("input"))
    assert input_value == {"user_id": "u-42"}, (
        f"Expected event observation input to equal {{'user_id': 'u-42'}}, "
        f"got {input_value!r}."
    )

    output_value = _maybe_json(obs.get("output"))
    assert output_value == {"status": "success"}, (
        f"Expected event observation output to equal {{'status': 'success'}}, "
        f"got {output_value!r}."
    )

    metadata_value = _maybe_json(obs.get("metadata"))
    assert isinstance(metadata_value, dict), (
        f"Expected event observation metadata to be a JSON object, got "
        f"{metadata_value!r}."
    )
    assert metadata_value.get("source") == "auth-service", (
        f"Expected metadata.source == 'auth-service', got "
        f"{metadata_value.get('source')!r}. Full metadata: {metadata_value!r}"
    )
    assert metadata_value.get("region") == "us-east-1", (
        f"Expected metadata.region == 'us-east-1', got "
        f"{metadata_value.get('region')!r}. Full metadata: {metadata_value!r}"
    )


def test_parent_trace_name_via_langfuse_api(log_ids):
    run_id = _run_id()
    expected_trace_name = f"harbor-event-trace-{run_id}"
    auth = _auth()
    base = _base_url()

    url = f"{base}/api/public/traces/{log_ids['trace_id']}"
    resp = _get_with_retry(url, auth)
    assert resp is not None and resp.status_code == 200, (
        f"GET {url} failed; expected 200, got "
        f"{getattr(resp, 'status_code', 'no-response')} body="
        f"{getattr(resp, 'text', '')!r}. The parent trace was not found "
        "in Langfuse Cloud."
    )

    trace = resp.json()
    name = trace.get("name")
    assert name == expected_trace_name, (
        f"Expected the parent Langfuse trace name to be "
        f"{expected_trace_name!r}, got {name!r}."
    )

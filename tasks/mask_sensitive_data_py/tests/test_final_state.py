import json
import os
import re
import time

import pytest
import requests
from requests.auth import HTTPBasicAuth

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

EMAIL_REGEX = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+")
PHONE_REGEX = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]?){13,19}\b")

RUN_ID = os.environ.get("ZEALT_RUN_ID")
LANGFUSE_BASE_URL = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")


def _read_trace_id_from_log():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.findall(r"^Trace ID: ([A-Za-z0-9]+)\s*$", content, flags=re.MULTILINE)
    assert len(matches) >= 1, (
        f"Expected at least one line in {LOG_FILE} matching 'Trace ID: <trace_id>'. "
        f"File content was: {content!r}"
    )
    trace_id = matches[-1].strip()
    assert trace_id, "Captured trace_id is empty."
    return trace_id


def _fetch_trace(trace_id):
    url = f"{LANGFUSE_BASE_URL}/api/public/traces/{trace_id}"
    auth = HTTPBasicAuth(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)

    last_error = None
    delay = 2.0
    deadline = time.time() + 90.0  # up to ~90s of retries to allow ingestion
    while time.time() < deadline:
        try:
            resp = requests.get(url, auth=auth, timeout=20)
        except requests.RequestException as e:
            last_error = e
            time.sleep(delay)
            delay = min(delay * 1.5, 10.0)
            continue

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (401, 403):
            pytest.fail(
                f"Authentication failed when calling {url} "
                f"(status {resp.status_code}). Check LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY."
            )
        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        time.sleep(delay)
        delay = min(delay * 1.5, 10.0)

    pytest.fail(
        f"Failed to fetch trace {trace_id} from {url} within timeout. "
        f"Last error: {last_error}"
    )


def _stringify(value):
    if value is None:
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


@pytest.fixture(scope="module")
def trace_payload():
    assert RUN_ID, "ZEALT_RUN_ID environment variable is not set during verification."
    assert LANGFUSE_PUBLIC_KEY, "LANGFUSE_PUBLIC_KEY is not set during verification."
    assert LANGFUSE_SECRET_KEY, "LANGFUSE_SECRET_KEY is not set during verification."

    trace_id = _read_trace_id_from_log()
    return _fetch_trace(trace_id)


def test_log_file_exists_with_trace_id():
    trace_id = _read_trace_id_from_log()
    assert re.fullmatch(r"[A-Za-z0-9]+", trace_id), (
        f"Trace ID {trace_id!r} contains unexpected characters."
    )


def test_trace_name_matches_run_id(trace_payload):
    expected_name = f"mask-demo-{RUN_ID}"
    actual_name = trace_payload.get("name")
    assert actual_name == expected_name, (
        f"Expected trace.name to be {expected_name!r}, got {actual_name!r}."
    )


def test_trace_input_output_contain_all_redaction_tokens(trace_payload):
    trace_text = (
        _stringify(trace_payload.get("input"))
        + " "
        + _stringify(trace_payload.get("output"))
    )

    for token in ("[REDACTED EMAIL]", "[REDACTED PHONE]", "[REDACTED CREDIT CARD]"):
        assert token in trace_text, (
            f"Expected the redaction token {token!r} to appear in the trace's "
            f"input/output, but it was not found. trace input/output: {trace_text!r}"
        )


def test_trace_input_output_contain_no_raw_pii(trace_payload):
    trace_text = (
        _stringify(trace_payload.get("input"))
        + " "
        + _stringify(trace_payload.get("output"))
    )

    email_match = EMAIL_REGEX.search(trace_text)
    assert email_match is None, (
        f"Raw email PII leaked into the trace input/output: {email_match.group(0)!r}. "
        f"trace input/output: {trace_text!r}"
    )

    phone_match = PHONE_REGEX.search(trace_text)
    assert phone_match is None, (
        f"Raw phone PII leaked into the trace input/output: {phone_match.group(0)!r}. "
        f"trace input/output: {trace_text!r}"
    )

    cc_match = CREDIT_CARD_REGEX.search(trace_text)
    assert cc_match is None, (
        f"Raw credit-card PII leaked into the trace input/output: {cc_match.group(0)!r}. "
        f"trace input/output: {trace_text!r}"
    )


def _find_generation_observation(trace_payload):
    observations = trace_payload.get("observations") or []
    for obs in observations:
        obs_type = (obs.get("type") or "").upper()
        if obs_type == "GENERATION":
            return obs
    return None


def test_generation_observation_exists(trace_payload):
    gen = _find_generation_observation(trace_payload)
    assert gen is not None, (
        "Expected at least one observation with type GENERATION in the trace, "
        f"but none was found. Observations: "
        f"{[(o.get('name'), o.get('type')) for o in (trace_payload.get('observations') or [])]}"
    )


def test_generation_input_output_redacted(trace_payload):
    gen = _find_generation_observation(trace_payload)
    assert gen is not None, "Generation observation missing (already asserted elsewhere)."

    gen_text = (
        _stringify(gen.get("input"))
        + " "
        + _stringify(gen.get("output"))
    )

    redaction_tokens = ("[REDACTED EMAIL]", "[REDACTED PHONE]", "[REDACTED CREDIT CARD]")
    assert any(token in gen_text for token in redaction_tokens), (
        "Expected the generation observation to contain at least one redaction token "
        f"({redaction_tokens}). generation input/output: {gen_text!r}"
    )

    email_match = EMAIL_REGEX.search(gen_text)
    assert email_match is None, (
        f"Raw email PII leaked into the generation observation: {email_match.group(0)!r}."
    )

    phone_match = PHONE_REGEX.search(gen_text)
    assert phone_match is None, (
        f"Raw phone PII leaked into the generation observation: {phone_match.group(0)!r}."
    )

    cc_match = CREDIT_CARD_REGEX.search(gen_text)
    assert cc_match is None, (
        f"Raw credit-card PII leaked into the generation observation: {cc_match.group(0)!r}."
    )

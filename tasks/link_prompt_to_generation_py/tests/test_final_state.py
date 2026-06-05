import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

TRACE_ID_RE = re.compile(r"^Trace ID:\s*([0-9a-fA-F]{32})\s*$", re.MULTILINE)


@pytest.fixture(scope="module")
def langfuse_env():
    base_url = os.environ.get("LANGFUSE_BASE_URL")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert base_url, "LANGFUSE_BASE_URL must be set in the verifier environment."
    assert public_key, "LANGFUSE_PUBLIC_KEY must be set in the verifier environment."
    assert secret_key, "LANGFUSE_SECRET_KEY must be set in the verifier environment."
    assert run_id, "ZEALT_RUN_ID must be set in the verifier environment."
    return {
        "base_url": base_url.rstrip("/"),
        "auth": (public_key, secret_key),
        "run_id": run_id,
        "prompt_name": f"movie-critic-chat-{run_id}",
    }


@pytest.fixture(scope="module")
def trace_id_from_log():
    assert os.path.isfile(LOG_PATH), f"Expected log file at {LOG_PATH}"
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = TRACE_ID_RE.search(content)
    assert match, (
        "output.log must contain a line in the format 'Trace ID: <trace_id>' "
        "with a 32-character hexadecimal trace id. "
        f"Got file content: {content!r}"
    )
    return match.group(1).lower()


def test_output_log_contains_trace_id(trace_id_from_log):
    assert len(trace_id_from_log) == 32, (
        f"Trace ID must be 32 hex characters, got: {trace_id_from_log!r}"
    )
    int(trace_id_from_log, 16)  # must parse as hex


def test_prompt_created_with_production_label(langfuse_env):
    """Verify the production-labeled chat prompt exists with the right template variables."""
    url = f"{langfuse_env['base_url']}/api/public/v2/prompts/{langfuse_env['prompt_name']}"
    resp = requests.get(
        url,
        params={"label": "production"},
        auth=langfuse_env["auth"],
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Expected GET {url}?label=production to return 200, got "
        f"{resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("type") == "chat", (
        f"Prompt type should be 'chat', got: {body.get('type')!r}"
    )
    version = body.get("version")
    assert isinstance(version, int) and version >= 1, (
        f"Prompt version must be a positive integer, got: {version!r}"
    )
    # Verify template variables are present in the messages.
    messages = body.get("prompt")
    assert isinstance(messages, list) and messages, (
        f"Chat prompt must have a non-empty list of messages, got: {messages!r}"
    )
    joined = " ".join(
        m.get("content", "") if isinstance(m, dict) else "" for m in messages
    )
    assert "{{criticlevel}}" in joined, (
        f"Chat prompt must reference the template variable '{{{{criticlevel}}}}'. "
        f"Messages: {messages!r}"
    )
    assert "{{movie}}" in joined, (
        f"Chat prompt must reference the template variable '{{{{movie}}}}'. "
        f"Messages: {messages!r}"
    )


def _get_production_version(langfuse_env):
    url = f"{langfuse_env['base_url']}/api/public/v2/prompts/{langfuse_env['prompt_name']}"
    resp = requests.get(
        url,
        params={"label": "production"},
        auth=langfuse_env["auth"],
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Could not fetch production prompt: {resp.status_code} {resp.text}"
    )
    return resp.json()["version"]


def test_generation_observation_linked_to_prompt(langfuse_env, trace_id_from_log):
    """Verify at least one GENERATION observation on the trace is linked to the prompt."""
    production_version = _get_production_version(langfuse_env)
    url = f"{langfuse_env['base_url']}/api/public/v2/observations"
    params = {
        "traceId": trace_id_from_log,
        "type": "GENERATION",
        "fields": "core,basic,prompt",
        "limit": 50,
    }

    deadline = time.time() + 90  # allow up to 90s for async ingestion
    last_payload = None
    matched = None
    while time.time() < deadline:
        resp = requests.get(
            url, params=params, auth=langfuse_env["auth"], timeout=30
        )
        assert resp.status_code == 200, (
            f"GET observations failed: {resp.status_code} {resp.text}"
        )
        last_payload = resp.json()
        observations = last_payload.get("data") or []
        for obs in observations:
            if (
                obs.get("type") == "GENERATION"
                and obs.get("promptName") == langfuse_env["prompt_name"]
                and obs.get("promptVersion") == production_version
            ):
                matched = obs
                break
        if matched:
            break
        time.sleep(5)

    assert matched is not None, (
        "Expected at least one GENERATION observation on trace "
        f"{trace_id_from_log} linked to prompt "
        f"{langfuse_env['prompt_name']} v{production_version}. "
        f"Last response payload: {last_payload!r}"
    )


def test_trace_persisted(langfuse_env, trace_id_from_log):
    url = f"{langfuse_env['base_url']}/api/public/traces/{trace_id_from_log}"
    deadline = time.time() + 60
    last_status = None
    last_body = None
    while time.time() < deadline:
        resp = requests.get(
            url, params={"fields": "core"}, auth=langfuse_env["auth"], timeout=30
        )
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("id") == trace_id_from_log, (
                f"Trace id mismatch: expected {trace_id_from_log}, got {body.get('id')!r}"
            )
            return
        time.sleep(5)
    pytest.fail(
        f"Trace {trace_id_from_log} not found at {url}. "
        f"Last status: {last_status}, body: {last_body!r}"
    )

import os
import re

import pytest
import requests


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = "/home/user/myproject/output.log"


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set in the verifier env."
    return run_id


def _prompt_name() -> str:
    return f"movie-critic-{_run_id()}"


def _base_url() -> str:
    base = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    )
    return base.rstrip("/")


def _auth():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert public_key and secret_key, (
        "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in the verifier env."
    )
    return (public_key, secret_key)


def _get_prompt(version=None, label=None):
    """Fetch a specific prompt version (or label) via the Langfuse Public API."""
    params = {}
    if version is not None:
        params["version"] = version
    if label is not None:
        params["label"] = label
    url = f"{_base_url()}/api/public/v2/prompts/{_prompt_name()}"
    return requests.get(url, params=params, auth=_auth(), timeout=30)


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."


def test_log_file_contains_prompt_name_line():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    expected = f"Prompt name: {_prompt_name()}"
    assert expected in content, (
        f"Expected log line {expected!r} not found in {LOG_FILE}.\nLog contents:\n{content}"
    )


def test_log_file_contains_promoted_version_line():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r"^Promoted version:\s*2\s*$", re.MULTILINE)
    assert pattern.search(content), (
        f"Expected a line 'Promoted version: 2' in {LOG_FILE}.\nLog contents:\n{content}"
    )


def test_prompt_listed_with_two_versions():
    url = f"{_base_url()}/api/public/v2/prompts"
    resp = requests.get(
        url, params={"name": _prompt_name()}, auth=_auth(), timeout=30
    )
    assert resp.status_code == 200, (
        f"GET /api/public/v2/prompts returned {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    data = body.get("data", [])
    matching = [p for p in data if p.get("name") == _prompt_name()]
    assert len(matching) == 1, (
        f"Expected exactly one prompt named {_prompt_name()!r} in list response, "
        f"got {len(matching)}. Response: {body}"
    )
    meta = matching[0]
    assert meta.get("type") == "text", (
        f"Expected prompt type 'text', got {meta.get('type')!r}. Response: {meta}"
    )
    versions = sorted(meta.get("versions") or [])
    assert versions == [1, 2], (
        f"Expected prompt to have exactly versions [1, 2], got {versions}. Response: {meta}"
    )


def test_version_1_content_and_labels():
    resp = _get_prompt(version=1)
    assert resp.status_code == 200, (
        f"GET prompt version 1 returned {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == 1, (
        f"Expected response version == 1, got {body.get('version')!r}. Body: {body}"
    )
    assert body.get("type") == "text", (
        f"Expected prompt type 'text' for version 1, got {body.get('type')!r}."
    )
    assert body.get("prompt") == "As a {{criticlevel}} critic, do you like {{movie}}?", (
        f"Version 1 prompt content mismatch. Got: {body.get('prompt')!r}"
    )
    labels = body.get("labels") or []
    assert "staging" in labels, (
        f"Expected 'staging' in version 1 labels, got: {labels}"
    )
    assert "production" not in labels, (
        f"Did NOT expect 'production' in version 1 labels (production must be on v2), "
        f"got: {labels}"
    )


def test_version_2_content_and_labels():
    resp = _get_prompt(version=2)
    assert resp.status_code == 200, (
        f"GET prompt version 2 returned {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == 2, (
        f"Expected response version == 2, got {body.get('version')!r}. Body: {body}"
    )
    assert body.get("type") == "text", (
        f"Expected prompt type 'text' for version 2, got {body.get('type')!r}."
    )
    expected = "As an {{criticlevel}} film critic, do you enjoy {{movie}}?"
    assert body.get("prompt") == expected, (
        f"Version 2 prompt content mismatch. Got: {body.get('prompt')!r}"
    )
    labels = body.get("labels") or []
    assert "staging" in labels, (
        f"Expected 'staging' in version 2 labels, got: {labels}"
    )
    assert "production" in labels, (
        f"Expected 'production' in version 2 labels, got: {labels}"
    )


def test_production_label_points_to_version_2():
    resp = _get_prompt(label="production")
    assert resp.status_code == 200, (
        f"GET prompt by label 'production' returned {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == 2, (
        f"Expected the 'production' label to currently point to version 2, "
        f"got version {body.get('version')!r}. Body: {body}"
    )

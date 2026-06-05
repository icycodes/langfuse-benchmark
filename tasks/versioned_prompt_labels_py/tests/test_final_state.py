import json
import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/langfuse_task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")


def _api_auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set."
    return (pk, sk)


def _base_url():
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set."
    return base.rstrip("/")


def _run_id():
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable must be set."
    return rid


def _expected_prompt_name():
    return f"movie-critic-chat-{_run_id()}"


def _read_log_text():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parse_log_versions(log_text):
    staging_match = re.search(r"^\s*Staging version:\s*(\d+)\s*$", log_text, re.MULTILINE)
    production_match = re.search(
        r"^\s*Production version:\s*(\d+)\s*$", log_text, re.MULTILINE
    )
    assert staging_match, (
        "Expected log file to contain a line 'Staging version: <integer>'."
    )
    assert production_match, (
        "Expected log file to contain a line 'Production version: <integer>'."
    )
    return int(staging_match.group(1)), int(production_match.group(1))


def _fetch_prompt(label=None, version=None):
    params = {}
    if label is not None:
        params["label"] = label
    if version is not None:
        params["version"] = version
    url = f"{_base_url()}/api/public/v2/prompts/{_expected_prompt_name()}"
    resp = requests.get(url, params=params, auth=_api_auth(), timeout=30)
    return resp


def _concat_chat_content(prompt_body):
    assert isinstance(prompt_body, list), (
        f"Expected chat prompt body to be a list of messages, got {type(prompt_body).__name__}."
    )
    parts = []
    for msg in prompt_body:
        assert isinstance(msg, dict), (
            f"Expected each chat message to be a dict, got {type(msg).__name__}."
        )
        content = msg.get("content")
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def _collect_roles(prompt_body):
    return [msg.get("role") for msg in prompt_body if isinstance(msg, dict)]


def test_log_file_contains_expected_prompt_name():
    log_text = _read_log_text()
    expected_line = f"Prompt name: {_expected_prompt_name()}"
    assert expected_line in log_text, (
        f"Expected log file to contain line '{expected_line}'. Got:\n{log_text}"
    )


def test_log_file_versions_are_sequential():
    log_text = _read_log_text()
    staging_v, production_v = _parse_log_versions(log_text)
    assert production_v == staging_v + 1, (
        f"Expected production version ({production_v}) to be exactly staging version ({staging_v}) + 1, "
        "because production was created after staging."
    )


def test_production_prompt_returned_via_api():
    log_text = _read_log_text()
    _, production_v = _parse_log_versions(log_text)

    resp = _fetch_prompt(label="production")
    assert resp.status_code == 200, (
        f"Expected GET prompt by label='production' to return 200, "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()

    assert body.get("type") == "chat", (
        f"Expected production prompt to have type='chat', got: {body.get('type')!r}."
    )
    assert body.get("version") == production_v, (
        f"Expected production prompt version ({body.get('version')}) to equal "
        f"the version recorded in the log ({production_v})."
    )
    labels = body.get("labels") or []
    assert "production" in labels, (
        f"Expected production prompt labels to include 'production', got: {labels}."
    )

    chat_body = body.get("prompt")
    roles = _collect_roles(chat_body)
    assert "system" in roles, (
        f"Expected production chat prompt to contain a 'system' role message, got roles: {roles}."
    )
    assert "user" in roles, (
        f"Expected production chat prompt to contain a 'user' role message, got roles: {roles}."
    )

    combined = _concat_chat_content(chat_body)
    for var in ("{{criticlevel}}", "{{movie}}", "{{genre}}"):
        assert var in combined, (
            f"Expected production chat prompt content to reference variable {var}. "
            f"Got combined content:\n{combined}"
        )


def test_staging_prompt_returned_via_api():
    log_text = _read_log_text()
    staging_v, _ = _parse_log_versions(log_text)

    resp = _fetch_prompt(label="staging")
    assert resp.status_code == 200, (
        f"Expected GET prompt by label='staging' to return 200, "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()

    assert body.get("type") == "chat", (
        f"Expected staging prompt to have type='chat', got: {body.get('type')!r}."
    )
    assert body.get("version") == staging_v, (
        f"Expected staging prompt version ({body.get('version')}) to equal "
        f"the version recorded in the log ({staging_v})."
    )

    labels = body.get("labels") or []
    assert "staging" in labels, (
        f"Expected staging prompt labels to include 'staging', got: {labels}."
    )
    assert "production" not in labels, (
        f"Expected staging prompt labels to NOT include 'production' (it must "
        f"have moved to the newer version), got: {labels}."
    )

    chat_body = body.get("prompt")
    roles = _collect_roles(chat_body)
    assert "system" in roles, (
        f"Expected staging chat prompt to contain a 'system' role message, got roles: {roles}."
    )
    assert "user" in roles, (
        f"Expected staging chat prompt to contain a 'user' role message, got roles: {roles}."
    )

    combined = _concat_chat_content(chat_body)
    for var in ("{{criticlevel}}", "{{movie}}"):
        assert var in combined, (
            f"Expected staging chat prompt content to reference variable {var}. "
            f"Got combined content:\n{combined}"
        )


def test_default_label_serves_production_version():
    log_text = _read_log_text()
    _, production_v = _parse_log_versions(log_text)

    resp = _fetch_prompt()  # no label → defaults to "production"
    assert resp.status_code == 200, (
        f"Expected GET prompt with no label to return 200 (defaulting to production), "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == production_v, (
        f"Expected the default (no-label) prompt fetch to return the production version "
        f"({production_v}), but got version {body.get('version')}."
    )

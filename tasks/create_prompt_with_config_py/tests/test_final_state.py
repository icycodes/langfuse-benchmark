import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")


@pytest.fixture(scope="module")
def run_id():
    value = os.environ.get("ZEALT_RUN_ID", "").strip()
    assert value, "ZEALT_RUN_ID environment variable is not set."
    return value


@pytest.fixture(scope="module")
def expected_prompt_name(run_id):
    return f"invoice-extractor-{run_id}"


@pytest.fixture(scope="module")
def langfuse_auth():
    public = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    base = os.environ.get("LANGFUSE_BASE_URL", "").strip().rstrip("/")
    assert public, "LANGFUSE_PUBLIC_KEY env var not set."
    assert secret, "LANGFUSE_SECRET_KEY env var not set."
    assert base, "LANGFUSE_BASE_URL env var not set."
    return public, secret, base


@pytest.fixture(scope="module")
def log_contents():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task ran."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def fetched_prompt(langfuse_auth, expected_prompt_name):
    public, secret, base = langfuse_auth
    url = f"{base}/api/public/v2/prompts/{expected_prompt_name}"
    response = requests.get(url, auth=(public, secret), timeout=30)
    assert response.status_code == 200, (
        f"Expected HTTP 200 when fetching prompt {expected_prompt_name!r} from "
        f"{url}, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    return body


# ----- Log file checks -----

def test_log_contains_prompt_name(log_contents, expected_prompt_name):
    line = f"Prompt name: {expected_prompt_name}"
    assert line in log_contents, (
        f"Expected log file to contain a line {line!r}. "
        f"Log contents:\n{log_contents}"
    )


def test_log_contains_prompt_version(log_contents):
    match = re.search(r"^Prompt version:\s*(\d+)\s*$", log_contents, re.MULTILINE)
    assert match is not None, (
        "Expected log file to contain a line matching "
        "'Prompt version: <integer>'. "
        f"Log contents:\n{log_contents}"
    )
    assert int(match.group(1)) >= 1, (
        f"Expected prompt version to be >= 1, got {match.group(1)}."
    )


def test_log_contains_prompt_type(log_contents):
    assert "Prompt type: chat" in log_contents, (
        "Expected log file to contain 'Prompt type: chat'. "
        f"Log contents:\n{log_contents}"
    )


def test_log_contains_config_keys(log_contents):
    match = re.search(r"^Config keys:\s*(.+)\s*$", log_contents, re.MULTILINE)
    assert match is not None, (
        "Expected log file to contain a line starting with 'Config keys:'. "
        f"Log contents:\n{log_contents}"
    )
    keys = {k.strip() for k in match.group(1).split(",")}
    expected = {"model", "temperature", "response_format"}
    assert expected.issubset(keys), (
        f"Expected log 'Config keys' line to include {expected}, got {keys}."
    )


def test_log_contains_labels(log_contents):
    match = re.search(r"^Labels:\s*(.+)\s*$", log_contents, re.MULTILINE)
    assert match is not None, (
        "Expected log file to contain a line starting with 'Labels:'. "
        f"Log contents:\n{log_contents}"
    )
    labels = {l.strip() for l in match.group(1).split(",")}
    assert {"production", "staging"}.issubset(labels), (
        f"Expected log 'Labels' line to include both 'production' and "
        f"'staging', got {labels}."
    )


# ----- API verification -----

def test_api_prompt_name_matches(fetched_prompt, expected_prompt_name):
    assert fetched_prompt.get("name") == expected_prompt_name, (
        f"Expected fetched prompt name to be {expected_prompt_name!r}, "
        f"got {fetched_prompt.get('name')!r}."
    )


def test_api_prompt_type_is_chat(fetched_prompt):
    # The public API response should expose a "type" discriminator equal to
    # "chat" for chat prompts. Be tolerant if absent and fall back to checking
    # that `prompt` is a list of chat messages.
    prompt_type = fetched_prompt.get("type")
    if prompt_type is not None:
        assert prompt_type == "chat", (
            f"Expected prompt type to be 'chat', got {prompt_type!r}."
        )
    messages = fetched_prompt.get("prompt")
    assert isinstance(messages, list) and len(messages) >= 1, (
        "Expected chat prompt body to be a non-empty list of messages, "
        f"got: {messages!r}"
    )
    # Each message should have a 'role' and 'content' field (chat messages),
    # placeholder messages have a 'name' field.
    for msg in messages:
        assert isinstance(msg, dict), (
            f"Expected each message to be a dict, got {type(msg).__name__}: {msg!r}"
        )


def test_api_prompt_has_mustache_variable(fetched_prompt):
    messages = fetched_prompt.get("prompt", [])
    found = False
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str) and re.search(r"\{\{\s*[\w\.\-]+\s*\}\}", content):
            found = True
            break
    assert found, (
        "Expected at least one chat message content to contain a "
        "'{{variable}}' Mustache-style placeholder. "
        f"Messages: {messages!r}"
    )


def test_api_config_has_required_keys(fetched_prompt):
    config = fetched_prompt.get("config")
    assert isinstance(config, dict), (
        f"Expected prompt 'config' to be a JSON object, got: {type(config).__name__}"
    )
    for key in ("model", "temperature", "response_format"):
        assert key in config, (
            f"Expected prompt config to contain key {key!r}, "
            f"got keys: {list(config.keys())}"
        )
    response_format = config["response_format"]
    assert isinstance(response_format, dict), (
        f"Expected 'response_format' to be a JSON object, "
        f"got: {type(response_format).__name__}"
    )
    assert "json_schema" in response_format, (
        f"Expected 'response_format' to contain a 'json_schema' key, "
        f"got keys: {list(response_format.keys())}"
    )


def test_api_prompt_has_both_labels(fetched_prompt):
    labels = fetched_prompt.get("labels")
    assert isinstance(labels, list), (
        f"Expected 'labels' to be a list, got: {type(labels).__name__}"
    )
    label_set = set(labels)
    for required in ("production", "staging"):
        assert required in label_set, (
            f"Expected prompt labels to include {required!r}, got: {labels}"
        )


def test_api_version_matches_log(fetched_prompt, log_contents):
    api_version = fetched_prompt.get("version")
    assert isinstance(api_version, int) and api_version >= 1, (
        f"Expected prompt version from API to be an integer >= 1, "
        f"got: {api_version!r}"
    )
    match = re.search(r"^Prompt version:\s*(\d+)\s*$", log_contents, re.MULTILINE)
    assert match is not None, "Log does not contain a 'Prompt version:' line."
    log_version = int(match.group(1))
    assert api_version == log_version, (
        f"Prompt version in log file ({log_version}) does not match the "
        f"version returned by the API ({api_version})."
    )


def test_api_fetch_by_staging_label(langfuse_auth, expected_prompt_name, fetched_prompt):
    public, secret, base = langfuse_auth
    url = f"{base}/api/public/v2/prompts/{expected_prompt_name}"
    response = requests.get(
        url, params={"label": "staging"}, auth=(public, secret), timeout=30
    )
    assert response.status_code == 200, (
        "Expected HTTP 200 when fetching prompt by label=staging, "
        f"got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert "staging" in (body.get("labels") or []), (
        f"Expected returned prompt for label=staging to include 'staging' "
        f"in its labels list, got: {body.get('labels')}"
    )
    assert body.get("version") == fetched_prompt.get("version"), (
        "Expected version returned for label=staging to match the production "
        f"version. staging={body.get('version')!r}, "
        f"production={fetched_prompt.get('version')!r}"
    )

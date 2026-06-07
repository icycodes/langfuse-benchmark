import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")


def _run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set during verification."
    return run_id


def _expected_prompt_name():
    return f"chat-prompt-cli-{_run_id()}"


def _read_log():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parse_log_fields():
    text = _read_log()
    name_match = re.search(r"^Prompt name:\s*(\S+)\s*$", text, re.MULTILINE)
    version_match = re.search(r"^Prompt version:\s*(\d+)\s*$", text, re.MULTILINE)
    assert name_match, (
        f"Log file {LOG_FILE} does not contain a line matching "
        f"'Prompt name: <name>'. Contents:\n{text}"
    )
    assert version_match, (
        f"Log file {LOG_FILE} does not contain a line matching "
        f"'Prompt version: <integer>'. Contents:\n{text}"
    )
    return name_match.group(1), int(version_match.group(1))


def _api_base():
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL environment variable is not set during verification."
    return base.rstrip("/")


def _auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, "LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY must be set during verification."
    return (pk, sk)


def _get_prompt(name, *, version=None, label=None):
    params = {}
    if version is not None:
        params["version"] = version
    if label is not None:
        params["label"] = label
    # Use 'resolve=false' to inspect the raw stored prompt content (avoids cache surprises).
    params["resolve"] = "false"
    url = f"{_api_base()}/api/public/v2/prompts/{name}"
    resp = requests.get(url, auth=_auth(), params=params, timeout=30)
    return resp


# ---------------------------------------------------------------------------
# Log file content checks
# ---------------------------------------------------------------------------


def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."


def test_log_contains_expected_prompt_name():
    name, _ = _parse_log_fields()
    expected = _expected_prompt_name()
    assert name == expected, (
        f"Logged prompt name {name!r} does not match expected run-id-scoped "
        f"name {expected!r}."
    )


def test_log_contains_prompt_version_integer():
    _, version = _parse_log_fields()
    assert version >= 1, f"Expected prompt version to be a positive integer, got {version}."


# ---------------------------------------------------------------------------
# Langfuse public API checks
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fetched_prompt():
    name, version = _parse_log_fields()
    resp = _get_prompt(name, version=version)
    assert resp.status_code == 200, (
        f"GET /api/public/v2/prompts/{name}?version={version} returned "
        f"HTTP {resp.status_code}. Body: {resp.text}"
    )
    return resp.json()


def test_prompt_name_matches(fetched_prompt):
    expected = _expected_prompt_name()
    assert fetched_prompt.get("name") == expected, (
        f"Prompt name returned by Langfuse is {fetched_prompt.get('name')!r}, "
        f"expected {expected!r}."
    )


def test_prompt_type_is_chat(fetched_prompt):
    assert fetched_prompt.get("type") == "chat", (
        f"Prompt type returned by Langfuse is {fetched_prompt.get('type')!r}, "
        f"expected 'chat'."
    )


def test_prompt_version_matches_log(fetched_prompt):
    _, expected_version = _parse_log_fields()
    assert fetched_prompt.get("version") == expected_version, (
        f"Prompt version returned by Langfuse is {fetched_prompt.get('version')!r}, "
        f"expected {expected_version}."
    )


def test_prompt_messages_structure(fetched_prompt):
    messages = fetched_prompt.get("prompt")
    assert isinstance(messages, list), (
        f"Expected 'prompt' field to be a list of chat messages, got {type(messages).__name__}."
    )
    assert len(messages) == 2, (
        f"Expected exactly 2 chat messages (system + user), got {len(messages)}: {messages!r}"
    )

    system_msg, user_msg = messages[0], messages[1]
    assert system_msg.get("role") == "system", (
        f"Expected first message role 'system', got {system_msg.get('role')!r}."
    )
    assert isinstance(system_msg.get("content"), str) and system_msg["content"].strip(), (
        f"Expected first message to have non-empty string content, got {system_msg.get('content')!r}."
    )

    assert user_msg.get("role") == "user", (
        f"Expected second message role 'user', got {user_msg.get('role')!r}."
    )
    user_content = user_msg.get("content")
    assert isinstance(user_content, str) and "{{topic}}" in user_content, (
        f"Expected second message content to include the '{{{{topic}}}}' template "
        f"variable, got {user_content!r}."
    )


def test_prompt_has_both_labels(fetched_prompt):
    labels = fetched_prompt.get("labels") or []
    assert isinstance(labels, list), f"Expected 'labels' to be a list, got {labels!r}."
    for required in ("production", "staging"):
        assert required in labels, (
            f"Expected label {required!r} on the created prompt, got labels={labels!r}."
        )


def test_prompt_has_required_tag(fetched_prompt):
    tags = fetched_prompt.get("tags") or []
    assert isinstance(tags, list), f"Expected 'tags' to be a list, got {tags!r}."
    assert "cli-demo" in tags, (
        f"Expected tag 'cli-demo' on the created prompt, got tags={tags!r}."
    )


def test_prompt_has_non_empty_commit_message(fetched_prompt):
    commit = fetched_prompt.get("commitMessage")
    assert isinstance(commit, str) and commit.strip(), (
        f"Expected non-empty commitMessage on the created prompt, got {commit!r}."
    )


def test_production_label_resolves_to_same_version():
    name, version = _parse_log_fields()
    resp = _get_prompt(name, label="production")
    assert resp.status_code == 200, (
        f"GET prompt by production label failed with HTTP {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == version, (
        f"Fetching prompt by label='production' returned version {body.get('version')}, "
        f"expected {version}."
    )


def test_staging_label_resolves_to_same_version():
    name, version = _parse_log_fields()
    resp = _get_prompt(name, label="staging")
    assert resp.status_code == 200, (
        f"GET prompt by staging label failed with HTTP {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == version, (
        f"Fetching prompt by label='staging' returned version {body.get('version')}, "
        f"expected {version}."
    )

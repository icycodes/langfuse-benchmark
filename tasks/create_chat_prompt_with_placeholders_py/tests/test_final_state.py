import json
import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_COMPILED_PROMPT = [
    {"role": "system", "content": "You are an expert movie critic"},
    {"role": "user", "content": "I love Ron Fricke movies like Baraka"},
    {"role": "user", "content": "Also, the Korean movie Memories of a Murderer"},
    {"role": "user", "content": "What should I watch next?"},
]


@pytest.fixture(scope="session")
def run_id():
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "ZEALT_RUN_ID environment variable must be set for verification."
    return value


@pytest.fixture(scope="session")
def expected_prompt_name(run_id):
    return f"movie-critic-chat-{run_id}"


@pytest.fixture(scope="session")
def langfuse_auth():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = os.environ.get("LANGFUSE_BASE_URL")
    assert public_key, "LANGFUSE_PUBLIC_KEY must be set for verification."
    assert secret_key, "LANGFUSE_SECRET_KEY must be set for verification."
    assert base_url, "LANGFUSE_BASE_URL must be set for verification."
    return public_key, secret_key, base_url.rstrip("/")


@pytest.fixture(scope="session")
def log_contents():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task completes."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fp:
        return fp.read()


def _normalize_chat_message(msg):
    """Drop optional fields (e.g. discriminator type) for content comparison."""
    if not isinstance(msg, dict):
        return msg
    return {"role": msg.get("role"), "content": msg.get("content")}


def test_log_file_records_prompt_name(log_contents, expected_prompt_name):
    pattern = re.compile(r"^Prompt name:\s*(\S+)\s*$", re.MULTILINE)
    match = pattern.search(log_contents)
    assert match, (
        f"Expected a line like 'Prompt name: <name>' in {LOG_FILE}. "
        f"Got:\n{log_contents}"
    )
    assert match.group(1) == expected_prompt_name, (
        f"Expected prompt name '{expected_prompt_name}' in log file, "
        f"got '{match.group(1)}'."
    )


def test_log_file_records_compiled_prompt(log_contents):
    pattern = re.compile(r"^Compiled prompt:\s*(\[.*\])\s*$", re.MULTILINE)
    match = pattern.search(log_contents)
    assert match, (
        f"Expected a line like 'Compiled prompt: <json-array>' in {LOG_FILE}. "
        f"Got:\n{log_contents}"
    )
    try:
        compiled = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"Could not parse the JSON payload after 'Compiled prompt:'. "
            f"Error: {exc}. Payload: {match.group(1)!r}"
        )
    assert isinstance(compiled, list), (
        f"Expected the compiled prompt to be a JSON list, got {type(compiled).__name__}."
    )
    assert len(compiled) == len(EXPECTED_COMPILED_PROMPT), (
        f"Expected the compiled prompt to contain "
        f"{len(EXPECTED_COMPILED_PROMPT)} messages, got {len(compiled)}: {compiled}"
    )
    normalized = [_normalize_chat_message(m) for m in compiled]
    assert normalized == EXPECTED_COMPILED_PROMPT, (
        f"Compiled prompt did not match the expected sequence.\n"
        f"Expected: {EXPECTED_COMPILED_PROMPT}\n"
        f"Got:      {normalized}"
    )


def test_prompt_exists_on_langfuse_api(langfuse_auth, expected_prompt_name):
    public_key, secret_key, base_url = langfuse_auth
    url = f"{base_url}/api/public/v2/prompts/{expected_prompt_name}"
    response = requests.get(
        url,
        params={"label": "production"},
        auth=(public_key, secret_key),
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET {url}?label=production returned status {response.status_code}: "
        f"{response.text}"
    )
    body = response.json()
    assert body.get("name") == expected_prompt_name, (
        f"Expected prompt name '{expected_prompt_name}' from API, got '{body.get('name')}'."
    )
    assert body.get("type") == "chat", (
        f"Expected prompt type 'chat' from API, got '{body.get('type')}'."
    )
    labels = body.get("labels") or []
    assert "production" in labels, (
        f"Expected 'production' label on prompt, got labels={labels}."
    )

    messages = body.get("prompt")
    assert isinstance(messages, list), (
        f"Expected the prompt payload to be a list, got {type(messages).__name__}: {messages}"
    )
    assert len(messages) == 3, (
        f"Expected exactly 3 entries in the prompt payload, got {len(messages)}: {messages}"
    )

    first = messages[0]
    assert isinstance(first, dict), f"First entry should be a dict, got {first!r}."
    assert first.get("role") == "system", (
        f"First entry should be a system message, got role={first.get('role')!r}."
    )
    assert first.get("content") == "You are an {{criticlevel}} movie critic", (
        "First entry should contain the templated system content "
        f"'You are an {{{{criticlevel}}}} movie critic'. Got content={first.get('content')!r}."
    )

    second = messages[1]
    assert isinstance(second, dict), f"Second entry should be a dict, got {second!r}."
    assert second.get("type") == "placeholder", (
        f"Second entry should be a placeholder (type='placeholder'), got type={second.get('type')!r}."
    )
    assert second.get("name") == "chat_history", (
        f"Second entry should be the 'chat_history' placeholder, got name={second.get('name')!r}."
    )

    third = messages[2]
    assert isinstance(third, dict), f"Third entry should be a dict, got {third!r}."
    assert third.get("role") == "user", (
        f"Third entry should be a user message, got role={third.get('role')!r}."
    )
    assert third.get("content") == "What should I watch next?", (
        f"Third entry should contain 'What should I watch next?'. Got content={third.get('content')!r}."
    )

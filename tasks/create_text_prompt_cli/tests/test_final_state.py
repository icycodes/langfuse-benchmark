import json
import os
import re
import urllib.parse

import pytest
import requests

PROJECT_DIR = "/home/user/langfuse-task"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_PROMPT_TEXT = "Hello {{name}}, welcome to {{service}}! Your plan is {{plan}}."
EXPECTED_COMMIT_MSG = "Initial onboarding template"
EXPECTED_MODEL = "gpt-4o-mini"
EXPECTED_TEMPERATURE = 0.5
EXPECTED_LABELS = {"production", "staging"}
EXPECTED_TAG = "onboarding"

LOG_LINE_RE = re.compile(
    r"Prompt created: name=(?P<name>welcome-email-[A-Za-z0-9_-]+) version=(?P<version>\d+)"
)


def _run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is required for verification."
    return run_id


def _expected_prompt_name():
    return f"welcome-email-{_run_id()}"


def _read_log_line():
    assert os.path.isfile(LOG_PATH), f"Expected log file {LOG_PATH} to exist after the task."
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = None
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        m = LOG_LINE_RE.search(line)
        if m:
            match = m
            break
    assert match is not None, (
        f"Expected a line matching 'Prompt created: name=<name> version=<n>' in {LOG_PATH}, "
        f"got contents:\n{content}"
    )
    return match.group("name"), int(match.group("version"))


def _fetch_prompt(name, version):
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    encoded_name = urllib.parse.quote(name, safe="")
    url = f"{base_url}/api/public/v2/prompts/{encoded_name}"
    response = requests.get(
        url,
        params={"version": version},
        auth=(public_key, secret_key),
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET {url} returned status {response.status_code}: {response.text}"
    )
    return response.json()


@pytest.fixture(scope="module")
def created_prompt_log():
    return _read_log_line()


@pytest.fixture(scope="module")
def fetched_prompt(created_prompt_log):
    name, version = created_prompt_log
    return _fetch_prompt(name, version), name, version


def test_log_file_records_prompt_name_matches_run_id(created_prompt_log):
    name, _version = created_prompt_log
    assert name == _expected_prompt_name(), (
        f"Expected prompt name in log to be {_expected_prompt_name()!r}, got {name!r}."
    )


def test_prompt_exists_via_api(fetched_prompt):
    prompt_obj, name, version = fetched_prompt
    assert prompt_obj.get("name") == name, (
        f"Langfuse API returned prompt name {prompt_obj.get('name')!r}; expected {name!r}."
    )
    assert prompt_obj.get("version") == version, (
        f"Langfuse API returned version {prompt_obj.get('version')!r}; expected {version!r}."
    )


def test_prompt_is_text_type(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    assert prompt_obj.get("type") == "text", (
        f"Expected prompt type 'text', got {prompt_obj.get('type')!r}."
    )


def test_prompt_body_matches(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    body = prompt_obj.get("prompt")
    assert body == EXPECTED_PROMPT_TEXT, (
        f"Expected prompt body {EXPECTED_PROMPT_TEXT!r}, got {body!r}."
    )


def test_prompt_labels_include_production_and_staging(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    labels = prompt_obj.get("labels") or []
    assert isinstance(labels, list), f"Expected labels to be a list, got {type(labels).__name__}."
    label_set = set(labels)
    missing = EXPECTED_LABELS - label_set
    assert not missing, (
        f"Expected labels to include {sorted(EXPECTED_LABELS)}, missing {sorted(missing)}; "
        f"got {labels!r}."
    )


def test_prompt_tags_include_onboarding(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    tags = prompt_obj.get("tags") or []
    assert isinstance(tags, list), f"Expected tags to be a list, got {type(tags).__name__}."
    assert EXPECTED_TAG in tags, (
        f"Expected tag {EXPECTED_TAG!r} in tags; got {tags!r}."
    )


def test_prompt_commit_message_matches(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    commit_msg = prompt_obj.get("commitMessage")
    assert commit_msg == EXPECTED_COMMIT_MSG, (
        f"Expected commitMessage {EXPECTED_COMMIT_MSG!r}, got {commit_msg!r}."
    )


def test_prompt_config_contains_model_and_temperature(fetched_prompt):
    prompt_obj, _name, _version = fetched_prompt
    config = prompt_obj.get("config")
    # The config may be returned as a JSON object or a JSON-encoded string depending on
    # how the executor passes it through the CLI; accept either form.
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError as e:
            pytest.fail(f"Expected config to be JSON object or JSON string; got {config!r}: {e}")
    assert isinstance(config, dict), (
        f"Expected config to be a dict, got {type(config).__name__}: {config!r}."
    )
    assert config.get("model") == EXPECTED_MODEL, (
        f"Expected config.model={EXPECTED_MODEL!r}, got {config.get('model')!r}."
    )
    actual_temp = config.get("temperature")
    assert actual_temp is not None, f"Expected config.temperature to be set; got {config!r}."
    assert float(actual_temp) == pytest.approx(EXPECTED_TEMPERATURE), (
        f"Expected config.temperature={EXPECTED_TEMPERATURE}, got {actual_temp!r}."
    )

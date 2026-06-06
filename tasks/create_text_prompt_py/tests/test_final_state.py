import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

PROMPT_NAME_RE = re.compile(r"^Prompt Name:\s*(\S+)\s*$", re.MULTILINE)
PROMPT_VERSION_RE = re.compile(r"^Prompt Version:\s*(\d+)\s*$", re.MULTILINE)


def _run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set."
    return run_id


def _expected_prompt_name():
    return f"movie-critic-text-{_run_id()}"


def _read_log_text():
    assert os.path.isfile(LOG_FILE), f"Expected log file at {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    assert text.strip(), f"Log file {LOG_FILE} is empty."
    return text


def _logged_prompt_name():
    text = _read_log_text()
    match = PROMPT_NAME_RE.search(text)
    assert match, (
        f"Log file {LOG_FILE} must contain a line matching 'Prompt Name: <name>'. "
        f"Content was: {text!r}"
    )
    return match.group(1)


def _logged_prompt_version():
    text = _read_log_text()
    match = PROMPT_VERSION_RE.search(text)
    assert match, (
        f"Log file {LOG_FILE} must contain a line matching 'Prompt Version: <integer>'. "
        f"Content was: {text!r}"
    )
    return int(match.group(1))


def _api_get_prompt(name, label=None, version=None):
    base_url = os.environ["LANGFUSE_BASE_URL"].rstrip("/")
    auth = (
        os.environ["LANGFUSE_PUBLIC_KEY"],
        os.environ["LANGFUSE_SECRET_KEY"],
    )
    params = {}
    if label is not None:
        params["label"] = label
    if version is not None:
        params["version"] = version
    url = f"{base_url}/api/public/v2/prompts/{name}"
    return requests.get(url, auth=auth, params=params, timeout=30)


def test_log_file_contains_expected_prompt_name():
    expected = _expected_prompt_name()
    logged = _logged_prompt_name()
    assert logged == expected, (
        f"Expected logged prompt name to be '{expected}', got '{logged}'."
    )


def test_log_file_contains_prompt_version():
    version = _logged_prompt_version()
    assert version >= 1, f"Logged prompt version must be >= 1, got {version}."


@pytest.fixture(scope="module")
def prompt_from_api():
    response = _api_get_prompt(_expected_prompt_name(), label="production")
    assert response.status_code == 200, (
        f"Langfuse API call to fetch prompt with label=production failed. "
        f"Status: {response.status_code}, body: {response.text}"
    )
    return response.json()


def test_api_prompt_name_matches(prompt_from_api):
    assert prompt_from_api.get("name") == _expected_prompt_name(), (
        f"Expected API prompt 'name' to equal '{_expected_prompt_name()}', got "
        f"'{prompt_from_api.get('name')}'."
    )


def test_api_prompt_is_text_type(prompt_from_api):
    assert prompt_from_api.get("type") == "text", (
        f"Expected API prompt 'type' to be 'text', got '{prompt_from_api.get('type')}'."
    )


def test_api_prompt_template_has_variable_placeholder(prompt_from_api):
    template = prompt_from_api.get("prompt")
    assert isinstance(template, str) and template.strip(), (
        f"Expected non-empty string in 'prompt' field, got: {template!r}"
    )
    assert "{{" in template, (
        f"Expected the prompt template to contain at least one '{{{{variable}}}}' placeholder. "
        f"Template was: {template!r}"
    )


def test_api_prompt_version_matches_log(prompt_from_api):
    logged_version = _logged_prompt_version()
    assert prompt_from_api.get("version") == logged_version, (
        f"Expected API prompt 'version' to equal the logged version {logged_version}, "
        f"got {prompt_from_api.get('version')}."
    )


def test_api_prompt_has_production_label(prompt_from_api):
    labels = prompt_from_api.get("labels") or []
    assert "production" in labels, (
        f"Expected prompt labels to contain 'production', got: {labels}"
    )


def test_api_prompt_has_non_empty_config(prompt_from_api):
    config = prompt_from_api.get("config")
    assert isinstance(config, dict) and len(config) > 0, (
        f"Expected prompt 'config' to be a non-empty object, got: {config!r}"
    )


def test_api_prompt_has_at_least_one_tag(prompt_from_api):
    tags = prompt_from_api.get("tags") or []
    assert isinstance(tags, list) and len(tags) >= 1, (
        f"Expected prompt 'tags' to be a list with at least one tag, got: {tags!r}"
    )

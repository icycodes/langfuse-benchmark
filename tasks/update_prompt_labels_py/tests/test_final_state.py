import os
import re

import pytest
import requests
from requests.auth import HTTPBasicAuth

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")

PROMOTED_LINE_RE = re.compile(r"^Promoted version:\s*2\s*labels:\s*(.+)$", re.MULTILINE)
PREVIOUS_LINE_RE = re.compile(r"^Previous version:\s*1\s*labels:\s*(.+)$", re.MULTILINE)


def _get_run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def _langfuse_base_url() -> str:
    return os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")


def _langfuse_auth() -> HTTPBasicAuth:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    assert public_key and secret_key, (
        "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set for verification."
    )
    return HTTPBasicAuth(public_key, secret_key)


def _fetch_prompt_version(prompt_name: str, version: int) -> dict:
    url = f"{_langfuse_base_url()}/api/public/v2/prompts/{prompt_name}"
    response = requests.get(
        url,
        params={"version": version},
        auth=_langfuse_auth(),
        timeout=30,
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200 fetching version {version} of '{prompt_name}', "
        f"got {response.status_code}: {response.text}"
    )
    return response.json()


def _labels_excluding_latest(labels) -> list:
    return sorted(label for label in (labels or []) if label != "latest")


def _expected_log_value(labels_sorted: list) -> str:
    return ",".join(labels_sorted) if labels_sorted else "none"


@pytest.fixture(scope="module")
def log_contents() -> str:
    assert os.path.isfile(LOG_PATH), (
        f"Log file '{LOG_PATH}' does not exist. The agent must write evidence of the promotion."
    )
    with open(LOG_PATH) as f:
        return f.read()


@pytest.fixture(scope="module")
def prompt_name() -> str:
    run_id = _get_run_id()
    return f"movie-critic-{run_id}"


def test_version_2_has_production_and_approved_labels(prompt_name):
    payload = _fetch_prompt_version(prompt_name, 2)
    labels = payload.get("labels") or []
    label_set = {label for label in labels if label != "latest"}
    assert label_set == {"production", "approved"}, (
        f"Expected version 2 of '{prompt_name}' to carry exactly the labels "
        f"{{'production', 'approved'}} (excluding 'latest'). Got: {sorted(label_set)}"
    )


def test_version_1_no_longer_has_production_label(prompt_name):
    payload = _fetch_prompt_version(prompt_name, 1)
    labels = payload.get("labels") or []
    assert "production" not in labels, (
        f"Version 1 of '{prompt_name}' must no longer carry the 'production' label. "
        f"Got labels: {labels}"
    )


def test_log_contains_promoted_version_line(log_contents, prompt_name):
    match = PROMOTED_LINE_RE.search(log_contents)
    assert match, (
        f"Expected log file to contain a line matching "
        f"'Promoted version: 2 labels: <labels>'. Log contents:\n{log_contents}"
    )
    logged_value = match.group(1).strip()

    payload = _fetch_prompt_version(prompt_name, 2)
    expected_labels = _labels_excluding_latest(payload.get("labels"))
    expected_value = _expected_log_value(expected_labels)

    assert logged_value == expected_value, (
        f"Promoted version log line mismatch. Expected '{expected_value}' "
        f"(sorted labels of version 2 excluding 'latest'), got '{logged_value}'."
    )


def test_log_contains_previous_version_line(log_contents, prompt_name):
    match = PREVIOUS_LINE_RE.search(log_contents)
    assert match, (
        f"Expected log file to contain a line matching "
        f"'Previous version: 1 labels: <labels>'. Log contents:\n{log_contents}"
    )
    logged_value = match.group(1).strip()

    payload = _fetch_prompt_version(prompt_name, 1)
    expected_labels = _labels_excluding_latest(payload.get("labels"))
    expected_value = _expected_log_value(expected_labels)

    assert logged_value == expected_value, (
        f"Previous version log line mismatch. Expected '{expected_value}' "
        f"(sorted labels of version 1 excluding 'latest', or 'none' if empty), "
        f"got '{logged_value}'."
    )

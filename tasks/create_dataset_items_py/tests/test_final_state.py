import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def _expected_dataset_name() -> str:
    return f"qa-eval-{_run_id()}"


def _langfuse_base_url() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL environment variable must be set for verification."
    return base.rstrip("/")


def _basic_auth() -> tuple:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    assert public_key, "LANGFUSE_PUBLIC_KEY environment variable must be set for verification."
    assert secret_key, "LANGFUSE_SECRET_KEY environment variable must be set for verification."
    return (public_key, secret_key)


def _is_non_empty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    # numbers, booleans, etc. are considered non-empty if present
    return True


def test_log_file_contains_dataset_name():
    assert os.path.isfile(LOG_PATH), (
        f"Expected the log file {LOG_PATH} to exist after the task is executed."
    )
    expected_name = _expected_dataset_name()
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(
        r"^\s*Dataset name:\s*" + re.escape(expected_name) + r"\s*$",
        re.MULTILINE,
    )
    assert pattern.search(content) is not None, (
        f"Expected log file {LOG_PATH} to contain a line of the form "
        f"'Dataset name: {expected_name}'. Actual log content:\n{content}"
    )


def test_dataset_exists_via_public_api():
    expected_name = _expected_dataset_name()
    url = f"{_langfuse_base_url()}/api/public/v2/datasets/{expected_name}"
    response = requests.get(url, auth=_basic_auth(), timeout=30)
    assert response.status_code == 200, (
        f"Expected GET {url} to return HTTP 200 but got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert body.get("name") == expected_name, (
        f"Expected dataset 'name' field to equal {expected_name!r}, "
        f"got {body.get('name')!r}. Full body: {body}"
    )


def test_dataset_has_three_items_with_expected_shape():
    expected_name = _expected_dataset_name()
    url = f"{_langfuse_base_url()}/api/public/dataset-items"
    params = {"datasetName": expected_name, "limit": 50}
    response = requests.get(url, auth=_basic_auth(), params=params, timeout=30)
    assert response.status_code == 200, (
        f"Expected GET {url}?datasetName={expected_name}&limit=50 to return HTTP 200 "
        f"but got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    items = body.get("data")
    assert isinstance(items, list), (
        f"Expected 'data' field of dataset-items response to be a list, got: {body}"
    )
    assert len(items) == 3, (
        f"Expected exactly 3 dataset items for dataset {expected_name}, "
        f"got {len(items)}. Items: {items}"
    )
    for idx, item in enumerate(items):
        assert _is_non_empty(item.get("input")), (
            f"Dataset item #{idx} (id={item.get('id')!r}) must have a non-empty 'input' "
            f"field. Got: {item.get('input')!r}"
        )
        assert _is_non_empty(item.get("expectedOutput")), (
            f"Dataset item #{idx} (id={item.get('id')!r}) must have a non-empty "
            f"'expectedOutput' field. Got: {item.get('expectedOutput')!r}"
        )
        metadata = item.get("metadata")
        assert isinstance(metadata, dict), (
            f"Dataset item #{idx} (id={item.get('id')!r}) must have a 'metadata' object, "
            f"got: {metadata!r}"
        )
        assert metadata.get("source") == "harbor-task", (
            f"Dataset item #{idx} (id={item.get('id')!r}) must have metadata.source == "
            f"'harbor-task'. Got metadata: {metadata!r}"
        )

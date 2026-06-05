import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

REQUIRED_ITEMS = {
    "What is the capital of France?": "paris",
    "What is the capital of Japan?": "tokyo",
    "What is the capital of Brazil?": "brasilia",
}


def _read_log_lines():
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh.readlines()]


def _expected_dataset_name():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set in the verifier env."
    return f"geography-quiz-{run_id}"


def _langfuse_auth_and_host():
    public = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_BASE_URL")
    assert public, "LANGFUSE_PUBLIC_KEY is not set in the verifier env."
    assert secret, "LANGFUSE_SECRET_KEY is not set in the verifier env."
    assert host, "LANGFUSE_BASE_URL is not set in the verifier env."
    return (public, secret), host.rstrip("/")


def _find_log_line(prefix):
    for line in _read_log_lines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def test_log_contains_dataset_name():
    dataset_name = _expected_dataset_name()
    value = _find_log_line("Dataset name:")
    assert value == dataset_name, (
        f"Expected log line 'Dataset name: {dataset_name}', got '{value}'."
    )


def test_log_contains_dataset_id():
    value = _find_log_line("Dataset id:")
    assert value, "Expected a 'Dataset id: <id>' line in the log file."
    # Dataset ids returned by Langfuse are non-empty strings.
    assert len(value) > 0, "Logged dataset id is empty."


def test_log_contains_item_count():
    value = _find_log_line("Item count:")
    assert value == "3", f"Expected log line 'Item count: 3', got 'Item count: {value}'."


def test_log_contains_three_item_ids():
    ids = []
    for line in _read_log_lines():
        m = re.match(r"^Item id:\s*(\S+)\s*$", line)
        if m:
            ids.append(m.group(1))
    assert len(ids) == 3, (
        f"Expected exactly three 'Item id: <id>' lines in the log file, found {len(ids)}: {ids}"
    )
    assert len(set(ids)) == 3, f"Item ids in log file are not unique: {ids}"


def test_dataset_exists_via_langfuse_api():
    dataset_name = _expected_dataset_name()
    auth, host = _langfuse_auth_and_host()
    url = f"{host}/api/public/v2/datasets/{dataset_name}"
    response = requests.get(url, auth=auth, timeout=30)
    assert response.status_code == 200, (
        f"GET {url} failed: status={response.status_code}, body={response.text}"
    )
    body = response.json()
    assert body.get("name") == dataset_name, (
        f"Dataset name from API ({body.get('name')!r}) does not match expected ({dataset_name!r})."
    )
    assert body.get("description") == "Geography QA evaluation dataset", (
        f"Dataset description from API ({body.get('description')!r}) does not match the required value."
    )

    logged_id = _find_log_line("Dataset id:")
    assert logged_id, "Could not extract 'Dataset id:' from the log file."
    assert body.get("id") == logged_id, (
        f"Logged dataset id ({logged_id!r}) does not match the API id ({body.get('id')!r})."
    )


def test_dataset_items_exist_via_langfuse_api():
    dataset_name = _expected_dataset_name()
    auth, host = _langfuse_auth_and_host()
    url = f"{host}/api/public/dataset-items"
    response = requests.get(
        url,
        params={"datasetName": dataset_name, "limit": 50},
        auth=auth,
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET {url} failed: status={response.status_code}, body={response.text}"
    )
    body = response.json()
    meta = body.get("meta", {})
    items = body.get("data", [])
    assert meta.get("totalItems") == 3, (
        f"Expected meta.totalItems == 3, got {meta.get('totalItems')!r}."
    )
    assert len(items) == 3, f"Expected exactly 3 dataset items, got {len(items)}."

    seen_inputs = []
    for item in items:
        assert item.get("datasetName") == dataset_name, (
            f"Dataset item {item.get('id')!r} has datasetName {item.get('datasetName')!r}, "
            f"expected {dataset_name!r}."
        )
        input_value = item.get("input")
        expected_output = item.get("expectedOutput")
        assert isinstance(input_value, str), (
            f"Dataset item {item.get('id')!r} has non-string input: {input_value!r}."
        )
        assert isinstance(expected_output, str), (
            f"Dataset item {item.get('id')!r} has non-string expectedOutput: {expected_output!r}."
        )
        assert input_value in REQUIRED_ITEMS, (
            f"Unexpected dataset item input: {input_value!r}. "
            f"Allowed inputs: {sorted(REQUIRED_ITEMS.keys())}"
        )
        assert REQUIRED_ITEMS[input_value] in expected_output.strip().lower(), (
            f"Dataset item with input {input_value!r} has expectedOutput {expected_output!r}, "
            f"expected (case-insensitive) {REQUIRED_ITEMS[input_value]!r}."
        )
        seen_inputs.append(input_value)

    assert sorted(seen_inputs) == sorted(REQUIRED_ITEMS.keys()), (
        f"The three dataset items do not cover all required questions. "
        f"Got: {sorted(seen_inputs)}, required: {sorted(REQUIRED_ITEMS.keys())}"
    )


def test_logged_item_ids_match_api_item_ids():
    dataset_name = _expected_dataset_name()
    auth, host = _langfuse_auth_and_host()
    url = f"{host}/api/public/dataset-items"
    response = requests.get(
        url,
        params={"datasetName": dataset_name, "limit": 50},
        auth=auth,
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET {url} failed: status={response.status_code}, body={response.text}"
    )
    api_ids = {item.get("id") for item in response.json().get("data", [])}

    log_ids = set()
    for line in _read_log_lines():
        m = re.match(r"^Item id:\s*(\S+)\s*$", line)
        if m:
            log_ids.add(m.group(1))

    assert log_ids == api_ids, (
        f"Logged item ids do not match Langfuse API item ids. "
        f"Logged: {sorted(log_ids)}, API: {sorted(api_ids)}"
    )

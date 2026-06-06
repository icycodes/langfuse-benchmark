import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_DESCRIPTION = "Geography QA seeded by TS SDK"
EXPECTED_QA_PAIRS = {
    "What is the capital of France?": "Paris",
    "What is the capital of Germany?": "Berlin",
    "What is the capital of Japan?": "Tokyo",
}


def _run_id():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set in the verifier env."
    return run_id


def _dataset_name():
    return f"qa-dataset-{_run_id()}"


def _auth():
    pub = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sec = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert pub, "LANGFUSE_PUBLIC_KEY is not set in the verifier env."
    assert sec, "LANGFUSE_SECRET_KEY is not set in the verifier env."
    return (pub, sec)


def _base_url():
    base = os.environ.get("LANGFUSE_BASE_URL", "").rstrip("/")
    assert base, "LANGFUSE_BASE_URL is not set in the verifier env."
    return base


@pytest.fixture(scope="module")
def log_contents():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file at {LOG_FILE} but it does not exist."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def parsed_log(log_contents):
    name_match = re.search(r"^Dataset name:\s*(.+?)\s*$", log_contents, re.MULTILINE)
    id_match = re.search(r"^Dataset ID:\s*(.+?)\s*$", log_contents, re.MULTILINE)
    count_match = re.search(r"^Items created:\s*(\d+)\s*$", log_contents, re.MULTILINE)
    assert name_match, (
        f"Could not find a 'Dataset name: <name>' line in {LOG_FILE}. "
        f"Log contents:\n{log_contents}"
    )
    assert id_match, (
        f"Could not find a 'Dataset ID: <id>' line in {LOG_FILE}. "
        f"Log contents:\n{log_contents}"
    )
    assert count_match, (
        f"Could not find an 'Items created: <n>' line in {LOG_FILE}. "
        f"Log contents:\n{log_contents}"
    )
    return {
        "name": name_match.group(1),
        "id": id_match.group(1),
        "count": int(count_match.group(1)),
    }


def test_log_dataset_name_matches_run_id(parsed_log):
    expected = _dataset_name()
    assert parsed_log["name"] == expected, (
        f"Log file reports dataset name {parsed_log['name']!r}, expected {expected!r}."
    )


def test_log_dataset_id_non_empty(parsed_log):
    assert parsed_log["id"], "Log file's 'Dataset ID:' line has an empty value."


def test_log_items_created_count(parsed_log):
    assert parsed_log["count"] == 3, (
        f"Log file reports 'Items created: {parsed_log['count']}', expected 3."
    )


def test_dataset_exists_on_langfuse(parsed_log):
    dataset_name = _dataset_name()
    url = f"{_base_url()}/api/public/v2/datasets/{dataset_name}"
    response = requests.get(url, auth=_auth(), timeout=30)
    assert response.status_code == 200, (
        f"GET {url} returned status {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("name") == dataset_name, (
        f"Dataset 'name' on server is {body.get('name')!r}, expected {dataset_name!r}."
    )
    assert body.get("id") == parsed_log["id"], (
        "Dataset 'id' on server "
        f"({body.get('id')!r}) does not match the 'Dataset ID' line "
        f"({parsed_log['id']!r}) in {LOG_FILE}."
    )
    assert body.get("description") == EXPECTED_DESCRIPTION, (
        f"Dataset description on server is {body.get('description')!r}, "
        f"expected {EXPECTED_DESCRIPTION!r}."
    )
    metadata = body.get("metadata")
    assert isinstance(metadata, dict), (
        f"Dataset metadata on server is not a JSON object: {metadata!r}."
    )
    assert metadata.get("language") == "typescript", (
        f"Dataset metadata.language on server is {metadata.get('language')!r}, "
        "expected 'typescript'."
    )


def test_dataset_items_on_langfuse():
    dataset_name = _dataset_name()
    url = f"{_base_url()}/api/public/dataset-items"
    response = requests.get(
        url,
        params={"datasetName": dataset_name, "limit": 50},
        auth=_auth(),
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET {url} returned status {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    data = body.get("data", [])
    assert isinstance(data, list), (
        f"Expected 'data' to be a list in the dataset-items response; got {type(data)}."
    )
    assert len(data) == 3, (
        f"Expected exactly 3 dataset items for dataset {dataset_name!r}, "
        f"found {len(data)}. Items: {data}"
    )

    actual_pairs = {}
    for item in data:
        assert item.get("datasetName") == dataset_name, (
            f"Dataset item {item.get('id')!r} has datasetName "
            f"{item.get('datasetName')!r}, expected {dataset_name!r}."
        )
        item_input = item.get("input")
        item_expected = item.get("expectedOutput")
        assert isinstance(item_input, dict) and "question" in item_input, (
            f"Dataset item {item.get('id')!r} input is not an object with a "
            f"'question' field; got {item_input!r}."
        )
        assert isinstance(item_expected, dict) and "answer" in item_expected, (
            f"Dataset item {item.get('id')!r} expectedOutput is not an object "
            f"with an 'answer' field; got {item_expected!r}."
        )
        actual_pairs[item_input["question"]] = item_expected["answer"]

    assert actual_pairs == EXPECTED_QA_PAIRS, (
        "Dataset items do not match the expected question/answer pairs. "
        f"Expected {EXPECTED_QA_PAIRS}, got {actual_pairs}."
    )

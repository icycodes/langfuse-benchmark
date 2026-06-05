import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

VALID_LABELS = {"positive", "negative", "neutral"}


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set in the verifier."
    return run_id


def _dataset_name() -> str:
    return f"harbor-eval-{_run_id()}"


def _run_name() -> str:
    return f"experiment-{_run_id()}"


def _auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
    assert pk and sk, "LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY must be set."
    return (pk, sk)


def _base_url() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL", "").rstrip("/")
    assert base, "LANGFUSE_BASE_URL must be set."
    return base


@pytest.fixture(scope="session")
def log_contents() -> str:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="session")
def log_accuracy(log_contents: str) -> float:
    match = re.search(r"^Accuracy:\s*([0-9]+(?:\.[0-9]+)?)\s*$",
                      log_contents, flags=re.MULTILINE)
    assert match, (
        "Expected a line like 'Accuracy: <float>' in the log file, "
        f"but log contained:\n{log_contents}"
    )
    value = float(match.group(1))
    assert 0.0 <= value <= 1.0, (
        f"Accuracy value in log file must be in [0.0, 1.0], got {value}."
    )
    return value


def test_log_contains_dataset_name(log_contents: str):
    expected = f"Dataset name: {_dataset_name()}"
    assert expected in log_contents, (
        f"Log file is missing required line '{expected}'."
    )


def test_log_contains_dataset_run_name(log_contents: str):
    expected = f"Dataset run name: {_run_name()}"
    assert expected in log_contents, (
        f"Log file is missing required line '{expected}'."
    )


def test_log_contains_item_count(log_contents: str):
    assert "Items: 5" in log_contents, (
        "Log file is missing required line 'Items: 5'."
    )


def test_log_contains_status_ok(log_contents: str):
    assert "Status: OK" in log_contents, (
        "Log file is missing required line 'Status: OK'."
    )


def test_log_accuracy_format(log_accuracy: float):
    # Fixture itself validates the format and range.
    assert isinstance(log_accuracy, float)


def test_dataset_exists_via_api():
    url = f"{_base_url()}/api/public/v2/datasets/{_dataset_name()}"
    resp = requests.get(url, auth=_auth(), timeout=30)
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    data = resp.json()
    assert data.get("name") == _dataset_name(), (
        f"Expected dataset name {_dataset_name()!r}, got {data.get('name')!r}."
    )


def test_dataset_has_five_items_with_valid_labels():
    url = f"{_base_url()}/api/public/dataset-items"
    resp = requests.get(
        url,
        auth=_auth(),
        params={"datasetName": _dataset_name(), "limit": 50},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    payload = resp.json()
    items = payload.get("data", [])
    assert len(items) == 5, (
        f"Expected exactly 5 dataset items in '{_dataset_name()}', got {len(items)}."
    )

    labels = []
    for item in items:
        expected = item.get("expectedOutput")
        # `expectedOutput` may be returned as a JSON-encoded string; accept either.
        if isinstance(expected, str):
            label = expected.strip().strip('"').lower()
        else:
            label = str(expected).strip().lower()
        assert label in VALID_LABELS, (
            f"Item expectedOutput must be one of {sorted(VALID_LABELS)}, got {expected!r}."
        )
        labels.append(label)

    assert len(set(labels)) >= 2, (
        f"Dataset items must cover at least two distinct labels, got {labels}."
    )


@pytest.fixture(scope="session")
def dataset_run_payload():
    url = (
        f"{_base_url()}/api/public/datasets/{_dataset_name()}/runs/{_run_name()}"
    )
    resp = requests.get(url, auth=_auth(), timeout=30)
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    payload = resp.json()
    return payload


def test_dataset_run_metadata(dataset_run_payload):
    payload = dataset_run_payload
    assert payload.get("name") == _run_name(), (
        f"Expected dataset run name {_run_name()!r}, got {payload.get('name')!r}."
    )
    run_id = payload.get("id")
    assert run_id, f"Dataset run is missing an 'id' field: {payload}"
    items = payload.get("datasetRunItems") or []
    assert len(items) == 5, (
        f"Expected exactly 5 dataset-run items for run {_run_name()!r}, got {len(items)}."
    )


@pytest.fixture(scope="session")
def dataset_run_id(dataset_run_payload) -> str:
    run_id = dataset_run_payload.get("id")
    assert run_id, "Dataset run payload missing 'id'."
    return run_id


@pytest.fixture(scope="session")
def run_scores(dataset_run_id: str):
    url = f"{_base_url()}/api/public/v2/scores"
    resp = requests.get(
        url,
        auth=_auth(),
        params={"datasetRunId": dataset_run_id, "limit": 100},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text[:500]}"
    )
    payload = resp.json()
    return payload.get("data", [])


def test_accuracy_scores_present(run_scores):
    accuracy_scores = [s for s in run_scores if s.get("name") == "accuracy"]
    assert len(accuracy_scores) == 5, (
        "Expected exactly 5 accuracy scores attached to the dataset run, "
        f"got {len(accuracy_scores)}."
    )
    for score in accuracy_scores:
        value = score.get("value")
        assert value in (0, 0.0, 1, 1.0), (
            f"Accuracy score values must be 0.0 or 1.0, got {value!r}."
        )


def test_avg_accuracy_score_matches_log(run_scores, log_accuracy):
    avg_scores = [s for s in run_scores if s.get("name") == "avg_accuracy"]
    assert avg_scores, (
        "Expected at least one run-level 'avg_accuracy' score on the dataset run."
    )
    score = avg_scores[0]
    value = score.get("value")
    assert isinstance(value, (int, float)), (
        f"avg_accuracy score value must be numeric, got {value!r}."
    )
    assert 0.0 <= float(value) <= 1.0, (
        f"avg_accuracy score value must be in [0.0, 1.0], got {value!r}."
    )
    assert abs(float(value) - log_accuracy) <= 0.01, (
        f"avg_accuracy score value {value} does not match log Accuracy "
        f"{log_accuracy} within ±0.01."
    )


def test_accuracy_score_mean_matches_log(run_scores, log_accuracy):
    accuracy_values = [
        float(s["value"]) for s in run_scores if s.get("name") == "accuracy"
    ]
    assert len(accuracy_values) == 5, (
        f"Expected 5 accuracy score values, got {len(accuracy_values)}."
    )
    mean = sum(accuracy_values) / len(accuracy_values)
    assert abs(mean - log_accuracy) <= 0.01, (
        f"Mean of accuracy scores ({mean}) does not match log Accuracy "
        f"({log_accuracy}) within ±0.01."
    )

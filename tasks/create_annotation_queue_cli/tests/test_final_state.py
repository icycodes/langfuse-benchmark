import math
import os
import re

import httpx
import pytest

PROJECT_DIR = "/home/user/langfuse-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

EXPECTED_QUEUE_DESCRIPTION = "Queue for QA reviewers to score model answers"
EXPECTED_SCORE_CONFIG_DESCRIPTION = (
    "Quality score for QA reviewer answers (0=bad, 1=great)"
)

SCORE_CONFIG_LOG_PATTERN = re.compile(
    r"^Score Config ID:\s*(?P<score_config_id>[A-Za-z0-9_\-]+)\s*$"
)
QUEUE_LOG_PATTERN = re.compile(
    r"^Annotation Queue ID:\s*(?P<queue_id>[A-Za-z0-9_\-]+)\s*$"
)


def _get_env(name: str) -> str:
    value = os.environ.get(name, "")
    assert value, f"Required environment variable {name} is not set."
    return value


def _expected_score_config_name() -> str:
    run_id = _get_env("ZEALT_RUN_ID")
    assert re.fullmatch(r"zr-[a-z0-9]+", run_id), (
        f"ZEALT_RUN_ID must match 'zr-[a-z0-9]+'. Got: {run_id!r}"
    )
    return f"answer-quality-{run_id}"


def _expected_queue_name() -> str:
    run_id = _get_env("ZEALT_RUN_ID")
    assert re.fullmatch(r"zr-[a-z0-9]+", run_id), (
        f"ZEALT_RUN_ID must match 'zr-[a-z0-9]+'. Got: {run_id!r}"
    )
    return f"qa-review-queue-{run_id}"


def _langfuse_base_url() -> str:
    return _get_env("LANGFUSE_BASE_URL").rstrip("/")


def _langfuse_auth():
    return (_get_env("LANGFUSE_PUBLIC_KEY"), _get_env("LANGFUSE_SECRET_KEY"))


def _read_logged_ids():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} does not exist. The executor must write "
        f"'Score Config ID: <id>' and 'Annotation Queue ID: <id>' there."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]
    assert lines, f"{LOG_FILE} is empty; expected two ID lines."

    score_matches = [SCORE_CONFIG_LOG_PATTERN.match(line) for line in lines]
    score_matches = [m for m in score_matches if m]
    queue_matches = [QUEUE_LOG_PATTERN.match(line) for line in lines]
    queue_matches = [m for m in queue_matches if m]

    assert len(score_matches) == 1, (
        f"Expected exactly one 'Score Config ID: <id>' line in {LOG_FILE}, "
        f"found {len(score_matches)}. Content was: {lines!r}"
    )
    assert len(queue_matches) == 1, (
        f"Expected exactly one 'Annotation Queue ID: <id>' line in {LOG_FILE}, "
        f"found {len(queue_matches)}. Content was: {lines!r}"
    )

    return (
        score_matches[0].group("score_config_id"),
        queue_matches[0].group("queue_id"),
    )


@pytest.fixture(scope="module")
def logged_ids():
    return _read_logged_ids()


@pytest.fixture(scope="module")
def score_config_body(logged_ids):
    score_config_id, _ = logged_ids
    response = httpx.get(
        f"{_langfuse_base_url()}/api/public/score-configs/{score_config_id}",
        auth=_langfuse_auth(),
        timeout=30.0,
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200 fetching score config {score_config_id}, "
        f"got {response.status_code}: {response.text}"
    )
    return response.json()


@pytest.fixture(scope="module")
def annotation_queue_body(logged_ids):
    _, queue_id = logged_ids
    response = httpx.get(
        f"{_langfuse_base_url()}/api/public/annotation-queues/{queue_id}",
        auth=_langfuse_auth(),
        timeout=30.0,
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200 fetching annotation queue {queue_id}, "
        f"got {response.status_code}: {response.text}"
    )
    return response.json()


def test_log_file_format_captures_both_ids(logged_ids):
    score_config_id, queue_id = logged_ids
    assert score_config_id, "Captured score_config_id is empty."
    assert queue_id, "Captured queue_id is empty."


def test_score_config_id_matches_api(logged_ids, score_config_body):
    score_config_id, _ = logged_ids
    assert score_config_body.get("id") == score_config_id, (
        f"Score config id mismatch. API returned {score_config_body.get('id')!r}, "
        f"log file recorded {score_config_id!r}."
    )


def test_score_config_has_expected_name(score_config_body):
    expected = _expected_score_config_name()
    assert score_config_body.get("name") == expected, (
        f"Score config name mismatch. Expected {expected!r}, "
        f"got {score_config_body.get('name')!r}."
    )


def test_score_config_has_expected_data_type(score_config_body):
    assert score_config_body.get("dataType") == "NUMERIC", (
        f"Score config dataType mismatch. Expected 'NUMERIC', "
        f"got {score_config_body.get('dataType')!r}."
    )


def test_score_config_has_expected_min_value(score_config_body):
    min_value = score_config_body.get("minValue")
    assert isinstance(min_value, (int, float)), (
        f"Score config minValue must be numeric, got {type(min_value).__name__}."
    )
    assert math.isclose(float(min_value), 0.0, abs_tol=1e-9), (
        f"Score config minValue mismatch. Expected 0, got {min_value!r}."
    )


def test_score_config_has_expected_max_value(score_config_body):
    max_value = score_config_body.get("maxValue")
    assert isinstance(max_value, (int, float)), (
        f"Score config maxValue must be numeric, got {type(max_value).__name__}."
    )
    assert math.isclose(float(max_value), 1.0, abs_tol=1e-9), (
        f"Score config maxValue mismatch. Expected 1, got {max_value!r}."
    )


def test_score_config_has_expected_description(score_config_body):
    assert score_config_body.get("description") == EXPECTED_SCORE_CONFIG_DESCRIPTION, (
        f"Score config description mismatch. "
        f"Expected {EXPECTED_SCORE_CONFIG_DESCRIPTION!r}, "
        f"got {score_config_body.get('description')!r}."
    )


def test_annotation_queue_id_matches_api(logged_ids, annotation_queue_body):
    _, queue_id = logged_ids
    assert annotation_queue_body.get("id") == queue_id, (
        f"Annotation queue id mismatch. API returned "
        f"{annotation_queue_body.get('id')!r}, log file recorded {queue_id!r}."
    )


def test_annotation_queue_has_expected_name(annotation_queue_body):
    expected = _expected_queue_name()
    assert annotation_queue_body.get("name") == expected, (
        f"Annotation queue name mismatch. Expected {expected!r}, "
        f"got {annotation_queue_body.get('name')!r}."
    )


def test_annotation_queue_has_expected_description(annotation_queue_body):
    assert annotation_queue_body.get("description") == EXPECTED_QUEUE_DESCRIPTION, (
        f"Annotation queue description mismatch. "
        f"Expected {EXPECTED_QUEUE_DESCRIPTION!r}, "
        f"got {annotation_queue_body.get('description')!r}."
    )


def test_annotation_queue_references_logged_score_config(
    logged_ids, annotation_queue_body
):
    score_config_id, _ = logged_ids
    score_config_ids = annotation_queue_body.get("scoreConfigIds")
    assert isinstance(score_config_ids, list), (
        f"Expected 'scoreConfigIds' to be a list, got {type(score_config_ids).__name__}."
    )
    assert score_config_ids == [score_config_id], (
        f"Annotation queue scoreConfigIds mismatch. Expected "
        f"[{score_config_id!r}], got {score_config_ids!r}."
    )


def test_annotation_queue_visible_in_list_endpoint():
    expected_name = _expected_queue_name()
    base_url = _langfuse_base_url()
    auth = _langfuse_auth()

    found = False
    page = 1
    for _ in range(20):
        response = httpx.get(
            f"{base_url}/api/public/annotation-queues",
            params={"page": page, "limit": 100},
            auth=auth,
            timeout=30.0,
        )
        assert response.status_code == 200, (
            f"Listing annotation queues failed on page {page}: "
            f"HTTP {response.status_code}: {response.text}"
        )
        data = response.json().get("data") or []
        if not data:
            break
        if any(item.get("name") == expected_name for item in data):
            found = True
            break
        page += 1

    assert found, (
        f"Annotation queue named {expected_name!r} was not found in any page of "
        f"GET /api/public/annotation-queues."
    )

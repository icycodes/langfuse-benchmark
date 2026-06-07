import os
import re

import pytest
import requests

LOG_FILE = "/home/user/myproject/output.log"
NUMERIC_LINE_RE = re.compile(r"^Numeric Score Config ID:\s*(\S+)\s*$", re.MULTILINE)
CATEGORICAL_LINE_RE = re.compile(
    r"^Categorical Score Config ID:\s*(\S+)\s*$", re.MULTILINE
)


def _env(name: str) -> str:
    value = os.environ.get(name)
    assert value, f"Required environment variable {name!r} is not set."
    return value


def _api_get(path: str) -> requests.Response:
    base_url = _env("LANGFUSE_BASE_URL").rstrip("/")
    public_key = _env("LANGFUSE_PUBLIC_KEY")
    secret_key = _env("LANGFUSE_SECRET_KEY")
    url = f"{base_url}{path}"
    return requests.get(url, auth=(public_key, secret_key), timeout=30)


@pytest.fixture(scope="session")
def run_id() -> str:
    return _env("ZEALT_RUN_ID")


@pytest.fixture(scope="session")
def log_text() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task is complete."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="session")
def numeric_id(log_text: str) -> str:
    matches = NUMERIC_LINE_RE.findall(log_text)
    assert len(matches) == 1, (
        "Expected exactly one line of the form "
        f"'Numeric Score Config ID: <id>' in {LOG_FILE}, found {len(matches)}."
    )
    return matches[0]


@pytest.fixture(scope="session")
def categorical_id(log_text: str) -> str:
    matches = CATEGORICAL_LINE_RE.findall(log_text)
    assert len(matches) == 1, (
        "Expected exactly one line of the form "
        f"'Categorical Score Config ID: <id>' in {LOG_FILE}, found {len(matches)}."
    )
    return matches[0]


def test_numeric_score_config_via_api(run_id: str, numeric_id: str):
    expected_name = f"quality-{run_id}"
    response = _api_get(f"/api/public/score-configs/{numeric_id}")
    assert response.status_code == 200, (
        f"GET /api/public/score-configs/{numeric_id} returned "
        f"{response.status_code}: {response.text}"
    )
    payload = response.json()
    assert payload.get("id") == numeric_id, (
        f"Score config id mismatch in API response: expected {numeric_id}, "
        f"got {payload.get('id')!r}."
    )
    assert payload.get("name") == expected_name, (
        f"Numeric score config name mismatch: expected {expected_name!r}, "
        f"got {payload.get('name')!r}."
    )
    assert payload.get("dataType") == "NUMERIC", (
        "Numeric score config has unexpected dataType: "
        f"expected 'NUMERIC', got {payload.get('dataType')!r}."
    )
    assert payload.get("minValue") == 0, (
        f"Numeric score config minValue mismatch: expected 0, "
        f"got {payload.get('minValue')!r}."
    )
    assert payload.get("maxValue") == 10, (
        f"Numeric score config maxValue mismatch: expected 10, "
        f"got {payload.get('maxValue')!r}."
    )
    description = payload.get("description")
    assert isinstance(description, str) and description.strip(), (
        "Numeric score config description must be a non-empty string, "
        f"got {description!r}."
    )


def test_categorical_score_config_via_api(run_id: str, categorical_id: str):
    expected_name = f"sentiment-{run_id}"
    response = _api_get(f"/api/public/score-configs/{categorical_id}")
    assert response.status_code == 200, (
        f"GET /api/public/score-configs/{categorical_id} returned "
        f"{response.status_code}: {response.text}"
    )
    payload = response.json()
    assert payload.get("id") == categorical_id, (
        f"Score config id mismatch in API response: expected {categorical_id}, "
        f"got {payload.get('id')!r}."
    )
    assert payload.get("name") == expected_name, (
        f"Categorical score config name mismatch: expected {expected_name!r}, "
        f"got {payload.get('name')!r}."
    )
    assert payload.get("dataType") == "CATEGORICAL", (
        "Categorical score config has unexpected dataType: "
        f"expected 'CATEGORICAL', got {payload.get('dataType')!r}."
    )
    categories = payload.get("categories")
    assert isinstance(categories, list), (
        "Categorical score config 'categories' must be a list, "
        f"got {type(categories).__name__}."
    )
    actual = {(int(cat["value"]), cat["label"]) for cat in categories}
    expected = {(0, "negative"), (1, "neutral"), (2, "positive")}
    assert actual == expected, (
        "Categorical score config categories do not match the required "
        f"sentiment buckets. Expected {expected!r}, got {actual!r}."
    )


def test_configs_listed_via_api(run_id: str, numeric_id: str, categorical_id: str):
    seen_ids: set[str] = set()
    page = 1
    target = {numeric_id, categorical_id}
    # Walk through pages until both configs are seen or the listing is exhausted.
    while True:
        response = _api_get(f"/api/public/score-configs?page={page}&limit=100")
        assert response.status_code == 200, (
            f"GET /api/public/score-configs (page {page}) returned "
            f"{response.status_code}: {response.text}"
        )
        body = response.json()
        data = body.get("data") or []
        for item in data:
            cfg_id = item.get("id")
            if isinstance(cfg_id, str):
                seen_ids.add(cfg_id)
        if target.issubset(seen_ids):
            break
        meta = body.get("meta") or {}
        total_pages = meta.get("totalPages")
        if total_pages is None or page >= int(total_pages):
            break
        page += 1
    missing = target - seen_ids
    assert not missing, (
        "Score configs were not reachable through the listing endpoint "
        f"GET /api/public/score-configs (missing ids: {sorted(missing)})."
    )

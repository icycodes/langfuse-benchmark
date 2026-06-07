import os
import re
from typing import Dict, List, Optional

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

LOG_LINE_RE = re.compile(r"^ScoreConfig:\s*(?P<name>\S+?)=(?P<id>\S+)\s*$")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID is required in the verification environment."
    return run_id


def _expected_names(run_id: str) -> Dict[str, str]:
    return {
        "numeric": f"quality-score-{run_id}",
        "categorical": f"feedback-sentiment-{run_id}",
        "boolean": f"is-relevant-{run_id}",
    }


def _api_base() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set for verification."
    return base.rstrip("/")


def _auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, "Both LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set."
    return (pk, sk)


def _read_log_entries() -> Dict[str, str]:
    assert os.path.isfile(LOG_FILE), f"Expected log file at {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f.readlines()]

    non_empty = [ln for ln in lines if ln.strip()]
    assert len(non_empty) == 3, (
        f"Expected exactly 3 non-empty lines in {LOG_FILE}; found {len(non_empty)}: {non_empty!r}"
    )

    entries: Dict[str, str] = {}
    for ln in non_empty:
        match = LOG_LINE_RE.match(ln)
        assert match, (
            f"Log line {ln!r} does not match the required format 'ScoreConfig: <name>=<id>'."
        )
        name = match.group("name")
        sid = match.group("id")
        assert name not in entries, f"Duplicate score config name {name!r} in log file."
        entries[name] = sid
    return entries


def _fetch_all_score_configs() -> List[dict]:
    base = _api_base()
    auth = _auth()
    page = 1
    out: List[dict] = []
    while True:
        resp = requests.get(
            f"{base}/api/public/score-configs",
            params={"page": page, "limit": 100},
            auth=auth,
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"GET /api/public/score-configs returned {resp.status_code}: {resp.text}"
        )
        payload = resp.json()
        data = payload.get("data") or []
        out.extend(data)
        meta = payload.get("meta") or {}
        total_pages = meta.get("totalPages") or 1
        if page >= total_pages or not data:
            break
        page += 1
    return out


def _find_by_id(configs: List[dict], cid: str) -> Optional[dict]:
    for c in configs:
        if c.get("id") == cid:
            return c
    return None


@pytest.fixture(scope="module")
def log_entries() -> Dict[str, str]:
    return _read_log_entries()


@pytest.fixture(scope="module")
def remote_configs() -> List[dict]:
    return _fetch_all_score_configs()


@pytest.fixture(scope="module")
def expected_names() -> Dict[str, str]:
    return _expected_names(_run_id())


def test_log_file_contains_three_expected_names(log_entries, expected_names):
    assert set(log_entries.keys()) == set(expected_names.values()), (
        f"Log file names {sorted(log_entries.keys())} do not match expected "
        f"{sorted(expected_names.values())}."
    )


def test_numeric_score_config(log_entries, remote_configs, expected_names):
    name = expected_names["numeric"]
    cid = log_entries[name]
    cfg = _find_by_id(remote_configs, cid)
    assert cfg is not None, (
        f"Score config with id {cid!r} (name {name!r}) was not found in Langfuse via "
        f"GET /api/public/score-configs."
    )
    assert cfg.get("name") == name, (
        f"Score config id {cid!r} has name {cfg.get('name')!r}, expected {name!r}."
    )
    assert cfg.get("dataType") == "NUMERIC", (
        f"Score config {name!r} dataType is {cfg.get('dataType')!r}, expected 'NUMERIC'."
    )
    assert not cfg.get("isArchived", False), (
        f"Score config {name!r} must not be archived."
    )
    assert float(cfg.get("minValue")) == 0.0, (
        f"Score config {name!r} minValue is {cfg.get('minValue')!r}, expected 0."
    )
    assert float(cfg.get("maxValue")) == 10.0, (
        f"Score config {name!r} maxValue is {cfg.get('maxValue')!r}, expected 10."
    )


def test_categorical_score_config(log_entries, remote_configs, expected_names):
    name = expected_names["categorical"]
    cid = log_entries[name]
    cfg = _find_by_id(remote_configs, cid)
    assert cfg is not None, (
        f"Score config with id {cid!r} (name {name!r}) was not found in Langfuse via "
        f"GET /api/public/score-configs."
    )
    assert cfg.get("name") == name, (
        f"Score config id {cid!r} has name {cfg.get('name')!r}, expected {name!r}."
    )
    assert cfg.get("dataType") == "CATEGORICAL", (
        f"Score config {name!r} dataType is {cfg.get('dataType')!r}, expected 'CATEGORICAL'."
    )
    assert not cfg.get("isArchived", False), (
        f"Score config {name!r} must not be archived."
    )
    categories = cfg.get("categories") or []
    actual = {c.get("label"): float(c.get("value")) for c in categories}
    expected = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    assert actual == expected, (
        f"Score config {name!r} categories are {actual!r}, expected {expected!r}."
    )


def test_boolean_score_config(log_entries, remote_configs, expected_names):
    name = expected_names["boolean"]
    cid = log_entries[name]
    cfg = _find_by_id(remote_configs, cid)
    assert cfg is not None, (
        f"Score config with id {cid!r} (name {name!r}) was not found in Langfuse via "
        f"GET /api/public/score-configs."
    )
    assert cfg.get("name") == name, (
        f"Score config id {cid!r} has name {cfg.get('name')!r}, expected {name!r}."
    )
    assert cfg.get("dataType") == "BOOLEAN", (
        f"Score config {name!r} dataType is {cfg.get('dataType')!r}, expected 'BOOLEAN'."
    )
    assert not cfg.get("isArchived", False), (
        f"Score config {name!r} must not be archived."
    )

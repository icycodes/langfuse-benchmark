import math
import os
import re
from typing import List, Optional

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

LOG_LINE_RE = re.compile(r"^Model:\s*(?P<name>\S+?)=(?P<id>\S+)\s*$")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID is required in the verification environment."
    return run_id


def _expected_model_name(run_id: str) -> str:
    return f"harbor-llm-{run_id}"


def _expected_match_pattern(run_id: str) -> str:
    return f"(?i)^harbor-llm-{run_id}$"


def _api_base() -> str:
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set for verification."
    return base.rstrip("/")


def _auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, "Both LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set."
    return (pk, sk)


def _read_log_entry():
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file at {LOG_FILE} does not exist."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f.readlines()]

    non_empty = [ln for ln in lines if ln.strip()]
    assert len(non_empty) == 1, (
        f"Expected exactly 1 non-empty line in {LOG_FILE}; found {len(non_empty)}: "
        f"{non_empty!r}"
    )

    match = LOG_LINE_RE.match(non_empty[0])
    assert match, (
        f"Log line {non_empty[0]!r} does not match the required format "
        f"'Model: <modelName>=<id>'."
    )
    return match.group("name"), match.group("id")


def _fetch_model_by_id(model_id: str) -> Optional[dict]:
    base = _api_base()
    auth = _auth()
    resp = requests.get(
        f"{base}/api/public/models/{model_id}",
        auth=auth,
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    assert resp.status_code == 200, (
        f"GET /api/public/models/{model_id} returned {resp.status_code}: {resp.text}"
    )
    return resp.json()


def _fetch_all_models() -> List[dict]:
    base = _api_base()
    auth = _auth()
    page = 1
    out: List[dict] = []
    while True:
        resp = requests.get(
            f"{base}/api/public/models",
            params={"page": page, "limit": 100},
            auth=auth,
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"GET /api/public/models returned {resp.status_code}: {resp.text}"
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


@pytest.fixture(scope="module")
def run_id() -> str:
    return _run_id()


@pytest.fixture(scope="module")
def log_entry():
    return _read_log_entry()


@pytest.fixture(scope="module")
def remote_model(log_entry):
    _, model_id = log_entry
    model = _fetch_model_by_id(model_id)
    assert model is not None, (
        f"Model with id {model_id!r} was not found via GET /api/public/models/{model_id}. "
        f"The Langfuse CLI must have actually created the model definition."
    )
    return model


def test_log_modelname_matches_expected(log_entry, run_id):
    logged_name, _ = log_entry
    expected = _expected_model_name(run_id)
    assert logged_name == expected, (
        f"Logged modelName {logged_name!r} does not match expected {expected!r} "
        f"(run-id {run_id!r})."
    )


def test_remote_model_id_matches_log(remote_model, log_entry):
    _, model_id = log_entry
    assert remote_model.get("id") == model_id, (
        f"Remote model id {remote_model.get('id')!r} does not match the id "
        f"{model_id!r} recorded in {LOG_FILE}."
    )


def test_remote_model_name_is_run_id_scoped(remote_model, run_id):
    expected = _expected_model_name(run_id)
    assert remote_model.get("modelName") == expected, (
        f"Remote model modelName is {remote_model.get('modelName')!r}, "
        f"expected {expected!r}."
    )


def test_remote_model_match_pattern(remote_model, run_id):
    expected = _expected_match_pattern(run_id)
    assert remote_model.get("matchPattern") == expected, (
        f"Remote model matchPattern is {remote_model.get('matchPattern')!r}, "
        f"expected {expected!r}."
    )


def test_remote_model_unit_is_tokens(remote_model):
    assert remote_model.get("unit") == "TOKENS", (
        f"Remote model unit is {remote_model.get('unit')!r}, expected 'TOKENS'."
    )


def test_remote_model_input_price(remote_model):
    raw = remote_model.get("inputPrice")
    assert raw is not None, (
        f"Remote model is missing inputPrice; full record: {remote_model!r}"
    )
    assert math.isclose(float(raw), 0.000003, rel_tol=1e-6, abs_tol=1e-12), (
        f"Remote model inputPrice is {raw!r}, expected 0.000003."
    )


def test_remote_model_output_price(remote_model):
    raw = remote_model.get("outputPrice")
    assert raw is not None, (
        f"Remote model is missing outputPrice; full record: {remote_model!r}"
    )
    assert math.isclose(float(raw), 0.000009, rel_tol=1e-6, abs_tol=1e-12), (
        f"Remote model outputPrice is {raw!r}, expected 0.000009."
    )


def test_remote_model_is_not_langfuse_managed(remote_model):
    managed = remote_model.get("isLangfuseManaged")
    # The field may be absent for custom models; if present it must be False.
    assert managed in (None, False), (
        f"Remote model isLangfuseManaged is {managed!r}, expected False or absent "
        f"for a user-created custom model."
    )


def test_remote_model_appears_in_list_endpoint(log_entry, run_id):
    _, model_id = log_entry
    expected_name = _expected_model_name(run_id)
    models = _fetch_all_models()
    matches = [
        m for m in models
        if m.get("id") == model_id and m.get("modelName") == expected_name
    ]
    assert matches, (
        f"No record with id={model_id!r} and modelName={expected_name!r} was returned "
        f"by GET /api/public/models (paged). Total records scanned: {len(models)}."
    )

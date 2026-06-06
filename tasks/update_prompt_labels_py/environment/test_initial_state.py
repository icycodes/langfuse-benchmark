import importlib
import os

import pytest
import requests
from requests.auth import HTTPBasicAuth

PROJECT_DIR = "/home/user/myproject"


def _get_run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set in the task environment."
    return run_id


def _langfuse_base_url() -> str:
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    return base_url


def _langfuse_auth() -> HTTPBasicAuth:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    assert public_key, "LANGFUSE_PUBLIC_KEY environment variable must be set."
    assert secret_key, "LANGFUSE_SECRET_KEY environment variable must be set."
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
        f"Expected HTTP 200 when fetching version {version} of prompt "
        f"'{prompt_name}', got {response.status_code}: {response.text}"
    )
    return response.json()


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory '{PROJECT_DIR}' does not exist. "
        "The initial environment must provide this directory."
    )


def test_initial_prompt_version_1_has_production_label():
    run_id = _get_run_id()
    prompt_name = f"movie-critic-{run_id}"
    payload = _fetch_prompt_version(prompt_name, 1)
    labels = payload.get("labels") or []
    assert "production" in labels, (
        f"Expected version 1 of prompt '{prompt_name}' to carry the 'production' label "
        f"as part of the initial state. Got labels: {labels}"
    )


def test_initial_prompt_version_2_has_staging_label():
    run_id = _get_run_id()
    prompt_name = f"movie-critic-{run_id}"
    payload = _fetch_prompt_version(prompt_name, 2)
    labels = payload.get("labels") or []
    assert "staging" in labels, (
        f"Expected version 2 of prompt '{prompt_name}' to carry the 'staging' label "
        f"as part of the initial state. Got labels: {labels}"
    )
    assert "production" not in labels, (
        f"Version 2 of prompt '{prompt_name}' must NOT carry the 'production' label "
        f"at task start. Got labels: {labels}"
    )

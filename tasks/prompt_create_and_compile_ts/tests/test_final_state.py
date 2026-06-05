import json
import os
import re

import pytest
import requests


PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")


def _api_auth():
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    assert pk and sk, "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set."
    return (pk, sk)


def _base_url():
    base = os.environ.get("LANGFUSE_BASE_URL")
    assert base, "LANGFUSE_BASE_URL must be set."
    return base.rstrip("/")


def _run_id():
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable must be set."
    return rid


def _expected_prompt_name():
    return f"movie-critic-text-{_run_id()}"


def _read_log_text():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parse_log_versions(log_text):
    staging_match = re.search(
        r"^\s*Staging version:\s*(\d+)\s*$", log_text, re.MULTILINE
    )
    production_match = re.search(
        r"^\s*Production version:\s*(\d+)\s*$", log_text, re.MULTILINE
    )
    assert staging_match, (
        "Expected log file to contain a line 'Staging version: <integer>'."
    )
    assert production_match, (
        "Expected log file to contain a line 'Production version: <integer>'."
    )
    return int(staging_match.group(1)), int(production_match.group(1))


def _fetch_prompt(label=None):
    params = {}
    if label is not None:
        params["label"] = label
    url = f"{_base_url()}/api/public/v2/prompts/{_expected_prompt_name()}"
    return requests.get(url, params=params, auth=_api_auth(), timeout=30)


# ---------------------------------------------------------------------------
# Log file checks
# ---------------------------------------------------------------------------


def test_log_file_contains_expected_prompt_name():
    log_text = _read_log_text()
    expected_line = f"Prompt name: {_expected_prompt_name()}"
    assert expected_line in log_text, (
        f"Expected log file to contain line '{expected_line}'. Got:\n{log_text}"
    )


def test_log_file_versions_are_sequential():
    log_text = _read_log_text()
    staging_v, production_v = _parse_log_versions(log_text)
    assert staging_v >= 1, (
        f"Expected staging version to be >= 1, got {staging_v}."
    )
    assert production_v == staging_v + 1, (
        f"Expected production version ({production_v}) to equal staging version "
        f"({staging_v}) + 1, because production was created after staging."
    )


def test_log_file_contains_compiled_prompt_line():
    log_text = _read_log_text()
    compiled_match = re.search(r"^\s*Compiled prompt:\s*(.+)$", log_text, re.MULTILINE)
    assert compiled_match, (
        "Expected log file to contain a line 'Compiled prompt: <rendered text>'."
    )
    compiled = compiled_match.group(1)

    assert "expert" in compiled, (
        f"Expected compiled prompt to contain 'expert' (variable criticlevel='expert'), "
        f"got: {compiled!r}"
    )
    assert "Dune 2" in compiled, (
        f"Expected compiled prompt to contain 'Dune 2' (variable movie='Dune 2'), "
        f"got: {compiled!r}"
    )
    assert "{{" not in compiled and "}}" not in compiled, (
        f"Expected compiled prompt to NOT contain unrendered '{{{{' or '}}}}' "
        f"placeholders, got: {compiled!r}"
    )


# ---------------------------------------------------------------------------
# package.json checks
# ---------------------------------------------------------------------------


def test_package_json_exists_and_has_start_script_and_dep():
    assert os.path.isfile(PACKAGE_JSON), (
        f"Expected {PACKAGE_JSON} to exist after the task runs."
    )
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    scripts = pkg.get("scripts") or {}
    assert "start" in scripts and scripts["start"], (
        f"Expected package.json to declare an 'npm run start' script. "
        f"Found scripts: {scripts}"
    )

    deps = {}
    deps.update(pkg.get("dependencies") or {})
    deps.update(pkg.get("devDependencies") or {})
    assert "@langfuse/client" in deps, (
        f"Expected package.json to list '@langfuse/client' in dependencies or "
        f"devDependencies. Found: {sorted(deps.keys())}"
    )


# ---------------------------------------------------------------------------
# Langfuse Public API checks
# ---------------------------------------------------------------------------


def test_production_prompt_returned_via_api():
    log_text = _read_log_text()
    _, production_v = _parse_log_versions(log_text)

    resp = _fetch_prompt(label="production")
    assert resp.status_code == 200, (
        f"Expected GET prompt by label='production' to return 200, "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()

    assert body.get("type") == "text", (
        f"Expected production prompt to have type='text', got: {body.get('type')!r}."
    )
    assert body.get("version") == production_v, (
        f"Expected production prompt version ({body.get('version')}) to equal "
        f"the version recorded in the log ({production_v})."
    )
    labels = body.get("labels") or []
    assert "production" in labels, (
        f"Expected production prompt labels to include 'production', got: {labels}."
    )

    prompt_body = body.get("prompt")
    assert isinstance(prompt_body, str), (
        f"Expected text prompt body to be a string, got {type(prompt_body).__name__}."
    )
    for var in ("{{criticlevel}}", "{{movie}}"):
        assert var in prompt_body, (
            f"Expected production text prompt to reference template variable {var}. "
            f"Got body:\n{prompt_body}"
        )


def test_staging_prompt_returned_via_api():
    log_text = _read_log_text()
    staging_v, _ = _parse_log_versions(log_text)

    resp = _fetch_prompt(label="staging")
    assert resp.status_code == 200, (
        f"Expected GET prompt by label='staging' to return 200, "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()

    assert body.get("type") == "text", (
        f"Expected staging prompt to have type='text', got: {body.get('type')!r}."
    )
    assert body.get("version") == staging_v, (
        f"Expected staging prompt version ({body.get('version')}) to equal "
        f"the version recorded in the log ({staging_v})."
    )

    labels = body.get("labels") or []
    assert "staging" in labels, (
        f"Expected staging prompt labels to include 'staging', got: {labels}."
    )
    assert "production" not in labels, (
        "Expected staging prompt labels to NOT include 'production' "
        f"(it must have moved to the newer version), got: {labels}."
    )

    prompt_body = body.get("prompt")
    assert isinstance(prompt_body, str), (
        f"Expected text prompt body to be a string, got {type(prompt_body).__name__}."
    )
    for var in ("{{criticlevel}}", "{{movie}}"):
        assert var in prompt_body, (
            f"Expected staging text prompt to reference template variable {var}. "
            f"Got body:\n{prompt_body}"
        )


def test_default_label_serves_production_version():
    log_text = _read_log_text()
    _, production_v = _parse_log_versions(log_text)

    resp = _fetch_prompt()  # no label -> defaults to "production"
    assert resp.status_code == 200, (
        f"Expected GET prompt with no label to return 200 (defaulting to production), "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("version") == production_v, (
        f"Expected the default (no-label) prompt fetch to return the production "
        f"version ({production_v}), but got version {body.get('version')}."
    )

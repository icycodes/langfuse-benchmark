import json
import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/myproject"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
TRACE_ID_RE = re.compile(r"^Trace ID:\s*([A-Za-z0-9_\-]+)\s*$", re.MULTILINE)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    assert value, f"Required environment variable {name} is not set in the verifier env."
    return value


@pytest.fixture(scope="session")
def langfuse_config():
    base_url = _required_env("LANGFUSE_BASE_URL").rstrip("/")
    public_key = _required_env("LANGFUSE_PUBLIC_KEY")
    secret_key = _required_env("LANGFUSE_SECRET_KEY")
    return {
        "base_url": base_url,
        "auth": (public_key, secret_key),
    }


@pytest.fixture(scope="session")
def run_id() -> str:
    return _required_env("ZEALT_RUN_ID")


@pytest.fixture(scope="session")
def expected_trace_name(run_id: str) -> str:
    return f"weather-assistant-{run_id}"


@pytest.fixture(scope="session")
def trace_id_from_log() -> str:
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task script ran."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        content = fh.read()
    match = TRACE_ID_RE.search(content)
    assert match, (
        f"Expected {LOG_FILE} to contain a line in the form 'Trace ID: <trace_id>'. "
        f"Got contents: {content!r}"
    )
    trace_id = match.group(1).strip()
    assert trace_id, "Captured trace_id from log file is empty."
    return trace_id


def test_log_file_contains_trace_id(trace_id_from_log: str):
    assert trace_id_from_log, "Log file did not contain a non-empty Trace ID line."


def test_package_json_declares_dependencies_and_start_script():
    package_json_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json_path), (
        f"Expected {package_json_path} to exist after the task is completed."
    )
    with open(package_json_path, "r", encoding="utf-8") as fh:
        pkg = json.load(fh)

    scripts = pkg.get("scripts") or {}
    assert "start" in scripts and isinstance(scripts["start"], str) and scripts["start"].strip(), (
        "package.json must define an `npm run start` script."
    )

    dependency_pool = {}
    for key in ("dependencies", "devDependencies"):
        section = pkg.get(key) or {}
        if isinstance(section, dict):
            dependency_pool.update(section)
    for dep in ("@langfuse/tracing", "@langfuse/otel", "@opentelemetry/sdk-node"):
        assert dep in dependency_pool, (
            f"package.json must declare a dependency on '{dep}'. "
            f"Got dependencies: {sorted(dependency_pool.keys())}"
        )


def test_source_uses_langfuse_tracing_primitives():
    required_substrings = (
        "LangfuseSpanProcessor",
        "startActiveObservation",
        "startObservation",
    )
    found = {s: False for s in required_substrings}
    candidate_exts = (".ts", ".mts", ".cts", ".tsx", ".js", ".mjs", ".cjs")
    for root, dirs, files in os.walk(PROJECT_DIR):
        # Skip dependency / build directories to keep the search bounded.
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".next", "build", ".turbo")]
        for fname in files:
            if not fname.endswith(candidate_exts):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            for needle in required_substrings:
                if needle in text:
                    found[needle] = True
        if all(found.values()):
            break

    missing = [s for s, ok in found.items() if not ok]
    assert not missing, (
        f"Could not find usage of the following Langfuse tracing primitives "
        f"in the project source: {missing}"
    )


def test_trace_listed_in_langfuse(langfuse_config, expected_trace_name, trace_id_from_log):
    list_url = f"{langfuse_config['base_url']}/api/public/traces"
    matched = None
    last_status = None
    last_payload_keys = None
    for attempt in range(12):
        resp = requests.get(
            list_url,
            params={"name": expected_trace_name, "limit": 50},
            auth=langfuse_config["auth"],
            timeout=30,
        )
        last_status = resp.status_code
        if resp.status_code == 200:
            payload = resp.json()
            last_payload_keys = list(payload.keys()) if isinstance(payload, dict) else None
            data = payload.get("data", []) if isinstance(payload, dict) else []
            for entry in data:
                if entry.get("name") == expected_trace_name and entry.get("id") == trace_id_from_log:
                    matched = entry
                    break
            if matched:
                break
        time.sleep(5)

    assert matched is not None, (
        f"Expected to find a trace with name '{expected_trace_name}' and id "
        f"'{trace_id_from_log}' via GET /api/public/traces. "
        f"Last status: {last_status}, last response keys: {last_payload_keys}."
    )


def test_trace_detail_has_nested_generation(langfuse_config, expected_trace_name, trace_id_from_log):
    detail_url = f"{langfuse_config['base_url']}/api/public/traces/{trace_id_from_log}"
    detail = None
    last_status = None
    for attempt in range(12):
        resp = requests.get(detail_url, auth=langfuse_config["auth"], timeout=30)
        last_status = resp.status_code
        if resp.status_code == 200:
            detail = resp.json()
            if detail and detail.get("observations"):
                break
        time.sleep(5)

    assert detail is not None, (
        f"Could not retrieve trace detail from GET /api/public/traces/{trace_id_from_log} "
        f"(last status: {last_status})."
    )

    assert detail.get("name") == expected_trace_name, (
        f"Trace name mismatch. Expected '{expected_trace_name}', got {detail.get('name')!r}."
    )

    assert detail.get("input") not in (None, "", {}, []), (
        f"Trace input is empty or missing. Got: {detail.get('input')!r}"
    )
    assert detail.get("output") not in (None, "", {}, []), (
        f"Trace output is empty or missing. Got: {detail.get('output')!r}"
    )

    observations = detail.get("observations") or []
    assert observations, "Trace detail must include at least one observation."

    generations = [
        obs
        for obs in observations
        if (obs.get("type") or "").upper() == "GENERATION"
        and obs.get("name") == "llm-call"
    ]
    assert generations, (
        f"Expected at least one observation with type GENERATION and name 'llm-call'. "
        f"Got observation names/types: "
        f"{[(o.get('name'), o.get('type')) for o in observations]}"
    )

    gen = generations[0]
    model_value = gen.get("model")
    assert isinstance(model_value, str) and model_value.strip(), (
        f"Generation observation 'llm-call' must include a non-empty 'model' attribute. "
        f"Got: {model_value!r}"
    )
    assert gen.get("input") not in (None, "", {}, []), (
        f"Generation observation 'llm-call' must have a non-empty input. "
        f"Got: {gen.get('input')!r}"
    )
    assert gen.get("output") not in (None, "", {}, []), (
        f"Generation observation 'llm-call' must have a non-empty output. "
        f"Got: {gen.get('output')!r}"
    )

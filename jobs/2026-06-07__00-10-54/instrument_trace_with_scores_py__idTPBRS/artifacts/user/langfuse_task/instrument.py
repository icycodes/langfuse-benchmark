#!/usr/bin/env python3
"""Instrument a nested Langfuse workflow and attach custom scores."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

from langfuse import get_client, propagate_attributes

TASK_DIR = Path("/home/user/langfuse_task")
LOG_FILE = TASK_DIR / "output.log"
MODEL_NAME = "gpt-3.5-turbo"


def enum_value(value: Any) -> Any:
    """Return enum.value when available, otherwise the raw value."""
    return getattr(value, "value", value)


def score_matches(
    score: Any,
    *,
    name: str,
    data_type: str,
    value: Any,
    trace_id: str,
    observation_id: str | None,
) -> bool:
    """Check whether a Langfuse score object has the expected fields."""
    score_value = getattr(score, "value", None)
    string_value = getattr(score, "string_value", None)

    if isinstance(value, float):
        value_ok = abs(float(score_value) - value) < 1e-9
    elif isinstance(value, str):
        value_ok = string_value == value or score_value == value
    else:
        value_ok = score_value == value

    return (
        getattr(score, "name", None) == name
        and enum_value(getattr(score, "data_type", None)) == data_type
        and value_ok
        and getattr(score, "trace_id", None) == trace_id
        and getattr(score, "observation_id", None) == observation_id
    )


def verify_persisted(langfuse: Any, trace_id: str, generation_id: str, run_id: str) -> None:
    """Poll the public API client until the trace, generation, and scores are visible."""
    expected_user_id = f"user-{run_id}"
    expected_session_id = f"session-{run_id}"
    expected_generation_name = f"summarize-{run_id}"

    deadline = time.time() + 60
    last_error = "verification did not run"

    while time.time() < deadline:
        try:
            trace = langfuse.api.trace.get(trace_id)
            if getattr(trace, "user_id", None) != expected_user_id:
                raise AssertionError(
                    f"trace user_id mismatch: {getattr(trace, 'user_id', None)!r}"
                )
            if getattr(trace, "session_id", None) != expected_session_id:
                raise AssertionError(
                    f"trace session_id mismatch: {getattr(trace, 'session_id', None)!r}"
                )

            observations = getattr(trace, "observations", []) or []
            generation = next(
                (
                    obs
                    for obs in observations
                    if getattr(obs, "id", None) == generation_id
                    and enum_value(getattr(obs, "type", None)) == "GENERATION"
                    and getattr(obs, "name", None) == expected_generation_name
                    and (
                        getattr(obs, "provided_model_name", None) == MODEL_NAME
                        or getattr(obs, "model", None) == MODEL_NAME
                    )
                ),
                None,
            )
            if generation is None:
                raise AssertionError("matching generation observation not visible yet")

            scores_response = langfuse.api.scores.get_many(trace_id=trace_id, limit=100)
            scores = getattr(scores_response, "data", []) or []

            expected_scores = [
                ("user_satisfaction", "NUMERIC", 0.8, None),
                ("hallucination", "BOOLEAN", 0, generation_id),
                ("relevance", "CATEGORICAL", "high", generation_id),
            ]
            missing = [
                name
                for name, data_type, value, observation_id in expected_scores
                if not any(
                    score_matches(
                        score,
                        name=name,
                        data_type=data_type,
                        value=value,
                        trace_id=trace_id,
                        observation_id=observation_id,
                    )
                    for score in scores
                )
            ]
            if missing:
                raise AssertionError(f"missing scores: {', '.join(missing)}")

            return
        except Exception as exc:  # noqa: BLE001 - keep polling while ingestion catches up.
            last_error = str(exc)
            time.sleep(2)

    raise RuntimeError(f"Langfuse verification failed: {last_error}")


def main() -> int:
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise RuntimeError("ZEALT_RUN_ID must be set")

    TASK_DIR.mkdir(parents=True, exist_ok=True)

    user_id = f"user-{run_id}"
    session_id = f"session-{run_id}"
    root_name = f"process-document-{run_id}"
    generation_name = f"summarize-{run_id}"

    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    generation_id: str | None = None

    with propagate_attributes(user_id=user_id, session_id=session_id):
        with langfuse.start_as_current_observation(
            trace_context={"trace_id": trace_id},
            name=root_name,
            as_type="span",
            input=f"Document payload for run {run_id}",
        ) as root_span:
            trace_id = langfuse.get_current_trace_id() or getattr(root_span, "trace_id", trace_id)

            generation_input = [
                {
                    "role": "system",
                    "content": "Summarize the supplied document in one sentence.",
                },
                {
                    "role": "user",
                    "content": f"Document for run {run_id}: Langfuse records nested observations and scores.",
                },
            ]
            generation_output = (
                "Langfuse captured a nested generation for a fabricated document summary."
            )

            with langfuse.start_as_current_observation(
                name=generation_name,
                as_type="generation",
                model=MODEL_NAME,
                input=generation_input,
                output=generation_output,
            ) as generation:
                generation_id = langfuse.get_current_observation_id() or getattr(
                    generation, "id", None
                )
                if generation_id is None:
                    raise RuntimeError("Could not capture generation observation ID")

            root_span.update(output=f"Processed document for run {run_id}")

    if generation_id is None:
        raise RuntimeError("Generation observation ID was not captured")

    langfuse.create_score(
        trace_id=trace_id,
        name="user_satisfaction",
        value=0.8,
        data_type="NUMERIC",
    )
    langfuse.create_score(
        trace_id=trace_id,
        observation_id=generation_id,
        name="hallucination",
        value=0,
        data_type="BOOLEAN",
    )
    langfuse.create_score(
        trace_id=trace_id,
        observation_id=generation_id,
        name="relevance",
        value="high",
        data_type="CATEGORICAL",
    )

    langfuse.flush()
    verify_persisted(langfuse, trace_id, generation_id, run_id)

    LOG_FILE.write_text(
        "\n".join(
            [
                f"Trace ID: {trace_id}",
                f"Generation ID: {generation_id}",
                f"User ID: {user_id}",
                f"Session ID: {session_id}",
                "Status: OK",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Trace ID: {trace_id}")
    print(f"Generation ID: {generation_id}")
    print("Status: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

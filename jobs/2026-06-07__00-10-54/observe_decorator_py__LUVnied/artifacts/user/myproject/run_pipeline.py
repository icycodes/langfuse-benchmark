#!/usr/bin/env python3
"""Instrument a simple multi-step pipeline with Langfuse @observe decorators."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from langfuse import get_client, observe, propagate_attributes

PROJECT_DIR = Path("/home/user/myproject")
OUTPUT_LOG = PROJECT_DIR / "output.log"


def _require_run_id() -> str:
    """Return the verifier-provided run id from the environment."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise RuntimeError("ZEALT_RUN_ID environment variable is required")
    return run_id


@observe(name="simulated-llm-call", as_type="generation")
def simulated_llm_call(prompt: str) -> str:
    """Simulate an LLM generation and attach generation metadata."""
    response = "This is a simulated LLM response for the observed pipeline."

    langfuse = get_client()
    langfuse.update_current_generation(
        model="simulated-model-v1",
        model_parameters={"temperature": 0.0, "max_tokens": 64},
        input=prompt,
        output=response,
        usage_details={"input": len(prompt.split()), "output": len(response.split())},
    )

    return response


@observe(name="observed-query-pipeline", as_type="span")
def run_pipeline(query: str, *, run_id: str) -> Dict[str, Any]:
    """Run a small observed query-processing pipeline."""
    user_id = f"obs-deco-user-{run_id}"
    session_id = f"obs-deco-session-{run_id}"
    tags = ["obs-decorator", f"harbor-{run_id}"]

    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=tags,
        trace_name="observed-query-pipeline",
    ):
        normalized_query = query.strip()
        prompt = f"Answer the user's question succinctly: {normalized_query}"
        answer = simulated_llm_call(prompt)
        trace_id = get_client().get_current_trace_id()

        return {
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "tags": tags,
            "query": normalized_query,
            "answer": answer,
        }


def main() -> None:
    run_id = _require_run_id()
    langfuse = get_client()

    result = run_pipeline("How should I instrument this pipeline?", run_id=run_id)
    trace_id = result["trace_id"]
    if not trace_id:
        raise RuntimeError("Langfuse did not provide a current trace id")

    langfuse.flush()

    OUTPUT_LOG.write_text(f"Trace ID: {trace_id}\n", encoding="utf-8")
    print(f"Trace ID: {trace_id}")


if __name__ == "__main__":
    main()

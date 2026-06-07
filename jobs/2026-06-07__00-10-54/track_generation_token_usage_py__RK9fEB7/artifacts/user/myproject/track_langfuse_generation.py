#!/usr/bin/env python3
"""Create a Langfuse generation with provider-supplied usage and cost details."""

from __future__ import annotations

import os
from pathlib import Path

from langfuse import get_client


INPUT_MESSAGES = [
    {"role": "user", "content": "Summarize Langfuse in one sentence."},
]
OUTPUT_TEXT = (
    "Langfuse is an open-source LLM engineering platform for observability, "
    "prompts, and evals."
)
USAGE_DETAILS = {"input": 25, "output": 40, "total": 65}
COST_DETAILS = {"input": 0.000125, "output": 0.00040, "total": 0.000525}


def main() -> None:
    run_id = os.environ["ZEALT_RUN_ID"]
    langfuse = get_client()

    trace_id: str | None = None
    span_name = f"chat-pipeline-{run_id}"

    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
    ):
        trace_id = langfuse.get_current_trace_id()

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="chat-completion",
            model="gpt-4o-mini",
            input=INPUT_MESSAGES,
            output=OUTPUT_TEXT,
            usage_details=USAGE_DETAILS,
            cost_details=COST_DETAILS,
        ):
            # This block simulates the provider call. The exact provider-reported
            # usage and cost are supplied above for direct ingestion by Langfuse.
            pass

    if not trace_id:
        raise RuntimeError("Langfuse did not provide a trace ID")

    langfuse.flush()

    output_path = Path(__file__).resolve().parent / "output.log"
    output_path.write_text(f"Trace ID: {trace_id}\n", encoding="utf-8")


if __name__ == "__main__":
    main()

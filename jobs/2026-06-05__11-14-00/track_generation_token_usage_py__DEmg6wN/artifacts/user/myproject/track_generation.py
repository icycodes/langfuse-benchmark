#!/usr/bin/env python3
"""Track LLM generation token usage and cost with the Langfuse Python SDK."""

import os
from langfuse import get_client


def main():
    run_id = os.environ["ZEALT_RUN_ID"]
    langfuse = get_client()

    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"chat-pipeline-{run_id}",
    ) as span:
        with span.start_as_current_observation(
            as_type="generation",
            name="chat-completion",
            model="gpt-4o-mini",
            input=[{"role": "user", "content": "Summarize Langfuse in one sentence."}],
            output="Langfuse is an open-source LLM engineering platform for observability, prompts, and evals.",
            usage_details={"input": 25, "output": 40, "total": 65},
            cost_details={"input": 0.000125, "output": 0.00040, "total": 0.000525},
        ) as generation:
            pass

        trace_id = langfuse.get_current_trace_id()

    langfuse.flush()

    # Write trace ID to log file
    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

    print(f"Trace ID: {trace_id}")


if __name__ == "__main__":
    main()
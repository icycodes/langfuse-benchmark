"""
Pipeline instrumented with Langfuse @observe() decorator.

Trace attributes:
  - user_id    = obs-deco-user-{ZEALT_RUN_ID}
  - session_id = obs-deco-session-{ZEALT_RUN_ID}
  - tags       = ["obs-decorator", "harbor-{ZEALT_RUN_ID}"]

Observations:
  1. pipeline_run  – SPAN  (top-level, created by @observe())
     └─ 2. llm_call – GENERATION (nested, created by @observe(as_type="generation"))
"""

import os

from langfuse import get_client, observe, propagate_attributes

# ---------------------------------------------------------------------------
# Read run-id from environment
# ---------------------------------------------------------------------------
run_id = os.environ.get("ZEALT_RUN_ID", "default")

user_id    = f"obs-deco-user-{run_id}"
session_id = f"obs-deco-session-{run_id}"
tags       = ["obs-decorator", f"harbor-{run_id}"]

# ---------------------------------------------------------------------------
# Langfuse client (singleton; picks up LANGFUSE_* env-vars automatically)
# ---------------------------------------------------------------------------
langfuse = get_client()

# Module-level variable to capture the trace id from inside the decorator
_captured_trace_id: list = []


# ---------------------------------------------------------------------------
# Nested generation – simulates an LLM call
# ---------------------------------------------------------------------------
@observe(name="llm_call", as_type="generation")
def llm_call(prompt: str) -> str:
    """Simulated LLM generation (no real API call)."""
    langfuse.update_current_generation(
        model="gpt-4o-mini",
        input={"prompt": prompt},
    )
    response = "The capital of France is Paris."
    langfuse.update_current_generation(output=response)
    return response


# ---------------------------------------------------------------------------
# Top-level pipeline – SPAN
# ---------------------------------------------------------------------------
@observe(name="pipeline_run")
def pipeline_run(user_query: str) -> str:
    """Top-level pipeline span that wraps the LLM call."""
    # Propagate trace-level attributes (user_id, session_id, tags) to this
    # span and all child observations created inside the context.
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=tags,
    ):
        # Capture trace id while the OTel context is still active
        tid = langfuse.get_current_trace_id()
        if tid:
            _captured_trace_id.append(tid)

        result = llm_call(user_query)

    return result


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    answer = pipeline_run("What is the capital of France?")

    # Flush all queued telemetry events before process exits
    langfuse.flush()

    trace_id = _captured_trace_id[0] if _captured_trace_id else None

    # Write the trace id to the log file expected by the verifier
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
    with open(log_path, "w") as fh:
        fh.write(f"Trace ID: {trace_id}\n")

    print(f"Pipeline answer : {answer}")
    print(f"Trace ID        : {trace_id}")
    print(f"Log written to  : {log_path}")

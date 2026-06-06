import os
from langfuse import observe, get_client, propagate_attributes

# Read run-id from environment
run_id = os.environ["ZEALT_RUN_ID"]

# Build collision-free identifiers
session_id = f"obs-deco-session-{run_id}"
user_id = f"obs-deco-user-{run_id}"
tags = ["obs-decorator", f"harbor-{run_id}"]


@observe(as_type="generation", name="llm-call")
def simulate_llm_call(prompt: str) -> str:
    """Simulate an LLM call with a hard-coded response."""
    langfuse_client = get_client()
    langfuse_client.update_current_generation(model="gpt-4o")
    return "This is a simulated LLM response."


@observe(name="pipeline")
def run_pipeline(query: str) -> dict:
    """Top-level pipeline function (span) that calls the LLM."""
    langfuse_client = get_client()
    trace_id = langfuse_client.get_current_trace_id()
    result = simulate_llm_call(query)
    return {"trace_id": trace_id, "result": result}


if __name__ == "__main__":
    langfuse_client = get_client()

    # Propagate trace-level attributes (user_id, session_id, tags)
    # so they are attached to the resulting Langfuse trace
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=tags,
    ):
        output = run_pipeline("What is the capital of France?")

    trace_id = output["trace_id"]

    # Flush all queued events to Langfuse before exiting
    langfuse_client.flush()

    # Write the trace ID to the log file
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
    with open(log_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

    print(f"Trace ID: {trace_id}")
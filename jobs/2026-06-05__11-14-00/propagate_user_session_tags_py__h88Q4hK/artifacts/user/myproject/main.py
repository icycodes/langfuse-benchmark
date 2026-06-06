import os
import langfuse

# Read run ID from environment
run_id = os.environ["ZEALT_RUN_ID"]

# Get the Langfuse client (configured from LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)
langfuse_client = langfuse.get_client()

# Propagate trace-level attributes (user_id, session_id, tags) to all observations
with langfuse.propagate_attributes(
    user_id=f"user-{run_id}",
    session_id=f"session-{run_id}",
    tags=[f"demo-{run_id}", "python-sdk"],
):
    # Root span named "chat-turn"
    with langfuse_client.start_as_current_span(name="chat-turn") as root_span:
        # Nested generation named "assistant-reply"
        with langfuse_client.start_as_current_observation(
            name="assistant-reply",
            as_type="generation",
            input={"prompt": "Hello"},
            output={"text": "Hi there!"},
        ) as gen:
            pass

        # Get the trace ID while still inside the span context
        trace_id = langfuse_client.get_current_trace_id()

# Write trace ID to log file
with open("/home/user/myproject/output.log", "w") as f:
    f.write(f"Trace ID: {trace_id}\n")

# Flush to ensure trace is delivered to Langfuse Cloud before exit
langfuse_client.flush()
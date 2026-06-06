"""
Langfuse trace demo: one `chat-turn` root span containing one
`assistant-reply` generation observation, with user_id, session_id,
and tags propagated via propagate_attributes.
"""

import os
from langfuse import get_client, propagate_attributes

# --------------------------------------------------------------------------- #
# Read runtime configuration from the environment
# --------------------------------------------------------------------------- #
run_id = os.environ["ZEALT_RUN_ID"]

# Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
# and LANGFUSE_BASE_URL from the environment automatically)
client = get_client()

# --------------------------------------------------------------------------- #
# Build the trace
# --------------------------------------------------------------------------- #
with propagate_attributes(
    user_id=f"user-{run_id}",
    session_id=f"session-{run_id}",
    tags=[f"demo-{run_id}", "python-sdk"],
):
    with client.start_as_current_observation(name="chat-turn") as root_span:
        trace_id = client.get_current_trace_id()

        # Nested generation observation
        with client.start_as_current_observation(
            name="assistant-reply",
            as_type="generation",
            input={"role": "user", "content": "Hello, how are you?"},
            output={"role": "assistant", "content": "I'm doing well, thank you!"},
        ):
            pass  # No real LLM call needed

# --------------------------------------------------------------------------- #
# Flush so the trace is reliably delivered before process exit
# --------------------------------------------------------------------------- #
client.flush()

# --------------------------------------------------------------------------- #
# Write the trace ID to the log file
# --------------------------------------------------------------------------- #
log_path = os.path.join(os.path.dirname(__file__), "output.log")
with open(log_path, "w") as f:
    f.write(f"Trace ID: {trace_id}\n")

print(f"Trace ID: {trace_id}")
print(f"Log written to: {log_path}")

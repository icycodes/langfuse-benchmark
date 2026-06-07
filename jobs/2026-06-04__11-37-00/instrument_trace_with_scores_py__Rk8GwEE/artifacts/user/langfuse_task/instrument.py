#!/usr/bin/env python3
"""Instrument a document-processing workflow with Langfuse nested observations and custom scores."""

import os
from langfuse import get_client
from langfuse._client.propagation import propagate_attributes

# Read run ID from environment
run_id = os.environ["ZEALT_RUN_ID"]

# Initialise the Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env)
langfuse = get_client()

# Derive namespaced identifiers
span_name = f"process-document-{run_id}"
gen_name = f"summarize-{run_id}"
user_id = f"user-{run_id}"
session_id = f"session-{run_id}"

# Variables to capture IDs inside context managers
trace_id = None
generation_id = None

# 1. Open root span, propagate user_id / session_id to the trace, then open nested generation
with langfuse.start_as_current_observation(name=span_name, as_type="span") as span:
    # 2. Propagate user_id and session_id so they appear on the trace
    with propagate_attributes(user_id=user_id, session_id=session_id):
        # 3. Nested generation
        with langfuse.start_as_current_observation(
            name=gen_name,
            as_type="generation",
            model="gpt-3.5-turbo",
            input=[{"role": "user", "content": "Summarize the following document: ..."}],
            output="The document discusses the key findings of the annual report.",
        ) as generation:
            # 4. Capture IDs while still inside the contexts
            trace_id = langfuse.get_current_trace_id()
            generation_id = langfuse.get_current_observation_id()

# 5. Attach three custom scores after both contexts are closed
# Trace-level numeric score
langfuse.create_score(
    trace_id=trace_id,
    name="user_satisfaction",
    value=0.8,
    data_type="NUMERIC",
)

# Observation-level boolean score on the generation
langfuse.create_score(
    trace_id=trace_id,
    observation_id=generation_id,
    name="hallucination",
    value=0,
    data_type="BOOLEAN",
)

# Observation-level categorical score on the generation
langfuse.create_score(
    trace_id=trace_id,
    observation_id=generation_id,
    name="relevance",
    value="high",
    data_type="CATEGORICAL",
)

# Flush so everything is delivered to the Langfuse server
langfuse.flush()

# Write output log
log_path = "/home/user/langfuse_task/output.log"
with open(log_path, "w") as f:
    f.write(f"Trace ID: {trace_id}\n")
    f.write(f"Generation ID: {generation_id}\n")
    f.write(f"User ID: {user_id}\n")
    f.write(f"Session ID: {session_id}\n")
    f.write(f"Status: OK\n")

print(f"Trace ID: {trace_id}")
print(f"Generation ID: {generation_id}")
print(f"User ID: {user_id}")
print(f"Session ID: {session_id}")
print("Status: OK")
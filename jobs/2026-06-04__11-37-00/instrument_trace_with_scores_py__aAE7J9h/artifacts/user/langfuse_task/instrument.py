"""
Instrument a workflow with nested observations and custom scores using Langfuse Python SDK.
"""

import os
import sys

from langfuse import get_client, propagate_attributes

# Read environment variables
RUN_ID = os.environ["ZEALT_RUN_ID"]
USER_ID = f"user-{RUN_ID}"
SESSION_ID = f"session-{RUN_ID}"
SPAN_NAME = f"process-document-{RUN_ID}"
GENERATION_NAME = f"summarize-{RUN_ID}"

# Initialise the SDK — reads credentials from env vars automatically
langfuse = get_client()

trace_id = None
generation_id = None

# Propagate user_id and session_id so they appear on the trace
with propagate_attributes(user_id=USER_ID, session_id=SESSION_ID):
    # Open the root span
    with langfuse.start_as_current_observation(
        name=SPAN_NAME,
        as_type="span",
    ) as root_span:
        # Capture trace ID while inside the context
        trace_id = langfuse.get_current_trace_id()

        # Open the nested generation
        with langfuse.start_as_current_observation(
            name=GENERATION_NAME,
            as_type="generation",
            model="gpt-3.5-turbo",
            input=[
                {"role": "system", "content": "You are a helpful assistant that summarises documents."},
                {"role": "user", "content": "Please summarise the following document: [document text here]"},
            ],
            output="The document discusses key topics including AI observability, tracing, and monitoring.",
        ) as generation:
            # Capture observation ID while still inside the generation context
            generation_id = langfuse.get_current_observation_id()

# Both contexts are now closed — attach the three custom scores

# 1. Trace-level numeric satisfaction score (no observation_id)
langfuse.create_score(
    trace_id=trace_id,
    name="user_satisfaction",
    value=0.8,
    data_type="NUMERIC",
)

# 2. Observation-level boolean hallucination score
langfuse.create_score(
    trace_id=trace_id,
    observation_id=generation_id,
    name="hallucination",
    value=0,
    data_type="BOOLEAN",
)

# 3. Observation-level categorical relevance score
langfuse.create_score(
    trace_id=trace_id,
    observation_id=generation_id,
    name="relevance",
    value="high",
    data_type="CATEGORICAL",
)

# Flush all queued events to the Langfuse server before exiting
langfuse.flush()

print(f"Trace ID: {trace_id}")
print(f"Generation ID: {generation_id}")
print(f"User ID: {USER_ID}")
print(f"Session ID: {SESSION_ID}")
print("Status: OK")

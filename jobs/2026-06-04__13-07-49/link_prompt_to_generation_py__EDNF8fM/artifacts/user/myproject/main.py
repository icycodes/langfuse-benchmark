"""
Langfuse Prompt Linking Demo
----------------------------
1. Creates a chat-type prompt named `movie-critic-chat-{run_id}` with the
   `production` label.
2. Fetches the `production` version at runtime and compiles it with template
   variables.
3. Emits a trace containing a single GENERATION observation linked to the
   fetched prompt.
4. Writes the trace ID to /home/user/myproject/output.log in the format
   `Trace ID: <trace_id>`.
"""

import os

from langfuse import get_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RUN_ID = os.environ["ZEALT_RUN_ID"]
PROMPT_NAME = f"movie-critic-chat-{RUN_ID}"
LOG_FILE = "/home/user/myproject/output.log"

# get_client() reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
langfuse = get_client()

# ---------------------------------------------------------------------------
# 1. Create (or update) a versioned chat prompt labelled `production`
# ---------------------------------------------------------------------------
prompt_messages = [
    {
        "role": "system",
        "content": (
            "You are a {{criticlevel}} movie critic. "
            "Provide an insightful review of the given movie."
        ),
    },
    {
        "role": "user",
        "content": "Please review the movie: {{movie}}",
    },
]

langfuse.create_prompt(
    name=PROMPT_NAME,
    type="chat",
    prompt=prompt_messages,
    labels=["production"],
)

# ---------------------------------------------------------------------------
# 2. Fetch the `production` version and compile with template variables
# ---------------------------------------------------------------------------
prompt = langfuse.get_prompt(PROMPT_NAME, type="chat", label="production")

compiled_messages = prompt.compile(criticlevel="expert", movie="Dune: Part Two")

# ---------------------------------------------------------------------------
# 3. Emit a trace with a linked GENERATION observation
# ---------------------------------------------------------------------------
trace_id: str | None = None

with langfuse.start_as_current_observation(
    as_type="generation",
    name=f"movie-critic-generation-{RUN_ID}",
    model="gpt-4o",
    input=compiled_messages,
    prompt=prompt,
) as generation:
    # Capture the trace ID while still inside the active observation context
    trace_id = langfuse.get_current_trace_id()

    # Simulate LLM output (no real LLM call required for linking)
    generation.update(
        output="Dune: Part Two is a masterful continuation of Denis Villeneuve's vision.",
    )

# ---------------------------------------------------------------------------
# 4. Flush telemetry before exit
# ---------------------------------------------------------------------------
langfuse.flush()

# ---------------------------------------------------------------------------
# 5. Write trace ID to log file
# ---------------------------------------------------------------------------
if trace_id is None:
    raise RuntimeError("Failed to capture trace ID inside the generation context.")

with open(LOG_FILE, "w") as f:
    f.write(f"Trace ID: {trace_id}\n")

print(f"Done. Trace ID: {trace_id}")
print(f"Log written to: {LOG_FILE}")

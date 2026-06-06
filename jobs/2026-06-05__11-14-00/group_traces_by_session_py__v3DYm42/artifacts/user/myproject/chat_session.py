"""Chat session script that emits three Langfuse traces grouped into one session."""

import os
from langfuse import get_client, propagate_attributes

# ---------------------------------------------------------------------------
# Derive identifiers from ZEALT_RUN_ID
# ---------------------------------------------------------------------------
run_id = os.environ.get("ZEALT_RUN_ID", "default")
session_id = f"chat-session-{run_id}"
user_id = f"chat-user-{run_id}"
tag = f"harbor-demo-{run_id}"

# ---------------------------------------------------------------------------
# Fix LANGFUSE_HOST if it contains an unexpanded shell variable
# ---------------------------------------------------------------------------
langfuse_host = os.environ.get("LANGFUSE_HOST", "")
if langfuse_host.startswith("$") or not langfuse_host:
    os.environ["LANGFUSE_HOST"] = "https://us.cloud.langfuse.com"

# ---------------------------------------------------------------------------
# Initialise the Langfuse client
# ---------------------------------------------------------------------------
langfuse = get_client()

# ---------------------------------------------------------------------------
# Turn 1 – greeting
# ---------------------------------------------------------------------------
with langfuse.start_as_current_observation(
    name="greeting-turn", as_type="span"
) as span:
    with propagate_attributes(
        user_id=user_id, session_id=session_id, tags=[tag]
    ):
        with span.start_as_current_observation(
            name="greeting-generation", as_type="generation", model="gpt-4o-mini"
        ) as gen:
            gen.update(output="Hello! How can I help you today?")

# ---------------------------------------------------------------------------
# Turn 2 – follow-up
# ---------------------------------------------------------------------------
with langfuse.start_as_current_observation(
    name="followup-turn", as_type="span"
) as span:
    with propagate_attributes(
        user_id=user_id, session_id=session_id, tags=[tag]
    ):
        with span.start_as_current_observation(
            name="followup-generation", as_type="generation", model="gpt-4o-mini"
        ) as gen:
            gen.update(output="Sure, I can help with that!")

# ---------------------------------------------------------------------------
# Turn 3 – farewell
# ---------------------------------------------------------------------------
with langfuse.start_as_current_observation(
    name="farewell-turn", as_type="span"
) as span:
    with propagate_attributes(
        user_id=user_id, session_id=session_id, tags=[tag]
    ):
        with span.start_as_current_observation(
            name="farewell-generation", as_type="generation", model="gpt-4o-mini"
        ) as gen:
            gen.update(output="Goodbye! Have a great day!")

# ---------------------------------------------------------------------------
# Flush all traces before exit
# ---------------------------------------------------------------------------
langfuse.flush()

# ---------------------------------------------------------------------------
# Append session ID to the log file
# ---------------------------------------------------------------------------
log_path = "/home/user/myproject/output.log"
with open(log_path, "a") as f:
    f.write(f"Session ID: {session_id}\n")
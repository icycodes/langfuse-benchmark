import os
import langfuse
from langfuse import Langfuse

# Read run-id from environment
run_id = os.environ["ZEALT_RUN_ID"]

# Derive identifiers
session_id = f"chat-session-{run_id}"
user_id = f"chat-user-{run_id}"
tag = f"harbor-demo-{run_id}"

# Initialize Langfuse client (credentials from env vars)
lf = Langfuse(host="https://us.cloud.langfuse.com")

# Define the three chat turns
turns = [
    {
        "name": "greeting-turn",
        "input": "Hello! How are you?",
        "output": "Hello! I'm doing well, thank you for asking. How can I help you today?",
    },
    {
        "name": "followup-turn",
        "input": "Can you tell me a fun fact?",
        "output": "Sure! Honey never spoils — archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible.",
    },
    {
        "name": "farewell-turn",
        "input": "Thanks, goodbye!",
        "output": "You're welcome! Goodbye and have a wonderful day!",
    },
]

# Emit one trace per chat turn, all linked to the same session
for turn in turns:
    with langfuse.propagate_attributes(
        session_id=session_id,
        user_id=user_id,
        tags=[tag],
        trace_name=turn["name"],
    ):
        with lf.start_as_current_observation(
            as_type="span",
            name=turn["name"],
            input=turn["input"],
        ) as root_span:
            # Nested generation (simulated LLM response)
            with lf.start_as_current_observation(
                as_type="generation",
                name=f"{turn['name']}-generation",
                model="gpt-4o-mini",
                input=turn["input"],
                output=turn["output"],
            ):
                pass  # No real LLM call needed

            root_span.update(output=turn["output"])

# Flush to ensure all spans are delivered before the process exits
lf.flush()

# Write the session ID to the log file
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
with open(log_path, "a") as f:
    f.write(f"Session ID: {session_id}\n")

print(f"Done. Session ID: {session_id}")

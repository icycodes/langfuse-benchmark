import json
import os

from langfuse import get_client

# Initialize Langfuse client (picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
# and LANGFUSE_BASE_URL from environment variables automatically)
langfuse = get_client()

# Read per-trial isolation ID
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"movie-critic-chat-{run_id}"

# Create the chat prompt with a message placeholder
langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=[
        {"role": "system", "content": "You are an {{criticlevel}} movie critic"},
        {"type": "placeholder", "name": "chat_history"},
        {"role": "user", "content": "What should I watch next?"},
    ],
    labels=["production"],
)

# Fetch the prompt back from Langfuse
prompt = langfuse.get_prompt(prompt_name, type="chat")

# Compile with variable substitution and placeholder resolution
compiled = prompt.compile(
    criticlevel="expert",
    chat_history=[
        {"role": "user", "content": "I love Ron Fricke movies like Baraka"},
        {"role": "user", "content": "Also, the Korean movie Memories of a Murderer"},
    ],
)

# Write results to the log file
output_path = "/home/user/myproject/output.log"
with open(output_path, "w") as f:
    f.write(f"Prompt name: {prompt_name}\n")
    f.write(f"Compiled prompt: {json.dumps(compiled)}\n")

print(f"Done. Log written to {output_path}")

# Flush any pending events before exiting
langfuse.flush()

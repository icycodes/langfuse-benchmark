#!/usr/bin/env python3
"""Create a Langfuse chat prompt with message placeholders, compile it, and log the result."""

import json
import os

from langfuse import get_client

# Read environment variables
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"movie-critic-chat-{run_id}"

# Instantiate the Langfuse client (picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)
langfuse = get_client()

# Define the chat prompt messages with a message placeholder
prompt_messages = [
    {"role": "system", "content": "You are an {{criticlevel}} movie critic"},
    {"type": "placeholder", "name": "chat_history"},
    {"role": "user", "content": "What should I watch next?"},
]

# Create the chat prompt in Langfuse with the "production" label
langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=prompt_messages,
    labels=["production"],
)

# Fetch the prompt back from Langfuse
prompt = langfuse.get_prompt(prompt_name)

# Compile the prompt with variable and placeholder values
compiled = prompt.compile(
    criticlevel="expert",
    chat_history=[
        {"role": "user", "content": "I love Ron Fricke movies like Baraka"},
        {"role": "user", "content": "Also, the Korean movie Memories of a Murderer"},
    ],
)

# Write the log file
output_path = "/home/user/myproject/output.log"
with open(output_path, "w") as f:
    f.write(f"Prompt name: {prompt_name}\n")
    f.write(f"Compiled prompt: {json.dumps(compiled)}\n")

# Flush pending events to ensure data is sent to Langfuse
langfuse.flush()
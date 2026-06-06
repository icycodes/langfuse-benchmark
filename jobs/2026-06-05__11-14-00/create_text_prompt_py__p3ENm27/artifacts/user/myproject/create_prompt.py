#!/usr/bin/env python3
"""Create a text prompt in Langfuse using the Python SDK."""

import os
from langfuse import get_client

# Initialise the Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env)
langfuse = get_client()

# Build the prompt name using the run-id for isolation
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"movie-critic-text-{run_id}"

# Create the text prompt via the SDK
result = langfuse.create_prompt(
    name=prompt_name,
    type="text",
    prompt="You are a movie critic. Write a review for the movie '{{movie_title}}'. Consider its plot, acting, and cinematography.",
    config={
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 512,
    },
    labels=["production"],
    tags=["movie-review", "critic"],
)

# Flush pending background work before exit
langfuse.flush()

# Log the results for auditing
log_path = "/home/user/myproject/output.log"
with open(log_path, "a") as f:
    f.write(f"Prompt Name: {result.name}\n")
    f.write(f"Prompt Version: {result.version}\n")

print(f"Created prompt: {result.name} (version {result.version})")
print(f"Log written to {log_path}")
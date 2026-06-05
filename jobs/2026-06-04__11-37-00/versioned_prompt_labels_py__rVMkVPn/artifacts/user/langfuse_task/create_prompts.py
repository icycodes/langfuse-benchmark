#!/usr/bin/env python3
"""Create two versions of a movie-critic chat prompt in Langfuse."""

import os
from langfuse import Langfuse

# --- Initialise SDK (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env) ---
langfuse = Langfuse()

# --- Prompt name -----------------------------------------------------------
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"movie-critic-chat-{run_id}"

# --- Version 1: baseline (label: staging) ---------------------------------
v1 = langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=[
        {"role": "system", "content": "You are a {{criticlevel}} movie critic who provides thoughtful reviews."},
        {"role": "user", "content": "Please review the movie {{movie}}."},
    ],
    labels=["staging"],
)

# --- Version 2: enhanced (label: production) ------------------------------
v2 = langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=[
        {"role": "system", "content": "You are a {{criticlevel}} movie critic specialising in {{genre}} films who provides detailed, thoughtful reviews."},
        {"role": "user", "content": "Please review the movie {{movie}} in the {{genre}} genre."},
    ],
    labels=["production"],
)

# --- Flush background events ----------------------------------------------
langfuse.flush()

# --- Write log file --------------------------------------------------------
log_path = "/home/user/langfuse_task/output.log"
with open(log_path, "w") as f:
    f.write(f"Prompt name: {prompt_name}\n")
    f.write(f"Staging version: {v1.version}\n")
    f.write(f"Production version: {v2.version}\n")

print(f"Done – log written to {log_path}")
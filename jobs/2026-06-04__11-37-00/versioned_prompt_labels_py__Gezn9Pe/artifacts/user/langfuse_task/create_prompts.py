import os
from langfuse import Langfuse

# Read environment variables
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"movie-critic-chat-{run_id}"

# Initialise the Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
# and LANGFUSE_BASE_URL automatically from the environment)
client = Langfuse()

# ------------------------------------------------------------------
# Version 1 – baseline prompt, labeled "staging"
# Variables: {{criticlevel}}, {{movie}}
# ------------------------------------------------------------------
version1_messages = [
    {
        "role": "system",
        "content": (
            "You are a movie critic with a {{criticlevel}} level of expertise. "
            "Provide honest, thoughtful reviews."
        ),
    },
    {
        "role": "user",
        "content": "Please write a review for the movie '{{movie}}'.",
    },
]

prompt_v1 = client.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=version1_messages,
    labels=["staging"],
)

# ------------------------------------------------------------------
# Version 2 – enhanced prompt, labeled "production"
# Variables: {{criticlevel}}, {{movie}}, {{genre}}
# ------------------------------------------------------------------
version2_messages = [
    {
        "role": "system",
        "content": (
            "You are a movie critic with a {{criticlevel}} level of expertise "
            "who specialises in the {{genre}} genre. "
            "Provide honest, detailed, and insightful reviews."
        ),
    },
    {
        "role": "user",
        "content": (
            "Please write an in-depth review for the {{genre}} movie '{{movie}}', "
            "highlighting its strengths and weaknesses."
        ),
    },
]

prompt_v2 = client.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=version2_messages,
    labels=["production"],
)

# Ensure all background events are delivered before the script exits
client.flush()

# ------------------------------------------------------------------
# Write the log file
# ------------------------------------------------------------------
log_path = "/home/user/langfuse_task/output.log"
log_lines = [
    f"Prompt name: {prompt_name}",
    f"Staging version: {prompt_v1.version}",
    f"Production version: {prompt_v2.version}",
]

with open(log_path, "w") as f:
    f.write("\n".join(log_lines) + "\n")

print("\n".join(log_lines))
print(f"\nLog written to {log_path}")

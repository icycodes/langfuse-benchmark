#!/usr/bin/env python3
"""Link a Langfuse Prompt to a Generation Observation.

Creates a versioned chat prompt, fetches its production version,
emits a trace with a linked generation observation, and logs the trace ID.
"""

import os
from langfuse import Langfuse

def main():
    run_id = os.environ["ZEALT_RUN_ID"]
    prompt_name = f"movie-critic-chat-{run_id}"

    langfuse = Langfuse()

    # 1. Create a chat-type prompt with the 'production' label.
    #    Template variables use mustache-style {{variable}} syntax.
    langfuse.create_prompt(
        name=prompt_name,
        type="chat",
        prompt=[
            {"role": "system", "content": "You are a {{criticlevel}} movie critic."},
            {"role": "user", "content": "Review the movie {{movie}}."},
        ],
        labels=["production"],
    )

    # 2. Fetch the production version of the prompt.
    prompt = langfuse.get_prompt(prompt_name, label="production", type="chat")

    # 3. Compile the prompt with template variables.
    compiled = prompt.compile(criticlevel="expert", movie="The Matrix")

    # 4. Emit a trace whose generation observation is linked to the prompt.
    with langfuse.start_as_current_observation(
        name="movie-critic-generation",
        as_type="generation",
        prompt=prompt,
        input=compiled,
        model="gpt-4",
    ) as generation:
        trace_id = langfuse.get_current_trace_id()
        generation.update(output="The Matrix is a groundbreaking sci-fi film.")

    # 5. Write the trace ID to the log file.
    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

    # 6. Flush all telemetry before exit.
    langfuse.flush()


if __name__ == "__main__":
    main()
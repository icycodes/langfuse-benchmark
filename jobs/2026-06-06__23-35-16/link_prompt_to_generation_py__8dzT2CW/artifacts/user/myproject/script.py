import os
import langfuse

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    prompt_name = f"movie-critic-chat-{run_id}"

    lf = langfuse.get_client()

    # 1. Create a versioned chat prompt in Langfuse, labeled `production`.
    lf.create_prompt(
        name=prompt_name,
        type="chat",
        prompt=[{"role": "user", "content": "Review {{movie}} with {{criticlevel}}."}],
        labels=["production"]
    )

    # 2. Fetch the `production` version of that prompt and compile it with template variables.
    prompt = lf.get_prompt(name=prompt_name, label="production")
    compiled_prompt = prompt.compile(movie="Inception", criticlevel="high")

    # 3. Emit one trace that contains a single generation observation linked to the fetched Langfuse prompt object.
    with lf.start_as_current_observation(
        name="movie-review-generation",
        as_type="generation",
        prompt=prompt,
        input=compiled_prompt
    ):
        # Update the output
        lf.update_current_generation(output="great movie")
        
        # Get the trace ID
        trace_id = lf.get_current_trace_id()

    # 4. Flush all telemetry before the script exits so the data is persisted in Langfuse.
    lf.flush()

    # 5. Write the resulting trace identifier to a log file in the agreed-upon format.
    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

if __name__ == "__main__":
    main()

import os
from langfuse import Langfuse

def main():
    # Read environment variables
    run_id = os.environ.get("ZEALT_RUN_ID", "unknown")
    prompt_name = f"movie-critic-chat-{run_id}"
    
    # Initialize Langfuse client
    # Credentials are automatically picked up from environment variables:
    # LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
    langfuse = Langfuse()

    # 1. Create a chat-type prompt in Langfuse and ensure it is labeled production
    chat_content = [
        {"role": "system", "content": "You are a movie critic with level {{criticlevel}}."},
        {"role": "user", "content": "What do you think about the movie {{movie}}?"}
    ]
    
    print(f"Creating prompt: {prompt_name}")
    langfuse.create_prompt(
        name=prompt_name,
        type="chat",
        prompt=chat_content,
        labels=["production"]
    )
    
    # 2. Fetch the production version of that prompt and compile it
    print(f"Fetching prompt: {prompt_name}")
    prompt = langfuse.get_prompt(prompt_name, label="production")
    
    # Compile with template variables
    compiled_prompt = prompt.compile(criticlevel="sophisticated", movie="The Matrix")

    # 3. Emit a trace whose generation observation is linked to that prompt
    # Use the prompt= argument of start_as_current_observation(as_type="generation", ...)
    print("Emitting trace and generation...")
    with langfuse.start_as_current_observation(
        name="movie-critic-generation",
        as_type="generation",
        prompt=prompt,
        input=compiled_prompt,
        output="A groundbreaking cyberpunk classic that redefined action cinema."
    ) as generation:
        # Capture the trace ID inside the active observation context
        trace_id = langfuse.get_current_trace_id()
    
    # 4. Flush all telemetry
    print("Flushing telemetry...")
    langfuse.flush()
    
    # 5. Write the resulting trace identifier to a log file
    output_path = "/home/user/myproject/output.log"
    with open(output_path, "w") as f:
        f.write(f"Trace ID: {trace_id}")
    
    print(f"Successfully created trace. Trace ID: {trace_id}")

if __name__ == "__main__":
    main()

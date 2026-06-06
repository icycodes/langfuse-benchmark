import os
import langfuse

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set")
        return

    user_id = f"user-{run_id}"
    session_id = f"session-{run_id}"
    tags = [f"demo-{run_id}", "python-sdk"]

    # Initialize client
    client = langfuse.get_client()

    # Use propagate_attributes to attach trace-level attributes
    # The propagation context wraps the work that creates the generation
    with langfuse.propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=tags
    ):
        # Create root span named chat-turn
        with client.start_as_current_observation(name="chat-turn") as root:
            # Create nested generation named assistant-reply
            with client.start_as_current_observation(
                name="assistant-reply",
                as_type="generation",
                input="Hello, how can I help you?",
                output="I am a demo of the Langfuse Python SDK."
            ):
                pass
            
            trace_id = client.get_current_trace_id()

    # Flush to ensure delivery
    client.flush()
    
    # Write trace ID to log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
    
    print(f"Successfully created trace with ID: {trace_id}")

if __name__ == "__main__":
    main()

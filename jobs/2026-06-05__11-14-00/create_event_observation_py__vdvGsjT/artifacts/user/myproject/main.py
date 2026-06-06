import os
from langfuse import get_client

def main():
    # Read environment variables
    zealt_run_id = os.getenv("ZEALT_RUN_ID", "default")
    
    # Initialize Langfuse client
    # Credentials are read from environment variables:
    # LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
    client = get_client()

    # Define names
    trace_name = f"harbor-event-trace-{zealt_run_id}"
    event_name = f"user-login-event-{zealt_run_id}"

    # Start a parent observation (span) that becomes the root of a Langfuse trace
    # In v4+, start_observation(as_type="span") or start_as_current_observation() can be used.
    # We'll use start_observation for simplicity.
    parent_span = client.start_observation(
        name=trace_name,
        as_type="span"
    )
    
    # Create a nested event observation inside that trace
    # Using the parent span's start_observation to nest it.
    event = parent_span.start_observation(
        name=event_name,
        as_type="event",
        input={"user_id": "u-42"},
        output={"status": "success"},
        metadata={
            "source": "auth-service",
            "region": "us-east-1"
        }
    )

    # End observations
    # For events, .end() is often implicit or handled, but we'll keep it for the span.
    # Actually, event observations in Langfuse are point-in-time.
    parent_span.end()

    # Flush events to Langfuse Cloud
    client.flush()

    # Capture IDs
    trace_id = parent_span.trace_id
    event_id = event.id

    # Write to log file
    log_path = "/home/user/myproject/output.log"
    # Ensure directory exists (though we already created it)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
        f.write(f"Observation ID: {event_id}\n")

if __name__ == "__main__":
    main()

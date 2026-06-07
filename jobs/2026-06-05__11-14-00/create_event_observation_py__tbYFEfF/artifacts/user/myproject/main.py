import os
from langfuse import get_client


def main():
    run_id = os.environ["ZEALT_RUN_ID"]
    trace_name = f"harbor-event-trace-{run_id}"
    event_name = f"user-login-event-{run_id}"

    langfuse = get_client()

    # Start a root span that becomes the trace
    with langfuse.start_as_current_observation(
        name=trace_name,
        as_type="span",
    ) as span:
        # Create an event observation nested under the span
        event = span.create_event(
            name=event_name,
            input={"user_id": "u-42"},
            output={"status": "success"},
            metadata={"source": "auth-service", "region": "us-east-1"},
        )

        trace_id = span.trace_id
        event_observation_id = event.id

    # Flush all buffered events to Langfuse Cloud
    langfuse.flush()

    # Write the IDs to the log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "a") as f:
        f.write(f"Trace ID: {trace_id}\n")
        f.write(f"Observation ID: {event_observation_id}\n")


if __name__ == "__main__":
    main()
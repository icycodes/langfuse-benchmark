import os
from langfuse import get_client

client = get_client()

run_id = os.environ.get("ZEALT_RUN_ID", "test")

with client.start_as_current_observation(name=f"harbor-event-trace-{run_id}", as_type="span") as span:
    event = client.create_event(
        name=f"user-login-event-{run_id}",
        input={"user_id": "u-42"},
        output={"status": "success"},
        metadata={"source": "auth-service", "region": "us-east-1"}
    )
    print("Trace ID:", client.get_current_trace_id())
    print("Observation ID:", event.id)

client.flush()

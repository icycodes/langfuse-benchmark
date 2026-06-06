import os
from langfuse import get_client

run_id = os.environ["ZEALT_RUN_ID"]

langfuse = get_client()

trace_name = f"harbor-event-trace-{run_id}"
event_name = f"user-login-event-{run_id}"

with langfuse.start_as_current_observation(name=trace_name, as_type="span") as root_span:
    trace_id = root_span.trace_id

    event = root_span.create_event(
        name=event_name,
        input={"user_id": "u-42"},
        output={"status": "success"},
        metadata={"source": "auth-service", "region": "us-east-1"},
    )
    observation_id = event.id

langfuse.flush()

log_path = "/home/user/myproject/output.log"
with open(log_path, "a") as f:
    f.write(f"Trace ID: {trace_id}\n")
    f.write(f"Observation ID: {observation_id}\n")

print(f"Trace ID: {trace_id}")
print(f"Observation ID: {observation_id}")

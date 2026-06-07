import os
from langfuse import get_client

def main():
    client = get_client()
    
    run_id = os.environ.get("ZEALT_RUN_ID", "default")
    
    trace_name = f"harbor-event-trace-{run_id}"
    event_name = f"user-login-event-{run_id}"
    
    with client.start_as_current_observation(name=trace_name, as_type="span") as span:
        event = client.create_event(
            name=event_name,
            input={"user_id": "u-42"},
            output={"status": "success"},
            metadata={"source": "auth-service", "region": "us-east-1"}
        )
        
        trace_id = client.get_current_trace_id()
        obs_id = event.id
    
    client.flush()
    
    with open("/home/user/myproject/output.log", "a") as f:
        f.write(f"Trace ID: {trace_id}\n")
        f.write(f"Observation ID: {obs_id}\n")

if __name__ == "__main__":
    main()

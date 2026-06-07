import os
from langfuse import get_client
import requests
from requests.auth import HTTPBasicAuth

client = get_client()

run_id = os.environ.get("ZEALT_RUN_ID", "test-api")

with client.start_as_current_observation(name=f"harbor-event-trace-{run_id}", as_type="span") as span:
    event = client.create_event(
        name=f"user-login-event-{run_id}",
        input={"user_id": "u-42"},
        output={"status": "success"},
        metadata={"source": "auth-service", "region": "us-east-1"}
    )
    trace_id = client.get_current_trace_id()
    obs_id = event.id

client.flush()

public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
base_url = os.environ.get("LANGFUSE_BASE_URL")

# Wait a moment for ingestion
import time
time.sleep(2)

print(f"Fetching trace: {base_url}/api/public/traces/{trace_id}")
r = requests.get(f"{base_url}/api/public/traces/{trace_id}", auth=HTTPBasicAuth(public_key, secret_key))
print(r.json())

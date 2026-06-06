import os
import requests
import json
import base64

def check_trace():
    trace_id = ""
    with open("/home/user/myproject/output.log", "r") as f:
        line = f.read().strip()
        if "Trace ID: " in line:
            trace_id = line.split("Trace ID: ")[1]

    if not trace_id:
        print("No Trace ID found in log.")
        return

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    auth_str = f"{public_key}:{secret_key}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    url = f"{base_url}/api/public/traces/{trace_id}"
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch trace: {response.status_code}")
        print(response.text)
        return

    trace_data = response.json()
    print("Trace Name:", trace_data.get("name"))
    print("Trace Input:", json.dumps(trace_data.get("input")))
    print("Trace Output:", json.dumps(trace_data.get("output")))

    observations = trace_data.get("observations", [])
    print(f"Found {len(observations)} observations.")
    for obs in observations:
        print(f"Obs Type: {obs.get('type')}, Name: {obs.get('name')}")
        print(f"Obs Input: {json.dumps(obs.get('input'))}")
        print(f"Obs Output: {json.dumps(obs.get('output'))}")

if __name__ == "__main__":
    check_trace()

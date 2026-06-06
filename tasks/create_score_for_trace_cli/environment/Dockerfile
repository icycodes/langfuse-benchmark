FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g langfuse-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests langfuse && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/task

# Initial-state bootstrap script: creates a Langfuse trace at container start
# (when LANGFUSE_* env vars are present) and writes its OTel trace ID to
# /home/user/task/trace_id.txt so the executor and verifier can target it.
RUN cat >/usr/local/bin/init_task.py <<'PYEOF'
import os
import pathlib
import sys
import time

# The plan provides LANGFUSE_BASE_URL; the SDK reads LANGFUSE_HOST.
base_url = os.environ.get("LANGFUSE_BASE_URL")
if base_url and not os.environ.get("LANGFUSE_HOST"):
    os.environ["LANGFUSE_HOST"] = base_url

from langfuse import get_client

run_id = os.environ.get("ZEALT_RUN_ID", "local")
trace_name = f"qa-review-{run_id}"

client = get_client()
trace_id = None
with client.start_as_current_observation(as_type="span", name=trace_name) as span:
    trace_id = span.trace_id
    span.update_trace(name=trace_name)

client.flush()

if not trace_id:
    sys.stderr.write("Failed to obtain a Langfuse trace ID.\n")
    sys.exit(1)

out_dir = pathlib.Path("/home/user/task")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "trace_id.txt").write_text(trace_id.strip() + "\n")
print(f"Wrote trace_id={trace_id} to /home/user/task/trace_id.txt", flush=True)
PYEOF

RUN cat >/usr/local/bin/init_task.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/user/task
if [ ! -s /home/user/task/trace_id.txt ]; then
    python3 /usr/local/bin/init_task.py
fi
SHEOF
RUN chmod +x /usr/local/bin/init_task.sh

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse CLI task environment with langfuse-cli installed globally, the Python Langfuse SDK for pre-creating a trace, jq for JSON parsing, and a bootstrap script that writes the pre-created trace ID to /home/user/task/trace_id.txt at container start."

CMD ["/bin/bash", "-c", "/usr/local/bin/init_task.sh; trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - additional apt packages: jq (parsing JSON returned by `langfuse api scores create --json`)
#   - always required pip3 packages: pytest-json-ctrf
#   - additional pip3 packages: requests (verifier hits the Langfuse REST API),
#       langfuse (used by the init script to create the pre-existing trace)
#   - Node.js v24 for installing langfuse-cli globally; `langfuse` command in PATH
#   - /home/user/task: project directory used by the executor and verifier
#   - /usr/local/bin/init_task.{py,sh}: bootstrap that creates a Langfuse trace and writes
#       its OTel trace ID to /home/user/task/trace_id.txt before the agent starts

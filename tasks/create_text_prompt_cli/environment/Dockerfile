FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/langfuse-task

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse CLI task environment: Node.js v24, Python 3, jq, and requests for verifying prompt creation via the Langfuse public API."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - additional apt packages: jq (parsing CLI JSON output for the log line)
#   - always required pip3 packages: pytest-json-ctrf
#   - additional pip3 packages: requests (used by tests/test_final_state.py to call the Langfuse REST API)
#   - Node.js v24 for installing and running langfuse-cli (npm/npx)
#   - /home/user/langfuse-task: working directory where the executor writes output.log

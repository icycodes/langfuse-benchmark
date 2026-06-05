FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        requests \
        langfuse && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/langfuse_task && chmod 0755 /home/user/langfuse_task

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse Python SDK task environment for managing versioned chat prompts with labels."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - langfuse Python SDK for prompt management
#   - requests for HTTP-based verification against the Langfuse public API
#   - /home/user/langfuse_task: working directory for the task

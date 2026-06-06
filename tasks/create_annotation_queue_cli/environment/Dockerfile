FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf httpx && \
    npm install -g langfuse-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Pre-warm the npx cache so the initial-state CLI smoke test does not need network.
RUN npx --yes langfuse-cli --help >/dev/null 2>&1 || true

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/langfuse-task && chmod 0755 /home/user/langfuse-task

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse CLI task environment for creating an annotation queue and its score config."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - extra apt packages: jq (for parsing CLI JSON output)
#   - Node.js v24 + globally installed langfuse-cli (also reachable via 'npx langfuse-cli')
#   - pip3 packages for verification: httpx
#   - /home/user/langfuse-task: project directory where the executor writes output.log

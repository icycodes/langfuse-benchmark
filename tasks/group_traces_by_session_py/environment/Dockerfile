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
RUN mkdir -p /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse Python SDK task environment: instrument a multi-turn chat script and group its traces into a single Langfuse session."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Langfuse Python SDK (pip: langfuse) for the executor to instrument /home/user/myproject/chat_session.py
#   - requests for the verifier's HTTP calls against the Langfuse public REST API
#   - /home/user/myproject: empty project directory in which the executor must create chat_session.py and output.log

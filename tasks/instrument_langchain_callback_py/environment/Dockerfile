FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        requests \
        "langfuse>=4.0.0" \
        "langchain>=0.3.0" \
        "langchain-core>=0.3.0" \
        "langchain-community>=0.3.0" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse Python SDK + LangChain environment for tracing a LangChain chain via the Langfuse CallbackHandler."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Langfuse Python SDK (>=4.0.0) including the langfuse.langchain CallbackHandler integration
#   - LangChain (langchain, langchain-core, langchain-community) for building a small LCEL chain
#     and for FakeListChatModel (no external LLM provider is required)
#   - requests for HTTP-based verification against the Langfuse public REST API
#   - /home/user/myproject: empty working directory for the task executor

FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm i -g tsx typescript && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cd /home/user/myproject && \
    cat >package.json <<'EOF'
{
  "name": "langfuse-dataset-task",
  "version": "1.0.0",
  "private": true,
  "type": "commonjs",
  "dependencies": {
    "@langfuse/client": "^4.0.0"
  }
}
EOF

RUN cd /home/user/myproject && \
    npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse TypeScript SDK task environment with @langfuse/client preinstalled in /home/user/myproject."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - requests (used by tests/test_final_state.py to call the Langfuse public REST API)
#   - Node.js v24 toolchain (node, npm, npx)
#   - Global npm packages: tsx, typescript (for running TypeScript directly)
#   - /home/user/myproject: TypeScript project pre-seeded with package.json depending on @langfuse/client
#   - /home/user/myproject/node_modules: @langfuse/client and its transitive deps preinstalled

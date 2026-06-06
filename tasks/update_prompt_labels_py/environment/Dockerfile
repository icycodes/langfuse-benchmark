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
RUN mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

# Initialization script: creates two versions of the prompt
# `movie-critic-${ZEALT_RUN_ID}` in the live Langfuse project so the
# initial state tests (and the agent's subsequent promotion) have a
# deterministic starting point.
RUN mkdir -p /opt/init && cat >/opt/init/init_langfuse.py <<'PYEOF'
import os
import sys
import time

from langfuse import Langfuse


def _wait_for_credentials(timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if (
            os.environ.get("LANGFUSE_PUBLIC_KEY")
            and os.environ.get("LANGFUSE_SECRET_KEY")
            and os.environ.get("ZEALT_RUN_ID")
        ):
            return
        time.sleep(1)
    raise RuntimeError(
        "Missing required environment variables: "
        "LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, ZEALT_RUN_ID"
    )


def _existing_versions(client: Langfuse, name: str) -> dict:
    """Return a mapping of version number -> set of labels currently present."""
    found: dict = {}
    for version in (1, 2):
        try:
            prompt = client.get_prompt(name, version=version, cache_ttl_seconds=0)
            labels = set(getattr(prompt, "labels", []) or [])
            found[version] = labels
        except Exception:
            continue
    return found


def main() -> int:
    _wait_for_credentials()

    run_id = os.environ["ZEALT_RUN_ID"]
    prompt_name = f"movie-critic-{run_id}"

    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    client = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=base_url,
    )

    existing = _existing_versions(client, prompt_name)

    v1_labels = existing.get(1, set())
    v2_labels = existing.get(2, set())

    needs_v1 = "production" not in v1_labels
    needs_v2 = "staging" not in v2_labels

    if not needs_v1 and not needs_v2:
        print(f"[init_langfuse] prompt '{prompt_name}' already initialized; skipping.")
        client.flush()
        return 0

    # Create version 1 with the production label.
    if 1 not in existing:
        client.create_prompt(
            name=prompt_name,
            type="chat",
            prompt=[
                {"role": "system", "content": "You are a {{criticlevel}} movie critic."},
                {"role": "user", "content": "Do you like {{movie}}?"},
            ],
            labels=["production"],
        )
        print(f"[init_langfuse] created v1 with label production for '{prompt_name}'.")
    else:
        print(
            f"[init_langfuse] v1 already exists for '{prompt_name}' with labels "
            f"{sorted(v1_labels)}; leaving as-is."
        )

    # Create version 2 with the staging label.
    if 2 not in existing:
        client.create_prompt(
            name=prompt_name,
            type="chat",
            prompt=[
                {
                    "role": "system",
                    "content": "You are a {{criticlevel}} movie critic with deep cinematic knowledge.",
                },
                {"role": "user", "content": "Could you share your thoughts on {{movie}}?"},
            ],
            labels=["staging"],
        )
        print(f"[init_langfuse] created v2 with label staging for '{prompt_name}'.")
    else:
        print(
            f"[init_langfuse] v2 already exists for '{prompt_name}' with labels "
            f"{sorted(v2_labels)}; leaving as-is."
        )

    client.flush()
    print(f"[init_langfuse] initialization complete for '{prompt_name}'.")
    return 0


sys.exit(main())
PYEOF

# Wrapper that runs initialization then keeps the container alive.
RUN cat >/opt/init/entrypoint.sh <<'SHEOF'
#!/usr/bin/env bash
set -u
echo "[entrypoint] running Langfuse prompt initialization..."
if ! python3 /opt/init/init_langfuse.py; then
    echo "[entrypoint] WARNING: Langfuse initialization failed; continuing so the container stays alive." >&2
fi
trap : TERM INT
sleep infinity & wait
SHEOF
RUN chmod +x /opt/init/entrypoint.sh

LABEL Author="generate-harbor-tasks"
LABEL Description="Langfuse Python SDK task environment with a pre-seeded versioned chat prompt for promotion."

CMD ["/bin/bash", "-c", "/opt/init/entrypoint.sh"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - target library: langfuse (Python SDK)
#   - verification dependency: requests
#   - /home/user/myproject: working directory for the task
#   - /opt/init/init_langfuse.py: idempotent seed script that creates v1 (production) and v2 (staging) of the chat prompt movie-critic-${ZEALT_RUN_ID}
#   - /opt/init/entrypoint.sh: container entrypoint that runs seeding then sleeps

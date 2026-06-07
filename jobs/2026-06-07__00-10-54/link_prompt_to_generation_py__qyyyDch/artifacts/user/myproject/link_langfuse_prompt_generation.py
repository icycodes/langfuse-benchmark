#!/usr/bin/env python3
"""Create a Langfuse chat prompt and link it to a generation observation.

The script expects Langfuse configuration in the standard environment variables:
  - LANGFUSE_PUBLIC_KEY
  - LANGFUSE_SECRET_KEY
  - LANGFUSE_BASE_URL

It also expects ZEALT_RUN_ID, which is incorporated into externally visible
resource names so parallel runs do not collide.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from langfuse import get_client


PROJECT_DIR = Path("/home/user/myproject")
LOG_FILE = PROJECT_DIR / "output.log"
TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def main() -> None:
    # Validate the required environment upfront. get_client() reads the Langfuse
    # credentials/base URL automatically from these standard variables.
    require_env("LANGFUSE_PUBLIC_KEY")
    require_env("LANGFUSE_SECRET_KEY")
    require_env("LANGFUSE_BASE_URL")
    run_id = require_env("ZEALT_RUN_ID")

    prompt_name = f"movie-critic-chat-{run_id}"
    observation_name = f"movie-critic-generation-{run_id}"

    langfuse = get_client()

    # Create a managed chat prompt version and assign the production label.
    # The variables {{criticlevel}} and {{movie}} are intentionally present in
    # the template so Langfuse can detect and store them for the prompt version.
    langfuse.create_prompt(
        name=prompt_name,
        type="chat",
        labels=["production"],
        prompt=[
            {
                "role": "system",
                "content": (
                    "You are a {{criticlevel}} movie critic. "
                    "Write concise, evidence-based reviews."
                ),
            },
            {
                "role": "user",
                "content": "Review the movie {{movie}} in exactly two sentences.",
            },
        ],
        config={
            "model": "gpt-4o-mini",
            "temperature": 0.2,
        },
        commit_message=f"Create production prompt for ZEALT run {run_id}",
    )

    # Fetch the production prompt at runtime and compile it with concrete values.
    production_prompt = langfuse.get_prompt(
        prompt_name,
        type="chat",
        label="production",
        cache_ttl_seconds=0,
    )
    compiled_messages = production_prompt.compile(
        criticlevel="thoughtful",
        movie="Spirited Away",
    )

    generated_review = (
        "Spirited Away is a richly imaginative coming-of-age story whose "
        "surreal imagery makes emotional growth feel tactile. Its patient "
        "pacing, layered worldbuilding, and humane character turns justify its "
        "reputation as a modern animated classic."
    )

    trace_id: str | None = None

    # Passing prompt=production_prompt links this generation observation to the
    # exact managed prompt version currently carrying the production label.
    with langfuse.start_as_current_observation(
        name=observation_name,
        as_type="generation",
        input=compiled_messages,
        output=generated_review,
        model="gpt-4o-mini",
        model_parameters={"temperature": 0.2},
        usage_details={
            "input": 34,
            "output": 42,
            "total": 76,
        },
        prompt=production_prompt,
    ):
        trace_id = langfuse.get_current_trace_id()

    if trace_id is None or not TRACE_ID_RE.fullmatch(trace_id):
        raise RuntimeError(f"Unexpected Langfuse trace id: {trace_id!r}")

    # Flush before writing completion artifact so verification never sees a trace
    # id before telemetry has been handed to the Langfuse client transport.
    langfuse.flush()

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(f"Trace ID: {trace_id}\n", encoding="utf-8")
    print(f"Trace ID: {trace_id}")


if __name__ == "__main__":
    main()

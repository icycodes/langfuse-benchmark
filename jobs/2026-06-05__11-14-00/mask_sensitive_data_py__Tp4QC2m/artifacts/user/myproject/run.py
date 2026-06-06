"""
run.py – Langfuse PII-masking demo.

Creates a trace whose root span and child generation contain PII (email,
phone, credit-card). The Langfuse client is configured with a `mask`
callable that redacts all three types before the events are exported.
The resulting trace ID is written to output.log.
"""

import os
import re

from langfuse import Langfuse, get_client

# ---------------------------------------------------------------------------
# PII masking helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# NNN-NNN-NNNN, NNN.NNN.NNNN, NNN NNN NNNN
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")

# 13-19 digit numbers, optionally grouped by spaces or dashes
_CC_RE = re.compile(
    r"\b(?:\d[ -]?){12,18}\d\b"
)


def _redact_string(value: str) -> str:
    """Replace PII tokens in a single string."""
    # Credit-card first (long digit sequences) to avoid partial matches
    value = _CC_RE.sub("[REDACTED CREDIT CARD]", value)
    value = _EMAIL_RE.sub("[REDACTED EMAIL]", value)
    value = _PHONE_RE.sub("[REDACTED PHONE]", value)
    return value


def mask(*, data, **kwargs):
    """
    Langfuse MaskFunction-compatible callable (data is passed as a keyword arg).
    Recursively sanitise strings inside any JSON-compatible structure.
    """
    if isinstance(data, str):
        return _redact_string(data)
    if isinstance(data, dict):
        return {k: mask(data=v) for k, v in data.items()}
    if isinstance(data, list):
        return [mask(data=item) for item in data]
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    run_id = os.environ["ZEALT_RUN_ID"]
    trace_name = f"mask-demo-{run_id}"

    # Initialise the Langfuse client with the masking function.
    # Credentials are taken from LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY /
    # LANGFUSE_BASE_URL environment variables automatically.
    Langfuse(mask=mask)

    # Retrieve the configured singleton client.
    langfuse = get_client()

    # PII-laden payloads (will be masked before export)
    root_input = {
        "message": (
            "Hi, I'm john.doe@example.com and my phone is 555-867-5309. "
            "Please charge my card 4111 1111 1111 1111."
        )
    }
    root_output = {
        "reply": (
            "Thanks john.doe@example.com! We'll call you at 555-867-5309 "
            "and process card 4111 1111 1111 1111 shortly."
        )
    }

    gen_input = [
        {"role": "system", "content": "You are a helpful support agent."},
        {
            "role": "user",
            "content": (
                "Customer email: jane.smith@corp.io, "
                "phone: 800.555.1234, "
                "card: 5500-0000-0000-0004."
            ),
        },
    ]
    gen_output = {
        "role": "assistant",
        "content": (
            "Understood. I've noted jane.smith@corp.io, "
            "800.555.1234, and card 5500-0000-0000-0004."
        ),
    }

    # Root span – becomes the top-level (root) observation / trace.
    with langfuse.start_as_current_observation(
        name=trace_name,
        as_type="span",
        input=root_input,
        output=root_output,
    ) as root_span:
        trace_id = root_span.trace_id

        # Child generation observation nested under the root span.
        with root_span.start_as_current_observation(
            name="llm-call",
            as_type="generation",
            input=gen_input,
            output=gen_output,
            model="gpt-4o",
        ):
            # Simulate work; the generation is ended automatically on exit.
            pass

    # Flush all buffered events to Langfuse before the process exits.
    langfuse.flush()

    # Write the trace ID to the log file.
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
    with open(log_path, "w") as fh:
        fh.write(f"Trace ID: {trace_id}\n")

    print(f"Trace ID: {trace_id}")
    print(f"Log written to: {log_path}")


if __name__ == "__main__":
    main()

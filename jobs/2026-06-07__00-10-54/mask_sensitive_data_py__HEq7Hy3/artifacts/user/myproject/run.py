#!/usr/bin/env python3
"""Create a Langfuse trace with client-side PII masking enabled."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from langfuse import Langfuse, get_client

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_LOG = PROJECT_DIR / "output.log"

REDACTED_EMAIL = "[REDACTED EMAIL]"
REDACTED_PHONE = "[REDACTED PHONE]"
REDACTED_CREDIT_CARD = "[REDACTED CREDIT CARD]"

# Original PII values intentionally used in the trace payloads before masking.
CUSTOMER_EMAIL = "ada.lovelace@example.com"
CUSTOMER_PHONE = "415-555-2671"
CUSTOMER_CARD = "4111-1111-1111-1111"
AGENT_EMAIL = "support.agent@example.org"
AGENT_PHONE = "212.555.0198"
AGENT_CARD = "5500 0000 0000 0004"

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)\d{3}[-. ]\d{3}[-. ]\d{4}(?!\d)")
# Match 13-19 digits where spaces or dashes may separate digit groups.
CREDIT_CARD_RE = re.compile(r"(?<!\d)(?=(?:\D*\d){13,19}\D*(?!\d))(?:\d[ -]?){12,18}\d(?!\d)")


def redact_string(value: str) -> str:
    """Replace supported PII patterns in a string with literal redaction tokens."""
    value = CREDIT_CARD_RE.sub(REDACTED_CREDIT_CARD, value)
    value = PHONE_RE.sub(REDACTED_PHONE, value)
    value = EMAIL_RE.sub(REDACTED_EMAIL, value)
    return value


def mask(data: Any = None, **_: Any) -> Any:
    """Recursively redact PII from strings while preserving container shape.

    Langfuse calls custom masking functions with a ``data=...`` keyword
    argument. Accepting ``**_`` keeps the callable forward-compatible with
    any additional context keywords the SDK may add.
    """
    if isinstance(data, str):
        return redact_string(data)

    if isinstance(data, dict):
        return {key: mask(item) for key, item in data.items()}

    if isinstance(data, list):
        return [mask(item) for item in data]

    if isinstance(data, tuple):
        return tuple(mask(item) for item in data)

    return data


def build_root_input(run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "ticket": "billing-1042",
        "message": (
            f"Customer {CUSTOMER_EMAIL} called from {CUSTOMER_PHONE} "
            f"and reported card {CUSTOMER_CARD} was charged twice."
        ),
        "nested": {
            "contact": CUSTOMER_EMAIL,
            "phone": CUSTOMER_PHONE,
            "payment_card": CUSTOMER_CARD,
        },
    }


def build_root_output() -> dict[str, Any]:
    return {
        "resolution": (
            f"Refund approved for {CUSTOMER_EMAIL}; verification phone "
            f"{CUSTOMER_PHONE}; card on file {CUSTOMER_CARD}."
        ),
        "next_steps": [
            f"Send confirmation to {CUSTOMER_EMAIL}",
            f"Do not expose {CUSTOMER_CARD} in downstream tools",
            f"Callback number remains {CUSTOMER_PHONE}",
        ],
    }


def main() -> None:
    run_id = os.environ["ZEALT_RUN_ID"]
    trace_name = f"mask-demo-{run_id}"

    # Environment variables provide LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and
    # LANGFUSE_BASE_URL. The mask callable is applied before export.
    Langfuse(mask=mask)
    langfuse = get_client()

    root_input = build_root_input(run_id)
    root_output = build_root_output()

    with langfuse.start_as_current_observation(
        name=trace_name,
        as_type="span",
        input=root_input,
        output=root_output,
        metadata={
            "source": "mask-demo",
            "raw_contact_copy": f"{CUSTOMER_EMAIL} / {CUSTOMER_PHONE} / {CUSTOMER_CARD}",
        },
    ) as root_span:
        # Make the top-level trace IO explicit in addition to the root span IO.
        root_span.set_trace_io(input=root_input, output=root_output)

        child_input = {
            "prompt": (
                f"Draft a reply for customer {AGENT_EMAIL}; alternate phone "
                f"{AGENT_PHONE}."
            ),
            "context": {"card_reference": AGENT_CARD},
        }
        child_output = {
            "completion": (
                f"Reply drafted and sent to {AGENT_EMAIL}. Confirmed account "
                f"by phone {AGENT_PHONE} and card {AGENT_CARD}."
            )
        }

        with root_span.start_as_current_observation(
            name=f"mask-demo-generation-{run_id}",
            as_type="generation",
            input=child_input,
            output=child_output,
            model="pii-redaction-demo-model",
            metadata={"raw_child_contact_copy": f"{AGENT_EMAIL} {AGENT_PHONE} {AGENT_CARD}"},
        ):
            pass

        trace_id = root_span.trace_id

    langfuse.flush()

    OUTPUT_LOG.write_text(f"Trace ID: {trace_id}\n", encoding="utf-8")
    print(f"Trace ID: {trace_id}")


if __name__ == "__main__":
    main()

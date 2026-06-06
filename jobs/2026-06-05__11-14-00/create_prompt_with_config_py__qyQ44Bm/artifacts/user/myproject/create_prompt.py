"""
Create a versioned invoice-extractor prompt with config in Langfuse,
then fetch it back and write a structured summary to output.log.
"""

import os
from langfuse import Langfuse
from langfuse.model import ChatPromptClient

# ── 1. Read run id ─────────────────────────────────────────────────────────────
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"invoice-extractor-{run_id}"

# ── 2. Build Langfuse client (picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
#        LANGFUSE_BASE_URL from the environment automatically) ──────────────────
langfuse = Langfuse()

# ── 3. Define the chat messages (user message contains a Mustache variable) ────
chat_messages = [
    {
        "role": "system",
        "content": (
            "You are an expert invoice extraction assistant. "
            "Extract all relevant fields from the invoice and return them as "
            "structured JSON that conforms to the provided schema."
        ),
    },
    {
        "role": "user",
        "content": (
            "Please extract the invoice details from the following text and "
            "return a JSON object matching the required schema.\n\n"
            "Invoice text:\n{{invoice_text}}"
        ),
    },
]

# ── 4. Define the config (model params + structured-output schema) ─────────────
prompt_config = {
    "model": "gpt-4o",
    "temperature": 0.0,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "invoice_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "invoice_number": {
                        "type": "string",
                        "description": "Unique invoice identifier",
                    },
                    "invoice_date": {
                        "type": "string",
                        "description": "Date the invoice was issued (ISO 8601)",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Payment due date (ISO 8601)",
                    },
                    "vendor": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "tax_id": {"type": "string"},
                        },
                        "required": ["name", "address", "tax_id"],
                        "additionalProperties": False,
                    },
                    "customer": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                        },
                        "required": ["name", "address"],
                        "additionalProperties": False,
                    },
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "total": {"type": "number"},
                            },
                            "required": ["description", "quantity", "unit_price", "total"],
                            "additionalProperties": False,
                        },
                    },
                    "subtotal": {"type": "number"},
                    "tax_amount": {"type": "number"},
                    "total_amount": {"type": "number"},
                    "currency": {"type": "string"},
                },
                "required": [
                    "invoice_number",
                    "invoice_date",
                    "due_date",
                    "vendor",
                    "customer",
                    "line_items",
                    "subtotal",
                    "tax_amount",
                    "total_amount",
                    "currency",
                ],
                "additionalProperties": False,
            },
        },
    },
}

# ── 5. Create the versioned prompt ─────────────────────────────────────────────
created = langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=chat_messages,
    config=prompt_config,
    labels=["production", "staging"],
)

print(f"Created prompt '{created.name}' version {created.version}")

# ── 6. Fetch back without cache ────────────────────────────────────────────────
fetched = langfuse.get_prompt(
    prompt_name,
    type="chat",
    cache_ttl_seconds=0,
)

# ── 7. Determine prompt type string ───────────────────────────────────────────
prompt_type_str = "chat" if isinstance(fetched, ChatPromptClient) else "text"

# ── 8. Extract config keys and labels (filter to only production/staging) ──────
config_keys = ", ".join(fetched.config.keys())

# Labels from API may include auto-assigned 'latest'; show only production & staging
user_labels = [lbl for lbl in fetched.labels if lbl in ("production", "staging")]
labels_str = ", ".join(sorted(user_labels))

# ── 9. Write the structured log ────────────────────────────────────────────────
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
log_lines = [
    f"Prompt name: {fetched.name}",
    f"Prompt version: {fetched.version}",
    f"Prompt type: {prompt_type_str}",
    f"Config keys: {config_keys}",
    f"Labels: {labels_str}",
]

with open(log_path, "w") as fh:
    fh.write("\n".join(log_lines) + "\n")

print(f"Log written to {log_path}")
for line in log_lines:
    print(" ", line)

# ── 10. Flush buffered SDK events before exit ──────────────────────────────────
langfuse.flush()
print("Done.")

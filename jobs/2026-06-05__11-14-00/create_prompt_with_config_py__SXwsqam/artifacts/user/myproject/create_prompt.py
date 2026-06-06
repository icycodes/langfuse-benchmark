#!/usr/bin/env python3
"""Create a versioned invoice-extractor prompt in Langfuse with config and labels."""

import os
from langfuse import Langfuse

# --- Read deterministic run ID ---
run_id = os.environ["ZEALT_RUN_ID"]
prompt_name = f"invoice-extractor-{run_id}"

# --- Initialize Langfuse client (picks up env vars automatically) ---
langfuse = Langfuse()

# --- Define the chat prompt messages ---
# At least one message uses a Mustache-style {{variable}} placeholder
messages = [
    {
        "role": "system",
        "content": "You are an expert invoice data extractor. Extract all relevant fields from the provided invoice text and return them as structured JSON.",
    },
    {
        "role": "user",
        "content": "Please extract the invoice data from the following text:\n\n{{invoice_text}}",
    },
]

# --- Define the config object ---
config = {
    "model": "gpt-4o",
    "temperature": 0.1,
    "response_format": {
        "json_schema": {
            "name": "invoice_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "invoice_date": {"type": "string"},
                    "vendor_name": {"type": "string"},
                    "total_amount": {"type": "number"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "line_total": {"type": "number"},
                            },
                            "required": ["description", "quantity", "unit_price", "line_total"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["invoice_number", "invoice_date", "vendor_name", "total_amount", "line_items"],
                "additionalProperties": False,
            },
        }
    },
}

# --- Create the prompt with labels ---
langfuse.create_prompt(
    name=prompt_name,
    type="chat",
    prompt=messages,
    config=config,
    labels=["production", "staging"],
)

# --- Flush to ensure the create request is sent ---
langfuse.flush()

# --- Fetch the prompt back (cache disabled so we hit the API) ---
prompt = langfuse.get_prompt(prompt_name, type="chat", cache_ttl_seconds=0)

# --- Determine prompt type ---
# ChatPromptClient is returned for chat prompts; we know it's "chat"
prompt_type = "chat"

# --- Extract config keys ---
config_keys = ", ".join(prompt.config.keys())

# --- Format labels (exclude auto-assigned 'latest' for the log line) ---
# The acceptance criteria lists only production and staging for the Labels line
labels_for_log = ", ".join(
    label for label in sorted(prompt.labels) if label in ("production", "staging")
)

# --- Write structured summary to log file ---
log_path = "/home/user/myproject/output.log"
with open(log_path, "w") as f:
    f.write(f"Prompt name: {prompt.name}\n")
    f.write(f"Prompt version: {prompt.version}\n")
    f.write(f"Prompt type: {prompt_type}\n")
    f.write(f"Config keys: {config_keys}\n")
    f.write(f"Labels: {labels_for_log}\n")

print(f"Log written to {log_path}")
# Create a Versioned Prompt with Config using the Langfuse Python SDK

## Background
Your team is onboarding a new `invoice-extractor` LLM workflow into [Langfuse Prompt Management](https://langfuse.com/docs/prompt-management/get-started). The Langfuse `config` feature lets you store model parameters (model name, temperature, structured-output schema) **versioned together with the prompt**, so engineers can switch models or tweak schemas without touching application code. Your task is to create the first version of this prompt programmatically via the Langfuse Python SDK and verify it round-trips correctly.

## Requirements
- Write a Python script that uses the Langfuse Python SDK (`langfuse` package) to create a NEW chat prompt with an attached `config` object and labels.
- The prompt must be a chat prompt (`type="chat"`) consisting of a system message and a user message. At least one of the messages must include a Mustache-style variable using the `{{variable}}` syntax (e.g. `{{invoice_text}}`).
- The `config` object must include the keys `model` (string), `temperature` (number), and `response_format` (object containing a `json_schema` definition for invoice extraction).
- At creation time, attach both labels `production` and `staging` to the new prompt version.
- After creating the prompt, fetch it back using `langfuse.get_prompt(...)` with caching disabled (so the fetch hits the API) and write a structured summary to a log file.
- The script must call `langfuse.flush()` before exiting so the create call is not silently dropped.

## Implementation Hints
- Read the deterministic run id from the `ZEALT_RUN_ID` environment variable.
- Langfuse credentials are provided via the `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables. The Python SDK picks them up automatically when you call `get_client()`.
- Use `langfuse.create_prompt(name=..., type="chat", prompt=[...], config=..., labels=[...])` to create the versioned prompt object.
- Use `langfuse.get_prompt(name, cache_ttl_seconds=0)` to read it back without hitting the in-process cache.
- Use `prompt.config`, `prompt.version`, `prompt.labels`, and `prompt.prompt_type` (or equivalent attributes) on the returned object when writing the log file.
- Common pitfall: scripts that exit immediately can lose buffered create requests — always flush before exiting.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the script is executed and the artifacts exist.
- Log file: `/home/user/myproject/output.log`
- The script must read the `ZEALT_RUN_ID` environment variable; the created prompt name MUST be exactly `invoice-extractor-${ZEALT_RUN_ID}`.
- The created prompt's `type` MUST be `chat`.
- The created prompt's `config` MUST contain the keys `model`, `temperature`, and `response_format` (with a nested `json_schema`).
- The created prompt MUST have both labels `production` and `staging` attached (in addition to the auto-assigned `latest` label).
- At least one of the chat messages MUST contain a `{{...}}` Mustache variable placeholder.
- The log file MUST contain the following lines (one per line, in any order):
  - `Prompt name: invoice-extractor-<run-id>`
  - `Prompt version: <integer>`
  - `Prompt type: chat`
  - `Config keys: model, temperature, response_format`
  - `Labels: production, staging`


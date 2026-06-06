# Create a Text Prompt via the Langfuse Python SDK

## Background
You are working with [Langfuse](https://langfuse.com/), an open-source AI engineering platform that provides versioned prompt management. The Langfuse Python SDK is preinstalled and authenticated via environment variables. Your job is to write a one-off Python script that creates a new **text** prompt in your Langfuse project so the rest of the team can fetch it at runtime by label.

## Requirements
- Implement a Python script that uses the Langfuse Python SDK (`langfuse` package) to create a single **text**-type prompt.
- The prompt must contain at least one Langfuse variable placeholder using the `{{variable}}` syntax (so it can later be compiled at runtime).
- The new prompt version must be created with a non-empty `config` dictionary (e.g., model parameters) and at least one `tag`.
- The new prompt version must be created with `production` as one of its labels so it becomes the default version served by the SDK.
- After the SDK call succeeds, the script must log the resulting prompt's name and version to a log file so the operation can be audited.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable and append it to the prompt name to keep concurrent runs isolated.
- The Langfuse Python SDK is initialised via `from langfuse import get_client; langfuse = get_client()`, which reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from the environment.
- `langfuse.create_prompt(...)` is the primary entry point for creating both text and chat prompts. Pass `type="text"` for a text prompt.
- For short-lived scripts you should call `langfuse.flush()` before exit so all pending background work is sent to the API.
- See: https://langfuse.com/docs/prompt-management/get-started and https://langfuse.com/docs/prompt-management/features/prompt-version-control.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/myproject/output.log
- The script must use the Langfuse Python SDK (not raw HTTP calls or the CLI) to create the prompt.
- The prompt name must be `movie-critic-text-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The created prompt must be of type `text`, must contain at least one `{{variable}}` placeholder, must have a non-empty `config` object, and must have at least one tag.
- The labels of the created prompt version must include `production`.
- The log file must contain a line in the format: `Prompt Name: <name>`
- The log file must contain a line in the format: `Prompt Version: <version>` (where `<version>` is the integer version number returned by Langfuse).


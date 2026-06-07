# Create a Versioned Text Prompt with the Langfuse CLI

## Background
Langfuse is an open-source AI engineering platform. It provides first-class versioned prompt management exposed through its public REST API, Python/JS SDKs, **and** an official Node-based CLI (`langfuse-cli`) that dynamically wraps the OpenAPI spec. Your team wants to script the creation of new prompt versions from CI scripts, so they need a reproducible CLI-based workflow that can author a brand new prompt, attach deployment labels, tags, a config blob, and a commit message — all in a single invocation — and then record the result for downstream tooling.

You must complete this prompt-creation flow using the **`langfuse-cli`** (NOT the Python/JS SDKs or raw `curl`). The Langfuse credentials (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) are already exported as environment variables.

## Requirements
- Install the official `langfuse-cli` from npm so the `langfuse` command is available on the PATH.
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- Build the prompt name as `welcome-email-${run-id}` (the literal string `welcome-email-` followed by the run-id) and use this exact name when calling the CLI.
- Use the CLI to create a single new **text** prompt version with:
  - the prompt body (the text template) set to: `Hello {{name}}, welcome to {{service}}! Your plan is {{plan}}.`
  - a `config` JSON object with at least `model` = `gpt-4o-mini` and `temperature` = `0.5`
  - the deployment labels `production` and `staging`
  - the tag `onboarding`
  - the commit message `Initial onboarding template`
- Save a single log line to `/home/user/langfuse-task/output.log` in the exact format:
  `Prompt created: name=<prompt_name> version=<version>`
  where `<prompt_name>` is the full prompt name (including the run-id suffix) and `<version>` is the numeric version returned by the API (e.g. `1`).

## Implementation Hints
- The CLI authenticates from the same env vars as the SDKs; no separate login step is required.
- The CLI is dynamically generated from the OpenAPI spec. Use `langfuse api prompts create --help` to discover the available flags for the create endpoint, including how to pass the prompt body, labels, tags, config, and commit message.
- A text prompt is the default prompt type; you do not need a chat-style message array for this task.
- The CLI prints the created prompt object as JSON; parsing it with `jq` (or another JSON tool) is a convenient way to pick out the `name` and `version` for the log line.
- Use `langfuse api __schema` or `langfuse api prompts --help` to explore available subcommands if the CLI surface is unfamiliar.

## Acceptance Criteria
- Project path: /home/user/langfuse-task
- Ensure the prompt-creation action is actually executed against Langfuse (do not mock it) and the log artifact exists.
- Log file: /home/user/langfuse-task/output.log
- The prompt name must be `welcome-email-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The created prompt must be of type `text`.
- The created prompt must have deployment labels that include both `production` and `staging`.
- The created prompt must have a tag that includes `onboarding`.
- The created prompt's `config` field must contain the keys `model` (set to `gpt-4o-mini`) and `temperature` (set to `0.5`).
- The created prompt's `commitMessage` must equal `Initial onboarding template`.
- The created prompt's `prompt` text must equal `Hello {{name}}, welcome to {{service}}! Your plan is {{plan}}.` exactly.
- The log file must contain a line in the format: `Prompt created: name=<prompt_name> version=<version>` matching the actually created prompt name and version.


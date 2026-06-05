# Link a Langfuse Prompt to a Generation Observation (Python SDK)

## Background
[Langfuse](https://langfuse.com/) is an open-source LLM engineering platform that combines observability, prompt management, and evaluation. Linking a managed prompt to a generation observation enables Langfuse to aggregate metrics (latency, tokens, cost, scores) per prompt version. This is the foundation of the Prompt Metrics view used to compare prompt versions in production.

In this task, you will use the Langfuse Python SDK to (1) create a versioned chat prompt, (2) fetch the production version of that prompt at runtime, and (3) emit a trace whose generation observation is **linked** to that prompt so Langfuse can attribute the generation to the correct prompt version.

## Requirements
- Write a single, self-contained Python script that, when executed, performs the entire workflow end-to-end against the real Langfuse backend.
- Create a chat-type prompt in Langfuse and ensure it is labeled `production`.
- Fetch the `production` version of that prompt and compile it with template variables.
- Emit one trace that contains a single generation observation linked to the fetched Langfuse prompt object.
- Flush all telemetry before the script exits so the data is persisted in Langfuse.
- Write the resulting trace identifier to a log file in the agreed-upon format.

## Implementation Hints
- Read the Langfuse credentials and base URL from the standard `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables. The Python SDK's `get_client()` helper picks these up automatically.
- Read the parallel-run identifier from the `ZEALT_RUN_ID` environment variable and incorporate it into all externally visible resource names so concurrent runs do not collide.
- The Langfuse Python SDK exposes prompt CRUD via `langfuse.create_prompt(...)` and `langfuse.get_prompt(...)`. Use `type="chat"` and supply `labels=["production"]` when creating the prompt.
- To link a prompt to a generation observation, pass the fetched prompt object via the `prompt=` argument of `start_as_current_observation(as_type="generation", ...)`. See the official guide: <https://langfuse.com/docs/prompt-management/features/link-to-traces>.
- Use `langfuse.get_current_trace_id()` (inside the active observation context) to capture the trace ID that you will log to disk.
- Call `langfuse.flush()` before the process exits so the trace and observation reach the Langfuse backend.
- You may install any extra packages with `pip` if needed, but `langfuse` is already installed in the environment.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the script is executed and the artifacts exist (the verifier will not re-run the side-effecting script).
- Log file: `/home/user/myproject/output.log`
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- A chat-type prompt named `movie-critic-chat-${run-id}` must exist in the configured Langfuse project, must have the label `production` on at least one version, and must include the template variables `criticlevel` and `movie`.
- The trace produced by the script must contain at least one observation whose `type` is `GENERATION` and whose linked prompt has `promptName == movie-critic-chat-${run-id}`.
- The `promptVersion` recorded on that generation observation must match the version of the prompt that currently carries the `production` label.
- The log file `/home/user/myproject/output.log` must contain a single line in the exact format `Trace ID: <trace_id>`, where `<trace_id>` is the 32-character hexadecimal OpenTelemetry trace ID returned by `langfuse.get_current_trace_id()` inside the active generation.


# Attach User, Session, and Tags to a Langfuse Trace (Python SDK)

## Background
[Langfuse](https://langfuse.com/) is an open-source LLM observability platform. Beyond raw spans, Langfuse exposes first-class concepts for **user tracking**, **sessions**, and **tags** that let you aggregate metrics, replay multi-turn conversations, and slice traces in the UI. The Langfuse Python SDK propagates these attributes through any nested observation via the `propagate_attributes` context manager.

You will write a small Python program that produces **one** trace and one nested generation observation, and that propagates a `user_id`, a `session_id`, and a list of `tags` onto the trace. The trace must be flushed to Langfuse Cloud before the program exits.

## Requirements
- Create a Python project that uses the official `langfuse` Python SDK (v3+).
- The program must produce exactly **one** Langfuse trace whose root span is named `chat-turn`. The root span must contain one nested observation of type `generation` named `assistant-reply`.
- Use `propagate_attributes` to attach the following trace-level attributes to that trace:
  - `user_id` = `"user-${run-id}"`
  - `session_id` = `"session-${run-id}"`
  - `tags` = `["demo-${run-id}", "python-sdk"]`
  where `${run-id}` is read from the `ZEALT_RUN_ID` environment variable.
- The Langfuse client must be configured from the `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables (already set in the environment).
- After the script finishes its work it must call `langfuse.flush()` so the trace is reliably delivered to Langfuse Cloud before process exit.
- The script must print the resulting Langfuse trace ID to a log file in the form `Trace ID: <trace_id>`.

## Implementation Hints
- The `langfuse` package exposes `get_client()`, `start_as_current_observation(as_type=...)`, and `propagate_attributes(user_id=..., session_id=..., tags=[...])`. Combine them so the propagation context wraps the work that creates the generation.
- The propagated attributes must be active **before** the generation is created so they appear on the trace in Langfuse.
- Use `langfuse.get_current_trace_id()` to obtain the active trace ID and write it to the log file.
- Short-lived scripts must call `langfuse.flush()` (or `shutdown()`) at the end, otherwise the trace will not appear in Langfuse Cloud.
- The agent does not need to make a real LLM call. The generation observation can be created with hard-coded `input`/`output` values via the SDK; it just needs the right `as_type="generation"` and name `assistant-reply`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed once and the resulting trace exists in Langfuse Cloud.
- Log file: /home/user/myproject/output.log
- In the log file, print the Langfuse trace ID in the format `Trace ID: <trace_id>` on its own line.
- The trace fetched from Langfuse Cloud must satisfy:
  - `name` of the root observation is `chat-turn`.
  - `userId` equals `user-${run-id}`.
  - `sessionId` equals `session-${run-id}`.
  - `tags` contains both `demo-${run-id}` and `python-sdk`.
  - The trace contains at least one observation of `type == "GENERATION"` named `assistant-reply`.
- `${run-id}` must be read at runtime from the `ZEALT_RUN_ID` environment variable.


# Group Multi-Turn Chat Traces into a Langfuse Session

## Background
You are building a small chatbot prototype and want to use [Langfuse](https://langfuse.com/) to observe whole conversations, not just one-off LLM calls. Langfuse uses OpenTelemetry under the hood: every interaction is a `trace` made up of nested `observations` (`span`, `generation`, ...). Traces that share the same `session_id` are grouped together in the Langfuse UI as a single replayable conversation, and a trace-level `user_id` lets you slice traffic per end-user.

For this task, you must instrument a script with the Langfuse **Python SDK v3+** so that one run of the script produces a complete Langfuse session containing **multiple traces**, all tagged with the same `user_id` and a shared tag.

The Langfuse credentials are pre-configured via environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`) and a pre-existing project at `/home/user/myproject` already has `langfuse` installed.

## Requirements
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable and derive these identifiers (use lowercase, no spaces):
  - Session ID: `chat-session-${run-id}`
  - User ID: `chat-user-${run-id}`
  - Tag: `harbor-demo-${run-id}`
- Implement `/home/user/myproject/chat_session.py` so that running it once with `python3 /home/user/myproject/chat_session.py` produces **exactly three** traces in the derived session, in order, with these `trace.name` values:
  - `greeting-turn`
  - `followup-turn`
  - `farewell-turn`
- Every trace must:
  - Be linked to the derived Session ID (so that all three appear under the same Langfuse session).
  - Have `user_id` set to the derived User ID.
  - Have `tags` that include the derived tag.
  - Contain at least one nested observation of type `generation` (the simulated LLM response). The generation must have a `model` attribute (you may use any string, e.g. `gpt-4o-mini`) and a non-empty `output`.
- The script must call `langfuse.flush()` before exit so traces are delivered before the process terminates.
- After all three traces are emitted and flushed, the script must append a single line to `/home/user/myproject/output.log` (creating the file if it does not exist) in the exact format:
  - `Session ID: <session_id>`

No real LLM call is required; you may use any deterministic string as the generation's output.

## Implementation Hints
- Use `from langfuse import get_client` and the `start_as_current_observation(as_type="span", name=...)` / `start_as_current_observation(as_type="generation", name=..., model=...)` context managers from the v3+ Python SDK. ([Get Started with Tracing](https://langfuse.com/docs/observability/get-started))
- To attach `session_id`, `user_id`, and `tags` to the enclosing trace, call the trace-update helper on the root span (e.g. `span.update_trace(session_id=..., user_id=..., tags=[...])`) **inside** the root span's context. ([Sessions](https://langfuse.com/docs/observability/features/sessions), [User Tracking](https://langfuse.com/docs/observability/features/users), [Tags](https://langfuse.com/docs/observability/features/tags))
- Each chat turn should be its own trace (its own outer span). Three turns => three separate top-level spans => three traces in the same session.
- Don't forget `langfuse.flush()` at the end — short-lived scripts otherwise drop spans on exit. ([Background processing](https://langfuse.com/docs/observability/data-model#background-processing))
- Verification will query the Langfuse public REST API for the session and its traces, so the IDs and tags above must match exactly.

## Acceptance Criteria
- Project path: /home/user/myproject
- Script path: /home/user/myproject/chat_session.py
- Log file: /home/user/myproject/output.log
- Ensure the script is actually executed against Langfuse Cloud and the resulting traces exist in the project; the verifier will call the Langfuse REST API to check them.
- The `run-id` MUST be read from the `ZEALT_RUN_ID` environment variable and used as the suffix for the session ID, user ID, and tag as specified in Requirements.
- The log file must contain a line in the format: `Session ID: chat-session-${run-id}`.
- Running `python3 /home/user/myproject/chat_session.py` must exit with status code 0.
- After the script runs:
  - `GET /api/public/sessions/{sessionId}` for the derived session ID must return HTTP 200 and contain three traces.
  - `GET /api/public/traces?sessionId={sessionId}` must list traces named `greeting-turn`, `followup-turn`, and `farewell-turn`, each with `userId` equal to the derived user ID and `tags` including the derived tag.
  - Each of those traces must contain at least one observation whose `type` is `GENERATION`.


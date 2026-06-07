# Emit a Langfuse Event Observation with the Python SDK

## Background
Langfuse traces are built from `observations`. In addition to generic spans and LLM generations, Langfuse supports a lightweight `event` observation type that represents a single point-in-time action inside a trace (e.g. "user logged in", "cache hit", "tool invoked"). Event observations are first-class observations in Langfuse: they appear in the trace timeline, the public Observations API, and metrics.

In this task, you will write a small Python program that uses the Langfuse Python SDK (v4+, `from langfuse import get_client`) to emit a structured `event`-type observation inside a parent trace, and you will record the resulting Langfuse IDs to a log file so the result can be verified through the Langfuse Cloud Public API.

## Requirements
- Create a Python script at `/home/user/myproject/main.py` that uses the official Langfuse Python SDK to:
  - Start a parent observation (span) that becomes the root of a Langfuse trace, named `harbor-event-trace-${ZEALT_RUN_ID}` (where `${ZEALT_RUN_ID}` is the value of the `ZEALT_RUN_ID` environment variable).
  - Inside that trace, create exactly one nested observation whose Langfuse observation type is `event`, named `user-login-event-${ZEALT_RUN_ID}`.
  - On that event observation, set:
    - `input` to the JSON object `{"user_id": "u-42"}`
    - `output` to the JSON object `{"status": "success"}`
    - `metadata` to a JSON object that contains at least the keys `source` (value `"auth-service"`) and `region` (value `"us-east-1"`).
  - Make sure all buffered events are flushed to Langfuse Cloud before the script exits.
  - Append two lines to `/home/user/myproject/output.log` so the verifier can locate the just-created Langfuse objects:
    - `Trace ID: <trace_id>`
    - `Observation ID: <event_observation_id>`
    where `<trace_id>` is the Langfuse trace ID of the parent trace and `<event_observation_id>` is the Langfuse observation ID of the event observation that was just created.
- The script must be runnable as `python3 /home/user/myproject/main.py`.

## Implementation Hints
- Use the Langfuse Python SDK's `get_client()` (v4+) and its observation APIs. The SDK supports specifying the observation type with an `as_type` parameter; the value for events is documented in Langfuse's observation-types docs.
- The Langfuse Python SDK reads credentials from `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`. These are already exported in the environment.
- Read the `ZEALT_RUN_ID` environment variable and use it as a suffix on the trace and event names so that concurrent runs do not collide.
- The SDK is asynchronous; remember to flush or shut down the client before the process exits, otherwise events may be lost.
- You can capture the Langfuse trace and observation IDs from the SDK (e.g. via the active span helpers or directly from the returned observation object) and write them to the log file before the script exits.

## Acceptance Criteria
- Project path: /home/user/myproject
- Script path: /home/user/myproject/main.py
- Log file: /home/user/myproject/output.log
- Ensure the script is executed once so that the trace and event observation are actually created in Langfuse Cloud, and the log file is written.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable. The created Langfuse trace name must be `harbor-event-trace-${run-id}` and the created event observation name must be `user-login-event-${run-id}`.
- The log file must contain exactly one line of the form `Trace ID: <trace_id>` and exactly one line of the form `Observation ID: <event_observation_id>`, where the IDs are the real Langfuse IDs returned by the SDK.
- When the recorded observation is fetched from the Langfuse Public API, it must have observation type `EVENT`, its `name` must equal `user-login-event-${run-id}`, its `traceId` must equal the recorded trace ID, its `input` must be the JSON object `{"user_id": "u-42"}`, its `output` must be the JSON object `{"status": "success"}`, and its `metadata` must include `source = "auth-service"` and `region = "us-east-1"`.
- When the recorded trace is fetched from the Langfuse Public API, its `name` must equal `harbor-event-trace-${run-id}`.


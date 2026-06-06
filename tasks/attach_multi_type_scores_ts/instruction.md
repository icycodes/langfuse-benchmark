# Attach Numeric, Categorical, and Boolean Scores to a Langfuse Trace via the TypeScript SDK

## Background
[Langfuse](https://langfuse.com/) is an open-source LLM engineering platform that captures OpenTelemetry-based traces for LLM applications and exposes a public REST API plus modular TypeScript SDKs (`@langfuse/tracing`, `@langfuse/otel`, `@langfuse/client`). After a trace is ingested, you can attach **scores** to it with the `LangfuseClient.score.create(...)` method. Scores can be numeric, categorical, boolean, or text and are a primary way of evaluating LLM application quality.

In this task, you will build a small Node.js / TypeScript script that creates a Langfuse trace (with one nested generation observation) and then attaches three scores of different data types to that trace using the Langfuse JS/TS SDK.

## Requirements
- Initialise the Langfuse OpenTelemetry exporter (`LangfuseSpanProcessor` from `@langfuse/otel`) and the Node OTel SDK before any traced code runs.
- Create a single trace whose name is `multi-score-demo-${run-id}` (replace `${run-id}` with the value of the `ZEALT_RUN_ID` environment variable).
- Inside that trace, create one nested observation of type `generation` whose name is `llm-call`.
- Use `LangfuseClient` from `@langfuse/client` to attach exactly **three** scores to the trace (not the observation) with the following names, data types, and values:
  - `correctness` — NUMERIC — value `0.92`
  - `sentiment` — CATEGORICAL — value `"positive"`
  - `helpfulness` — BOOLEAN — value `1`
- Flush both the OTel SDK and the Langfuse client so traces and scores are delivered before the process exits.
- After successful execution, write the trace's ID to a log file so the verifier can find the trace and its scores.

## Implementation Hints
- Use the modular packages: `@langfuse/tracing`, `@langfuse/otel`, `@langfuse/client`, and `@opentelemetry/sdk-node`.
- The `LangfuseSpanProcessor` reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from the environment automatically.
- `startActiveObservation` from `@langfuse/tracing` opens a trace-level span; `startObservation` (or another `startActiveObservation`) with `{ asType: "generation" }` creates a nested generation. The OTel trace ID of the active span is the Langfuse trace ID.
- The `score.create` method on `LangfuseClient` accepts `{ traceId, name, value, dataType, comment? }`. For boolean scores you must pass `dataType: "BOOLEAN"` because numeric values would otherwise be inferred as `NUMERIC`.
- Remember to `await otelSdk.shutdown()` and `await langfuse.flush()` before exiting; otherwise scores may be silently dropped from a short-lived script.
- Read the run id from `process.env.ZEALT_RUN_ID` before constructing any names. Do not hardcode it.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the real Langfuse ingestion is executed and the log artifact exists.
- Log file: `/home/user/myproject/output.log`
- The script must read `run-id` from the `ZEALT_RUN_ID` environment variable and use the trace name `multi-score-demo-${run-id}`.
- A single Langfuse trace named `multi-score-demo-${run-id}` must exist after the script runs, and it must contain a nested observation of type `generation` named `llm-call`.
- Exactly three scores with names `correctness`, `sentiment`, and `helpfulness` must be attached to that trace; each must carry the correct `dataType` (`NUMERIC`, `CATEGORICAL`, `BOOLEAN`) and value (`0.92`, `"positive"`, `1`) as specified above.
- The log file must contain a line in the exact format `Trace ID: <trace_id>` where `<trace_id>` is the Langfuse trace ID that was scored.


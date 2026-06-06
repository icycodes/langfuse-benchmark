# Register a Custom Model Definition via the Langfuse CLI

## Background
Langfuse uses **Model definitions** to compute USD cost and token usage for every generation it ingests. Built-in models cover popular providers, but teams running fine-tuned, proprietary, or self-hosted models need to register their own definitions so that traces, dashboards, and cost metrics light up correctly. The full set of model definitions is exposed through the public REST API at `/api/public/models` and, by extension, through the [Langfuse CLI](https://github.com/langfuse/langfuse-cli) which dynamically wraps the OpenAPI spec.

In this task you will use the Langfuse CLI (already installed globally as `langfuse`) to programmatically register a single custom model definition in the connected Langfuse project. Because the same project is shared across parallel evaluation runs, the model name must be uniquely suffixed with the current `run-id` to avoid collisions with other concurrent trials.

## Requirements
- Project path: `/home/user/myproject`.
- Use the `langfuse-cli` (already on PATH as `langfuse`) to create the custom model definition by talking to the Langfuse public API. Do **NOT** use the Python SDK, the JS/TS SDK, or raw `curl`/HTTP requests for the creation step.
- The new model definition must have all of the following properties:
  - `modelName`: `harbor-llm-${run-id}` (with the `run-id` substituted from the `ZEALT_RUN_ID` environment variable).
  - `matchPattern`: an exact case-insensitive regex that matches only `modelName`, i.e. `(?i)^harbor-llm-${run-id}$`.
  - `unit`: `TOKENS`.
  - `inputPrice`: `0.000003` USD per input token.
  - `outputPrice`: `0.000009` USD per output token.
- Record the `id` returned by the Langfuse API for the created model in a structured log file so the verifier can locate the exact record (other rows may share the same `modelName` from prior failed runs).

## Implementation Hints
- The Langfuse CLI reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from the environment — they are already exported for you. There is no separate `login` step.
- Discover the relevant resource and its flags with `langfuse api __schema`, `langfuse api models --help`, and `langfuse api models create --help`.
- The CLI maps directly to the public REST endpoint `POST /api/public/models`. The required body fields are `modelName`, `matchPattern`, and `unit`; `inputPrice` and `outputPrice` are optional numeric fields.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable **once** at the start of your script and build the model name and match pattern from it.
- Use `--json` to obtain machine-readable output from the CLI so you can parse the returned `id` reliably and write it to the log file.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the custom model definition is actually created in the connected Langfuse project (real side effect, not mocked).
- Log file: `/home/user/myproject/output.log`
- The model definition must be created using the Langfuse CLI (`langfuse api models create ...`).
- The model definition must use the `run-id`-scoped `modelName` and `matchPattern` defined in Requirements (with `run-id` read from the `ZEALT_RUN_ID` environment variable).
- The log file `/home/user/myproject/output.log` must contain exactly one non-empty line in the format:

  ```
  Model: <modelName>=<id>
  ```

  where `<modelName>` is the full `run-id`-scoped model name and `<id>` is the `id` field returned by the Langfuse API for the created model definition.


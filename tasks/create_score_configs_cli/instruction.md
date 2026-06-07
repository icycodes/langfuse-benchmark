# Create Langfuse Score Configurations via the Langfuse CLI

## Background
Langfuse Score Configs are typed, project-scoped schemas that ensure scores follow a consistent structure (data type, value range, allowed categories). They power both manual annotation in the UI and programmatic score ingestion via the SDKs/API.

In this task you will use the [Langfuse CLI](https://github.com/langfuse/langfuse-cli) — a thin wrapper around the public REST API — to programmatically create three score configurations (one of each non-text data type) in the connected Langfuse project. Because the project may be shared across parallel evaluation runs, every config name must be uniquely suffixed with the current `run-id` to avoid collisions.

## Requirements
- Project path: `/home/user/myproject`.
- Use the `langfuse-cli` (already installed globally as `langfuse`) to create three score configurations in the connected Langfuse project. Do **NOT** use the Python SDK, JS SDK, or raw HTTP requests for the creation step.
- The three score configs must be:
  1. A **NUMERIC** score config with `minValue = 0` and `maxValue = 10`.
  2. A **CATEGORICAL** score config with exactly three categories: `positive` (value `1`), `neutral` (value `0`), `negative` (value `-1`).
  3. A **BOOLEAN** score config (no extra constraints).
- Each score config name must be suffixed with the current `run-id`, read from the `ZEALT_RUN_ID` environment variable (see Implementation Hints for exact names).
- Record the returned `id` of every created score config in a structured log file so verification can locate them.

## Implementation Hints
- The Langfuse CLI reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from the environment — they are already exported for you. You do not need to log in.
- Discover the relevant resource and its flags with `langfuse api __schema` and `langfuse api score-configs --help` / `langfuse api score-configs create --help`.
- The CLI maps directly to the public API: `POST /api/public/score-configs`. Required fields are `name` and `dataType`. For `CATEGORICAL`, you must additionally supply a list of `categories` where each entry is `{ "label": string, "value": number }`. For `NUMERIC`, supply `minValue` / `maxValue`. For `BOOLEAN`, no extra fields are needed.
- Use `--json` to get machine-readable output from the CLI so you can parse the returned `id` reliably.
- Read `run-id` from the `ZEALT_RUN_ID` env var **once** at the start, then build the three config names from it.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the score configs are actually created in the Langfuse project (real side effect, not mocked).
- Log file: `/home/user/myproject/output.log`
- The score configs must be created with the Langfuse CLI (`langfuse api score-configs create ...`).
- The three config names must be (where `${run-id}` is the value of the `ZEALT_RUN_ID` environment variable):
  - `quality-score-${run-id}` — `dataType = NUMERIC`, `minValue = 0`, `maxValue = 10`.
  - `feedback-sentiment-${run-id}` — `dataType = CATEGORICAL`, with the three categories listed in Requirements.
  - `is-relevant-${run-id}` — `dataType = BOOLEAN`.
- The log file `/home/user/myproject/output.log` must contain exactly three lines (one per created config), each in the format:

  ```
  ScoreConfig: <name>=<id>
  ```

  where `<name>` is the full config name (including the `run-id` suffix) and `<id>` is the `id` field returned by the Langfuse API for that score config.


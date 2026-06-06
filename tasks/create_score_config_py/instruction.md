# Define Score Configs in Langfuse via the Python SDK

## Background
Your team standardizes how evaluation scores are collected across projects in [Langfuse](https://langfuse.com/). To make sure annotators and automated evaluators submit scores in a consistent shape, you want to predefine two score configurations in the project using the **Langfuse Python SDK** (not the CLI):

- A **NUMERIC** score config (range bounded) used to rate response quality.
- A **CATEGORICAL** score config used to record sentiment buckets.

The SDK exposes the public API for managing score configs via the `langfuse.api.score_configs.create(...)` method (see [Manage Score Configs](https://langfuse.com/faq/all/manage-score-configs) and the [Public API Reference](https://api.reference.langfuse.com/)).

## Requirements
- Implement a Python script `create_configs.py` that uses the Langfuse Python SDK (`langfuse` package) to create the two score configs described below in the Langfuse project authenticated by `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` against the host `LANGFUSE_BASE_URL`.
- The names of both score configs **must** be suffixed with the current `run-id` (read from the `ZEALT_RUN_ID` environment variable) so that parallel runs do not collide.
- After both configs are created, write the resulting IDs to a log file so that the verifier can locate them.

## Implementation Hints
- Read `run-id` from the `ZEALT_RUN_ID` environment variable before constructing config names.
- Initialize the SDK client with `from langfuse import get_client` and call `langfuse.api.score_configs.create(...)` for each config. The request body for the public endpoint is documented in the API reference under `ScoreConfigs / POST /api/public/score-configs`.
- For the NUMERIC config you must set the data type, a description, and bounded `minValue` / `maxValue`. For the CATEGORICAL config you must set the data type, a description, and the list of allowed `categories` (each with a numeric `value` and string `label`).
- The response object exposes the new `id` of each config — capture both and write them to the log file in the exact format documented in the Acceptance Criteria.
- Remember to call `langfuse.flush()` (or rely on the SDK's exit handlers) before the script terminates so all events are delivered.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/myproject/output.log
- The `run-id` must be read from the `ZEALT_RUN_ID` environment variable and appended to every score config name created by the task.
- A NUMERIC score config must exist in the Langfuse project with name `quality-${run-id}` and bounded numeric range.
- A CATEGORICAL score config must exist in the Langfuse project with name `sentiment-${run-id}` and the three sentiment categories defined in the task truth.
- The log file must contain exactly the following two lines (in any order), where each `<id>` is the `id` returned by the Langfuse API for the corresponding score config:
  - `Numeric Score Config ID: <id>`
  - `Categorical Score Config ID: <id>`


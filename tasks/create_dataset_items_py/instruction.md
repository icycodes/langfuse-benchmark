# Create a Langfuse Dataset with Items via the Python SDK

## Background
Langfuse [Datasets](https://langfuse.com/docs/evaluation/dataset-runs/datasets) are versioned collections of `(input, expected_output, metadata)` items. They are the foundation for offline evaluation: you upload curated test cases once and then run experiments against them. Your team wants a small, reproducible Python script that bootstraps a brand new Langfuse-hosted QA dataset and seeds it with three labelled question/answer pairs so the evaluation pipeline has something to run against.

The Langfuse Public API and the Langfuse Cloud project for this task are pre-configured in the environment. Credentials are exposed as `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` so the Python SDK can pick them up automatically.

## Requirements
- Write a Python script that uses the Langfuse Python SDK (`langfuse` package) to:
  - Create a new Langfuse-hosted dataset.
  - Create exactly three dataset items inside that dataset, each with an `input`, an `expected_output`, and a `metadata` object.
- The dataset name must be derived from the `ZEALT_RUN_ID` environment variable so that concurrent runs do not collide.
- The script must flush all pending events to Langfuse before exiting so the dataset and items are durably persisted.
- After the script runs, the dataset and all three items must be retrievable through the Langfuse Public API (`/api/public/v2/datasets/{datasetName}` and `/api/public/dataset-items?datasetName=...`).

## Implementation Hints
- Install the Python SDK with `pip install langfuse` (it is already available in the environment).
- Use `langfuse.get_client()` (or `Langfuse()`); the client picks up `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from environment variables.
- The primary SDK methods you need are `langfuse.create_dataset(name=..., description=..., metadata=...)` and `langfuse.create_dataset_item(dataset_name=..., input=..., expected_output=..., metadata=...)`.
- Read the `ZEALT_RUN_ID` environment variable inside the script and use it as the suffix when constructing the dataset name.
- Call `langfuse.flush()` at the very end of the script so the writes are not lost when the process exits.
- Append a single status line to the log file containing the dataset name actually used so the verifier can find the resource on the Langfuse side.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed and the side effects on the Langfuse project are real.
- Command: `python3 /home/user/myproject/seed_dataset.py`
- Log file: /home/user/myproject/output.log
- The script must:
  - Read `run-id` from the `ZEALT_RUN_ID` environment variable.
  - Create a Langfuse-hosted dataset whose name is exactly `qa-eval-${run-id}` (no leading or trailing whitespace).
  - Create exactly three dataset items inside that dataset; each item must have a non-empty `input`, a non-empty `expectedOutput`, and a `metadata` object that includes the key `source` with value `harbor-task`.
  - Flush all pending events to Langfuse before exiting.
- The log file must contain the dataset name in the format: `Dataset name: qa-eval-<run-id>`
- After execution, the Langfuse Public API must report:
  - `GET /api/public/v2/datasets/qa-eval-${run-id}` returns HTTP 200 with `name == "qa-eval-${run-id}"`.
  - `GET /api/public/dataset-items?datasetName=qa-eval-${run-id}&limit=50` returns exactly three items, each with non-empty `input`, non-empty `expectedOutput`, and `metadata.source == "harbor-task"`.


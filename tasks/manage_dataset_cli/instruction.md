# Manage a Langfuse Evaluation Dataset with the Langfuse CLI

## Background
Langfuse is an open-source LLM engineering platform. One of its three product surfaces is Evaluation, which is built around versioned datasets, scores, and experiments. The Langfuse CLI (`langfuse-cli`, distributed via npm) dynamically wraps the entire Langfuse Public API, so every dataset and dataset-item endpoint is available as a terminal command. You will use the CLI in scripts/CI-style workflows to seed an evaluation dataset for a small geography QA app.

Your Langfuse project is already provisioned. The credentials are exposed as environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) inside the task environment. The CLI picks up these env vars automatically (no separate login step).

## Requirements
- Use the Langfuse CLI exclusively for creating and populating the dataset. Do not use the Python or JS/TS SDK, and do not call the REST API directly with curl/HTTP clients.
- Create one new Langfuse dataset whose name embeds the current `run-id`.
- Populate the dataset with exactly three items covering basic geography questions (one per European, Asian, and South American capital).
- Record the resulting Langfuse identifiers and a brief summary into a log file so that they can be machine-verified.

## Implementation Hints
- Read the value of `run-id` from the `ZEALT_RUN_ID` environment variable and use it as a suffix on the dataset name.
- The CLI is published on npm as `langfuse-cli`. You can either install it globally (`npm i -g langfuse-cli`) or invoke it one-off with `npx langfuse-cli`. Use `langfuse api __schema` and `langfuse api <resource> --help` to discover the exact command shapes for dataset and dataset-item resources.
- The CLI's authentication uses the same environment variables that the SDKs use, so no extra setup is needed once the env vars are present.
- Each created dataset/dataset-item response includes a unique `id`. Capture those ids and write them to the log file as instructed below.
- Network access to the Langfuse API host (`LANGFUSE_BASE_URL`) is required. Make sure your final command output is success-checked before writing the log file.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the dataset and items are actually created against the live Langfuse API and the log artifact exists.
- Log file: /home/user/myproject/output.log
- The Langfuse CLI (`langfuse-cli`) must be used to perform every create operation.
- The dataset name must be `geography-quiz-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The dataset must have its description set to `Geography QA evaluation dataset` (exactly this string).
- Exactly three dataset items must exist under the dataset, each with both an `input` field (a question string) and an `expectedOutput` field (the capital city). The three items must cover the following questions and answers, matched case-insensitively for the expected output and exactly for the input string:
  - input: `What is the capital of France?`  expectedOutput: `Paris`
  - input: `What is the capital of Japan?`   expectedOutput: `Tokyo`
  - input: `What is the capital of Brazil?`  expectedOutput: `Brasilia`
- The log file must contain the following lines (one per line, exact prefixes):
  - `Dataset name: geography-quiz-<run-id>`
  - `Dataset id: <dataset_id>`
  - `Item count: 3`
  - One `Item id: <id>` line per created dataset item (three lines total).


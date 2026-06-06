# Attach Scores to an Existing Trace with the Langfuse CLI

## Background

Langfuse exposes a [public CLI (`langfuse-cli`)](https://langfuse.com/docs/api-and-data-platform/features/cli) that dynamically wraps the Langfuse REST API. A common quality-assurance workflow is to ingest a trace into Langfuse and then attach one or more [scores](https://langfuse.com/docs/evaluation/evaluation-methods/custom-scores) (numeric, categorical, boolean, text) to that trace from a CI/CD job, a review script, or a terminal session.

A QA reviewer has already pushed a Langfuse trace into the project and has saved its trace ID to disk. You must now use the `langfuse-cli` to attach two scores — one numeric and one categorical — to that exact trace, then record the score IDs returned by the API in a log file.

## Requirements

- Use the `langfuse-cli` (installed in the environment as the `langfuse` command) to talk to the Langfuse API. The CLI authenticates via the `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables that are already set.
- Read the target trace ID from `/home/user/task/trace_id.txt`. This file contains a single line: the 32-character OTel trace ID.
- Create exactly two scores against that trace:
  1. A **numeric** score with name `qa_quality`, value `0.95`, data type `NUMERIC`, and comment `Approved by QA team`.
  2. A **categorical** score with name `qa_verdict`, value `approved`, data type `CATEGORICAL`, and comment `Looks good`.
- After each successful score creation, append a line containing the returned score ID to `/home/user/task/output.log`.

## Implementation Hints

- Use `langfuse api __schema` or `langfuse api scores --help` to discover the correct subcommand and flag names for creating a score.
- The score-creation endpoint returns a JSON object containing an `id` field. Use the `--json` flag and a JSON-parsing tool (such as `jq`) to extract the ID.
- Make sure both scores reference the same trace ID read from `trace_id.txt`.
- Do **not** modify or recreate the source trace; only attach scores to it.

## Acceptance Criteria

- Project path: `/home/user/task`
- Ensure the score-creation actions are actually executed via the Langfuse CLI and that the resulting score IDs are persisted to the log artifact.
- Log file: `/home/user/task/output.log`
- The log file must contain exactly two lines, one per score, in the following formats (order matters):
  - Line 1: `Numeric score ID: <score_id>`
  - Line 2: `Categorical score ID: <score_id>`
- After execution, querying the Langfuse Scores API for the trace must return:
  - A score with `name = qa_quality`, `value = 0.95`, `dataType = NUMERIC`, and `comment = Approved by QA team`.
  - A score with `name = qa_verdict`, `stringValue = approved`, `dataType = CATEGORICAL`, and `comment = Looks good`.


# Provision a Langfuse Annotation Queue via the Langfuse CLI

## Background
Langfuse Annotation Queues power human-in-the-loop evaluation workflows: reviewers pull traces or observations from a queue and score them using a predefined score configuration. In this task you must use the [Langfuse CLI](https://langfuse.com/docs/api-and-data-platform/features/cli) (`langfuse-cli`, which dynamically wraps the [Langfuse Public API](https://api.reference.langfuse.com/)) to bootstrap a complete review workflow in the Langfuse project bound to the credentials in the environment.

No Langfuse resources exist for this task yet — you must create them all through the CLI. Concretely, you need to provision **(1) one numeric score configuration** and **(2) one annotation queue** that references that score config, then record both IDs to a log file so they can be verified.

## Requirements
- Use the `langfuse-cli` (either via `npx langfuse-cli ...` or a global install) for every Langfuse API call. Do not bypass it with `curl`, the SDK, or another HTTP client.
- Create exactly one **score config** via the CLI's score-config create action (which calls `POST /api/public/score-configs`) with the following properties:
  - `name`: `answer-quality-${ZEALT_RUN_ID}`
  - `dataType`: `NUMERIC`
  - `minValue`: `0`
  - `maxValue`: `1`
  - `description`: `Quality score for QA reviewer answers (0=bad, 1=great)`
- Create exactly one **annotation queue** via the CLI's annotation-queue create action (which calls `POST /api/public/annotation-queues`) with:
  - `name`: `qa-review-queue-${ZEALT_RUN_ID}`
  - `description`: `Queue for QA reviewers to score model answers`
  - `scoreConfigIds`: a list containing exactly the ID of the score config you just created.
- After both resources are created, append both IDs to a log file so the verifier can locate them.

## Implementation Hints
- The CLI reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` (or `LANGFUSE_HOST`) from the environment — they are already exported in the task environment.
- Use `langfuse api __schema`, `langfuse api score-configs --help`, and `langfuse api annotation-queues --help` to discover the exact action and flag names.
- Pass `--json` to CLI invocations to get machine-parseable output you can inspect (e.g., with `jq` or a small Python helper) to extract the new resource IDs.
- `CreateAnnotationQueueRequest` has three fields: `name` (string, required), `scoreConfigIds` (array of strings, required), and `description` (string, optional).
- Make every externally visible identifier unique per concurrent run by reading the `ZEALT_RUN_ID` environment variable and appending it as a suffix (as specified in Requirements).

## Acceptance Criteria
- Project path: `/home/user/langfuse-task`
- Ensure the real score config and annotation queue are created in Langfuse via the `langfuse-cli` (no mocking, no direct `curl`/SDK workarounds).
- Log file: `/home/user/langfuse-task/output.log`
- The score config must exist in Langfuse with the exact `name`, `dataType`, `minValue`, `maxValue`, and `description` specified above.
- The annotation queue must exist in Langfuse with the exact `name`, `description`, and `scoreConfigIds` (a single-element list containing only the score config's ID) specified above.
- The log file must contain exactly two lines (any order), each on its own line, matching these formats:
  - `Score Config ID: <score_config_id>`
  - `Annotation Queue ID: <annotation_queue_id>`
  where each `<id>` is the value returned by the Langfuse API for the resource you just created.


# Promote a Prompt Version with Langfuse Python SDK

## Background
Your team uses Langfuse to manage versioned prompts. A movie-critic chat prompt has already been published with two versions in your Langfuse project: version 1 carries the `production` label (currently deployed) and version 2 carries the `staging` label (under review). You have validated version 2 in QA and you now need to promote it to production while also tagging it as `approved`.

Langfuse models prompt versioning through versions and labels. Labels are unique across versions of the same prompt — assigning `production` to a new version automatically removes it from the previously labeled version, giving you a deterministic deployment pointer. Read more in the [Prompt Version Control](https://langfuse.com/docs/prompt-management/features/prompt-version-control) docs.

You must perform the promotion using the Langfuse Python SDK (not the CLI, not the UI) and log evidence of the change to a log file.

## Requirements
- Read the per-run identifier from the `ZEALT_RUN_ID` environment variable. The prompt to update is named `movie-critic-${ZEALT_RUN_ID}` (lowercase, with the dash).
- Use the Langfuse Python SDK to update the labels of **version 2** of that prompt so that the new label set is exactly `["production", "approved"]`.
- After the update, fetch version 2 from Langfuse and append a log line to the log file in the format `Promoted version: <version> labels: <comma-separated-sorted-labels>`.
- Also append a log line that records the label set of version 1 after the promotion in the format `Previous version: 1 labels: <comma-separated-sorted-labels>` (since `production` is a unique label, version 1 must no longer carry it).

## Implementation Hints
- Install the `langfuse` Python SDK and authenticate via the standard `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables.
- The SDK exposes a dedicated `update_prompt` method that takes a prompt `name`, a `version`, and a `new_labels` list to replace the labels of an existing version.
- The SDK's `get_prompt` (or equivalent) call lets you read back a specific version. Bypass cached results by passing a small `cache_ttl_seconds` such as `0` when re-fetching to verify the change.
- Make sure to flush or close the client before the process exits so writes are not dropped.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed against the real Langfuse backend and the log artifact exists.
- Log file: /home/user/myproject/output.log
- The Langfuse prompt named `movie-critic-${ZEALT_RUN_ID}` (where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable) must satisfy the following after the script runs:
  - Version 2 carries exactly the labels `production` and `approved` (and the auto-managed `latest` label).
  - Version 1 no longer carries the `production` label.
- The log file must contain a line in the format: `Promoted version: 2 labels: <comma-separated-sorted-labels>` listing the labels currently attached to version 2 (excluding the auto-managed `latest`), sorted alphabetically and joined with `,` (no spaces).
- The log file must contain a line in the format: `Previous version: 1 labels: <comma-separated-sorted-labels>` listing the labels currently attached to version 1 (excluding the auto-managed `latest`), sorted alphabetically and joined with `,` (no spaces). If version 1 has no remaining labels (excluding `latest`), the value must be the literal string `none`.


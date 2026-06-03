Observability pipelines often require post-execution evaluation using custom metrics or an LLM-as-a-judge approach to track application quality.

You need to create a Python evaluation script that accepts an existing `trace_id`, computes a mock "toxicity" check (returning a float value of 0.1), and attaches this evaluation score directly to the trace in Langfuse.

**Constraints:**
- Must use the `langfuse.score()` method to record the evaluation.
- The score parameter `name` MUST be set strictly to `"toxicity"`.
- The score must be linked to the provided `trace_id` parameter without generating a new trace or span.
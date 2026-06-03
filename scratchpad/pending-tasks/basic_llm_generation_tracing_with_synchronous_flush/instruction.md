Short-lived scripts often lose trace data because the process exits before the background exporter sends the telemetry events.

You need to write a Python CLI script that uses the Langfuse drop-in OpenAI wrapper to generate a simple greeting and successfully exports the trace to Langfuse before the process terminates. 

**Constraints:**
- Must import and use the OpenAI wrapper specifically via `from langfuse.openai import openai`.
- Must explicitly call the Langfuse `flush()` method at the end of the script to prevent telemetry data loss.
- Do NOT use the standard `openai` library directly.
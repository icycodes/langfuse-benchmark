Maintaining trace context across asynchronous executions is a common friction point in Python, frequently resulting in unlinked or "orphaned" spans.

You need to implement an asynchronous Python function that fires 3 concurrent dummy LLM generation tasks, ensuring all 3 asynchronous tasks are correctly linked as spans to a single parent trace.

**Constraints:**
- Must use `asyncio.gather` to execute the concurrent generation tasks.
- Must correctly pass the parent trace context or `trace_id` into each async task so the child spans are not orphaned.
- Must explicitly flush the Langfuse client after the async batch completes.
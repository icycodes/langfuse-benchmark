import os
from langfuse import get_client

run_id = os.environ["ZEALT_RUN_ID"]

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name=f"chat-pipeline-{run_id}",
):
    trace_id = langfuse.get_current_trace_id()

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="chat-completion",
        model="gpt-4o-mini",
        input=[{"role": "user", "content": "Summarize Langfuse in one sentence."}],
        output="Langfuse is an open-source LLM engineering platform for observability, prompts, and evals.",
        usage_details={
            "input": 25,
            "output": 40,
            "total": 65,
        },
        cost_details={
            "input": 0.000125,
            "output": 0.00040,
            "total": 0.000525,
        },
    ):
        pass

langfuse.flush()

log_path = "/home/user/myproject/output.log"
with open(log_path, "w") as f:
    f.write(f"Trace ID: {trace_id}\n")

print(f"Trace ID: {trace_id}")
print(f"Log written to {log_path}")

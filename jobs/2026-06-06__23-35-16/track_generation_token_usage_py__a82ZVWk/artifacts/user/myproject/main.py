import os
from langfuse import get_client

client = get_client()

run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")

with client.start_as_current_observation(as_type="span", name=f"chat-pipeline-{run_id}") as span:
    trace_id = client.get_current_trace_id()
    
    with client.start_as_current_observation(
        as_type="generation",
        name="chat-completion",
        model="gpt-4o-mini",
        input=[{"role": "user", "content": "Summarize Langfuse in one sentence."}],
        output="Langfuse is an open-source LLM engineering platform for observability, prompts, and evals.",
        usage_details={"input": 25, "output": 40, "total": 65},
        cost_details={"input": 0.000125, "output": 0.00040, "total": 0.000525}
    ) as gen:
        pass

client.flush()

with open("/home/user/myproject/output.log", "w") as f:
    f.write(f"Trace ID: {trace_id}")

import os
from langfuse import get_client

def main():
    # Langfuse client automatically picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL
    langfuse = get_client()
    
    # Read run-id from ZEALT_RUN_ID
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    
    # Use the context manager for nested instrumentation as suggested in implementation hints
    # Create one parent observation of type `span` named `chat-pipeline-${run-id}`
    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"chat-pipeline-{run_id}"
    ) as span:
        # Inside the span, create one nested observation of type `generation` named `chat-completion`
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="chat-completion",
            model="gpt-4o-mini",
            input=[{"role": "user", "content": "Summarize Langfuse in one sentence."}],
            output="Langfuse is an open-source LLM engineering platform for observability, prompts, and evals.",
            usage_details={
                "input": 25,
                "output": 40,
                "total": 65
            },
            cost_details={
                "input": 0.000125,
                "output": 0.00040,
                "total": 0.000525
            }
        ) as generation:
            # Get the trace ID from inside the active span
            trace_id = langfuse.get_current_trace_id()
    
    # Flush the SDK to ensure data is sent
    langfuse.flush()
    
    # Write the resulting Langfuse trace ID to the log file
    log_file_path = "/home/user/myproject/output.log"
    with open(log_file_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

if __name__ == "__main__":
    main()

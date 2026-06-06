import os
import langfuse
from langfuse import observe, propagate_attributes

# Read run-id from environment
run_id = os.environ.get("ZEALT_RUN_ID", "default")

# Define identifiers
session_id = f"obs-deco-session-{run_id}"
user_id = f"obs-deco-user-{run_id}"
tags = ["obs-decorator", f"harbor-{run_id}"]

@observe(as_type="generation")
def call_llm(prompt):
    # Simulate an LLM call
    # Set model name
    langfuse.get_client().update_current_generation(
        model="gpt-3.5-turbo"
    )
    return "This is a simulated response from the LLM."

@observe()
def run_pipeline(user_query):
    # Use propagate_attributes to enrich the trace
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=tags
    ):
        # Nested call
        response = call_llm(user_query)
        
        # Get current trace id
        return langfuse.get_client().get_current_trace_id()

if __name__ == "__main__":
    # Execute pipeline
    trace_id = run_pipeline("What is the weather today?")
    
    # Force delivery of events
    langfuse.get_client().flush()
    
    # Write trace id to log file
    log_file_path = "/home/user/myproject/output.log"
    with open(log_file_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
    
    print(f"Pipeline executed successfully. Trace ID: {trace_id}")

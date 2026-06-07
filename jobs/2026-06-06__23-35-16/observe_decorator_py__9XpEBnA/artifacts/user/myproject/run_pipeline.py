import os
from langfuse import observe, get_client, propagate_attributes

run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")

@observe(as_type="generation")
def llm_call(prompt: str):
    client = get_client()
    client.update_current_generation(model="gpt-3.5-turbo")
    return "This is a dummy response."

@observe()
def pipeline(query: str):
    result = llm_call(query)
    
    client = get_client()
    trace_id = client.get_current_trace_id()
    
    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
        
    return result

if __name__ == "__main__":
    with propagate_attributes(
        user_id=f"obs-deco-user-{run_id}",
        session_id=f"obs-deco-session-{run_id}",
        tags=["obs-decorator", f"harbor-{run_id}"]
    ):
        pipeline("Hello world")
        
    get_client().flush()

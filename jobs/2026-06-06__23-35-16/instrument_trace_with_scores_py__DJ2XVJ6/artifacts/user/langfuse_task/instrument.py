import os
from langfuse import get_client, propagate_attributes

def main():
    langfuse = get_client()
    run_id = os.environ.get("ZEALT_RUN_ID", "default_run_id")
    
    trace_id = None
    obs_id = None
    
    # 1. Open a root observation of type span
    # 2. Attach user_id and session_id to the trace
    with propagate_attributes(user_id=f"user-{run_id}", session_id=f"session-{run_id}"):
        with langfuse.start_as_current_observation(name=f"process-document-{run_id}", as_type="span"):
            
            # 3. Within that span, open a nested observation of type generation
            with langfuse.start_as_current_observation(
                name=f"summarize-{run_id}",
                as_type="generation",
                model="gpt-3.5-turbo",
                input=[{"role": "user", "content": "Please summarize this document."}],
                output="This is a summary of the document."
            ):
                # 4. Capture the trace ID and the observation ID
                trace_id = langfuse.get_current_trace_id()
                obs_id = langfuse.get_current_observation_id()
    
    # 5. After contexts are closed, attach three custom scores
    if trace_id:
        langfuse.create_score(
            name="user_satisfaction",
            value=0.8,
            data_type="NUMERIC",
            trace_id=trace_id
        )
        
        if obs_id:
            langfuse.create_score(
                name="hallucination",
                value=0,
                data_type="BOOLEAN",
                trace_id=trace_id,
                observation_id=obs_id
            )
            
            langfuse.create_score(
                name="relevance",
                value="high",
                data_type="CATEGORICAL",
                trace_id=trace_id,
                observation_id=obs_id
            )
    
    # Call flush before exiting
    langfuse.flush()
    
    # Write log file
    log_content = (
        f"Trace ID: {trace_id}\n"
        f"Generation ID: {obs_id}\n"
        f"User ID: user-{run_id}\n"
        f"Session ID: session-{run_id}\n"
        f"Status: OK\n"
    )
    
    with open("/home/user/langfuse_task/output.log", "w") as f:
        f.write(log_content)

if __name__ == "__main__":
    main()

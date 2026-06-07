import os
import langfuse
from langfuse import Langfuse

def main():
    zealt_run_id = os.environ.get("ZEALT_RUN_ID", "default")
    
    lf_client = Langfuse()

    root_span_name = f"process-document-{zealt_run_id}"
    user_id = f"user-{zealt_run_id}"
    session_id = f"session-{zealt_run_id}"
    generation_name = f"summarize-{zealt_run_id}"

    # Use start_as_current_observation for nesting
    with lf_client.start_as_current_observation(
        name=root_span_name,
        as_type="span"
    ) as span:
        # Use langfuse.propagate_attributes (module-level)
        with langfuse.propagate_attributes(
            user_id=user_id,
            session_id=session_id
        ):
            trace_id = lf_client.get_current_trace_id()
            
            with lf_client.start_as_current_observation(
                name=generation_name,
                as_type="generation",
                model="gpt-3.5-turbo",
                input=[{"role": "user", "content": "Summarize this document."}],
                output="This is a fabricated summary."
            ) as generation:
                generation_id = lf_client.get_current_observation_id()

    # 5. After both contexts are closed, attach three custom scores
    lf_client.create_score(
        trace_id=trace_id,
        name="user_satisfaction",
        value=0.8,
        data_type="NUMERIC"
    )
    
    lf_client.create_score(
        trace_id=trace_id,
        observation_id=generation_id,
        name="hallucination",
        value=0,
        data_type="BOOLEAN"
    )
    
    lf_client.create_score(
        trace_id=trace_id,
        observation_id=generation_id,
        name="relevance",
        value="high",
        data_type="CATEGORICAL"
    )

    # Call flush before exiting
    lf_client.flush()
    
    # Logging for output.log
    print(f"Trace ID: {trace_id}")
    print(f"Generation ID: {generation_id}")
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print("Status: OK")

if __name__ == "__main__":
    main()

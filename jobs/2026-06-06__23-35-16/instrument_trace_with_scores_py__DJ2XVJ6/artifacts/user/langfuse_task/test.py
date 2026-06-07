from langfuse import get_client, propagate_attributes
import os

langfuse = get_client()

run_id = os.environ.get("ZEALT_RUN_ID", "test")

with propagate_attributes(user_id=f"user-{run_id}", session_id=f"session-{run_id}"):
    with langfuse.start_as_current_observation(name=f"process-document-{run_id}", as_type="span"):
        with langfuse.start_as_current_observation(
            name=f"summarize-{run_id}", 
            as_type="generation", 
            model="gpt-3.5-turbo",
            input="hello",
            output="world"
        ):
            trace_id = langfuse.get_current_trace_id()
            obs_id = langfuse.get_current_observation_id()
            print(trace_id, obs_id)

import os
from pathlib import Path

from langfuse import get_client


PROJECT_DIR = Path("/home/user/myproject")
LOG_FILE = PROJECT_DIR / "output.log"


def main() -> None:
    run_id = os.environ["ZEALT_RUN_ID"]
    trace_name = f"harbor-event-trace-{run_id}"
    event_name = f"user-login-event-{run_id}"

    langfuse = get_client()

    with langfuse.start_as_current_observation(name=trace_name, as_type="span") as parent_span:
        trace_id = parent_span.trace_id
        event = langfuse.create_event(
            name=event_name,
            input={"user_id": "u-42"},
            output={"status": "success"},
            metadata={"source": "auth-service", "region": "us-east-1"},
        )
        event_observation_id = event.id

    langfuse.flush()
    langfuse.shutdown()

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(f"Trace ID: {trace_id}\n")
        log_file.write(f"Observation ID: {event_observation_id}\n")


if __name__ == "__main__":
    main()

import os
from langfuse import get_client

def main():
    # Read run-id and derive identifiers
    run_id = os.environ.get("ZEALT_RUN_ID", "unknown").lower()
    session_id = f"chat-session-{run_id}"
    user_id = f"chat-user-{run_id}"
    tag = f"harbor-demo-{run_id}"

    # Handle potentially unexpanded environment variable in LANGFUSE_HOST
    # In some environments, LANGFUSE_HOST might be set to the literal string '$LANGFUSE_BASE_URL'
    host = os.environ.get("LANGFUSE_HOST")
    if host in ["$LANGFUSE_BASE_URL", r"\$LANGFUSE_BASE_URL"]:
        # Check if LANGFUSE_BASE_URL is set, otherwise default to cloud
        os.environ["LANGFUSE_HOST"] = os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"

    # Initialize Langfuse client
    langfuse = get_client()

    turns = [
        ("greeting-turn", "Hello! I am your AI assistant. How can I help you today?"),
        ("followup-turn", "I understand you want to learn about Langfuse sessions. They are great for grouping traces!"),
        ("farewell-turn", "You're welcome! Feel free to ask if you have more questions. Goodbye!")
    ]

    for name, output in turns:
        # Each chat turn should be its own trace (its own outer span)
        with langfuse.start_as_current_observation(
            as_type="span",
            name=name
        ) as span:
            # We use the underlying OTEL span to set trace-level attributes.
            # This ensures all three traces are linked to the same session, user, and tag.
            # The keys used are the standard Langfuse OTel attribute keys.
            span._otel_span.set_attribute("session.id", session_id)
            span._otel_span.set_attribute("user.id", user_id)
            span._otel_span.set_attribute("langfuse.trace.tags", [tag])
            
            # Add a generation observation
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="llm-response",
                model="gpt-4o-mini"
            ) as generation:
                generation.update(output=output)

    # Ensure all data is sent to Langfuse
    langfuse.flush()

    # Append Session ID to log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "a") as f:
        f.write(f"Session ID: {session_id}\n")

if __name__ == "__main__":
    main()

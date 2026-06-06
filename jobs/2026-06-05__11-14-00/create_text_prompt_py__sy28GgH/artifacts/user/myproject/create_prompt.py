import os
import logging
from langfuse import get_client

# Configure logging to write to output.log
logging.basicConfig(
    filename="/home/user/myproject/output.log",
    level=logging.INFO,
    format="%(message)s",
)

def main():
    # Read the run ID from environment
    run_id = os.environ.get("ZEALT_RUN_ID", "default")

    # Build the prompt name with the run ID suffix
    prompt_name = f"movie-critic-text-{run_id}"

    # Initialise the Langfuse client (reads credentials from env vars)
    langfuse = get_client()

    # Create a text prompt with at least one {{variable}} placeholder,
    # a non-empty config, at least one tag, and the "production" label.
    prompt = langfuse.create_prompt(
        name=prompt_name,
        type="text",
        prompt=(
            "You are an expert movie critic. "
            "Write a detailed review for the movie '{{movie_title}}' "
            "released in {{release_year}}. "
            "Focus on {{review_aspect}} and provide a rating out of 10."
        ),
        config={
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 512,
        },
        tags=["movie-critic", "text-prompt", "automated"],
        labels=["production"],
    )

    # Log the name and version to the audit log file
    logging.info("Prompt Name: %s", prompt.name)
    logging.info("Prompt Version: %s", prompt.version)

    print(f"Prompt Name: {prompt.name}")
    print(f"Prompt Version: {prompt.version}")

    # Flush pending background work before exit
    langfuse.flush()


if __name__ == "__main__":
    main()

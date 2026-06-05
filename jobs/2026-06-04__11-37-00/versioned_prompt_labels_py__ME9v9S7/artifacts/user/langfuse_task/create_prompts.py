import os
from langfuse import Langfuse

def main():
    # Initialize Langfuse client
    # It reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL from env
    langfuse = Langfuse()

    zealt_run_id = os.getenv("ZEALT_RUN_ID")
    if not zealt_run_id:
        raise ValueError("ZEALT_RUN_ID environment variable is not set")

    prompt_name = f"movie-critic-chat-{zealt_run_id}"

    # Version 1: Baseline prompt (staging)
    # References {{criticlevel}} and {{movie}}
    v1_messages = [
        {"role": "system", "content": "You are a movie critic with a {{criticlevel}} level of critical analysis."},
        {"role": "user", "content": "Please review the movie: {{movie}}."}
    ]
    
    print(f"Creating version 1 of prompt: {prompt_name}")
    v1 = langfuse.create_prompt(
        name=prompt_name,
        prompt=v1_messages,
        type="chat",
        labels=["staging"]
    )
    staging_version = v1.version

    # Version 2: Enhanced prompt (production)
    # References {{criticlevel}}, {{movie}}, and {{genre}}
    v2_messages = [
        {"role": "system", "content": "You are an expert movie critic specialized in {{genre}}. Your critical analysis level is {{criticlevel}}."},
        {"role": "user", "content": "Provide a detailed review for the movie: {{movie}}."}
    ]

    print(f"Creating version 2 of prompt: {prompt_name}")
    v2 = langfuse.create_prompt(
        name=prompt_name,
        prompt=v2_messages,
        type="chat",
        labels=["production"]
    )
    production_version = v2.version

    # Ensure all events are sent
    langfuse.flush()

    # Write log file
    log_path = "/home/user/langfuse_task/output.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"Prompt name: {prompt_name}\n")
        f.write(f"Staging version: {staging_version}\n")
        f.write(f"Production version: {production_version}\n")
    
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    main()

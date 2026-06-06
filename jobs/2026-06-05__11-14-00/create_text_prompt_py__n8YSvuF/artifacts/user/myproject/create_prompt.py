import os
from langfuse import get_client

def main():
    run_id = os.getenv("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set")
        return

    prompt_name = f"movie-critic-text-{run_id}"
    
    # Initialize Langfuse client
    langfuse = get_client()

    # Create the text prompt
    # Based on Langfuse documentation and requirements:
    # - name: movie-critic-text-${run-id}
    # - prompt: content with {{variable}}
    # - type: "text"
    # - config: non-empty dict
    # - tags: at least one tag
    # - labels: includes "production"
    
    try:
        prompt = langfuse.create_prompt(
            name=prompt_name,
            prompt="You are a professional movie critic. Review the following movie: {{movie_name}}. Provide a rating out of 10.",
            type="text",
            config={
                "model": "gpt-4",
                "temperature": 0.5,
                "max_tokens": 500
            },
            tags=["automated-test"],
            labels=["production"]
        )

        # Log the resulting prompt's name and version to the log file
        log_path = "/home/user/myproject/output.log"
        with open(log_path, "w") as log_file:
            log_file.write(f"Prompt Name: {prompt.name}\n")
            log_file.write(f"Prompt Version: {prompt.version}\n")

        print(f"Prompt created successfully: {prompt.name}, version: {prompt.version}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Flush pending work before exit
        langfuse.flush()

if __name__ == "__main__":
    main()

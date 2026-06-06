import os
import json
from langfuse import Langfuse

def main():
    # Read environment variables
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID not set")
        return

    prompt_name = f"movie-critic-chat-{run_id}"
    
    # Instantiate Langfuse client
    # Credentials are automatically picked up from LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
    langfuse = Langfuse()

    # Define the chat prompt payload
    prompt_payload = [
        {"role": "system", "content": "You are an {{criticlevel}} movie critic"},
        {"type": "placeholder", "name": "chat_history"},
        {"role": "user", "content": "What should I watch next?"}
    ]

    # Create the prompt
    langfuse.create_prompt(
        name=prompt_name,
        prompt=prompt_payload,
        labels=["production"],
        type="chat"
    )

    # Fetch the prompt back
    prompt = langfuse.get_prompt(prompt_name, label="production")

    # Compile the prompt
    chat_history = [
        {"role": "user", "content": "I love Ron Fricke movies like Baraka"},
        {"role": "user", "content": "Also, the Korean movie Memories of a Murderer"}
    ]
    
    compiled_messages = prompt.compile(
        criticlevel="expert",
        chat_history=chat_history
    )

    # Save to output log
    output_path = "/home/user/myproject/output.log"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(f"Prompt name: {prompt_name}\n")
        f.write(f"Compiled prompt: {json.dumps(compiled_messages)}\n")

    # Flush pending events
    langfuse.flush()
    print(f"Successfully created and compiled prompt. Output saved to {output_path}")

if __name__ == "__main__":
    main()

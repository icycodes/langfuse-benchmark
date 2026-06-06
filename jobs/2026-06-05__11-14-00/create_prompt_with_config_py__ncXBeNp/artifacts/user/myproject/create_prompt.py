import os
from langfuse import Langfuse

def main():
    # Read environment variables
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise ValueError("ZEALT_RUN_ID environment variable is not set")
    
    prompt_name = f"invoice-extractor-{run_id}"
    
    # Initialize Langfuse client
    # Credentials are automatically picked up from environment variables:
    # LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
    langfuse = Langfuse()
    
    # Define the chat prompt messages
    prompt_messages = [
        {"role": "system", "content": "You are an expert invoice extractor. Extract information from the provided text into the specified JSON format."},
        {"role": "user", "content": "Extract invoice details from this text: {{invoice_text}}"}
    ]
    
    # Define the config object
    config = {
        "model": "gpt-4o",
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "invoice_extraction",
                "schema": {
                    "type": "object",
                    "properties": {
                        "invoice_number": {"type": "string"},
                        "total_amount": {"type": "number"},
                        "vendor_name": {"type": "string"}
                    },
                    "required": ["invoice_number", "total_amount", "vendor_name"]
                }
            }
        }
    }
    
    # Create the prompt
    print(f"Creating prompt: {prompt_name}")
    langfuse.create_prompt(
        name=prompt_name,
        type="chat",
        prompt=prompt_messages,
        config=config,
        labels=["production", "staging"]
    )
    
    # Flush to ensure the creation is sent
    langfuse.flush()
    
    # Fetch it back with caching disabled
    fetched_prompt = langfuse.get_prompt(prompt_name, cache_ttl_seconds=0)
    
    # Write to log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Prompt name: {fetched_prompt.name}\n")
        f.write(f"Prompt version: {fetched_prompt.version}\n")
        
        # Determine prompt type (chat or text)
        # Based on Langfuse SDK, ChatPromptClient has prompt as a list, TextPromptClient as a string
        prompt_type = "chat" if isinstance(fetched_prompt.prompt, list) else "text"
        f.write(f"Prompt type: {prompt_type}\n")
        
        # Get config keys
        config_keys = ", ".join(fetched_prompt.config.keys())
        f.write(f"Config keys: {config_keys}\n")
        
        # Labels - remove 'latest' from the list if it's there to match exactly "production, staging" 
        # or just keep it if the requirement allows. 
        # The requirement says: "Labels: production, staging"
        labels = [l for l in fetched_prompt.labels if l != "latest"]
        labels_str = ", ".join(labels)
        f.write(f"Labels: {labels_str}\n")
    
    print(f"Successfully wrote log to {log_path}")

if __name__ == "__main__":
    main()

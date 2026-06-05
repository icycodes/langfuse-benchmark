import os
from langfuse import Langfuse

def main():
    # Read ZEALT_RUN_ID environment variable
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        raise ValueError("ZEALT_RUN_ID environment variable is not set")

    dataset_name = f"qa-eval-{run_id}"
    
    # Initialize Langfuse client
    # Credentials (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL) 
    # are picked up automatically from environment variables.
    langfuse = Langfuse()

    # Create a new Langfuse-hosted dataset
    langfuse.create_dataset(
        name=dataset_name,
        description="A dataset for QA evaluation",
        metadata={"run_id": run_id}
    )

    # Dataset items to seed
    items = [
        {
            "input": "What is the capital of France?",
            "expected_output": "Paris",
            "metadata": {"source": "harbor-task", "difficulty": "easy"}
        },
        {
            "input": "Who wrote 'Romeo and Juliet'?",
            "expected_output": "William Shakespeare",
            "metadata": {"source": "harbor-task", "difficulty": "easy"}
        },
        {
            "input": "What is the largest planet in our solar system?",
            "expected_output": "Jupiter",
            "metadata": {"source": "harbor-task", "difficulty": "easy"}
        }
    ]

    # Create exactly three dataset items inside the dataset
    for item in items:
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=item["input"],
            expected_output=item["expected_output"],
            metadata=item["metadata"]
        )

    # Flush all pending events to Langfuse before exiting
    langfuse.flush()

    # Log the dataset name to the output file
    # The requirement says: Append a single status line to the log file 
    # containing the dataset name actually used.
    log_file_path = "/home/user/myproject/output.log"
    with open(log_file_path, "a") as f:
        f.write(f"Dataset name: {dataset_name}\n")

if __name__ == "__main__":
    main()

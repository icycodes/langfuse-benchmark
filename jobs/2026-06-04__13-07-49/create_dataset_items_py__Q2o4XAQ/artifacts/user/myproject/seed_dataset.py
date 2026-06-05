#!/usr/bin/env python3
"""Seed a Langfuse dataset with three QA items for evaluation pipelines."""

import os
from langfuse import Langfuse

def main():
    # Read the run ID from the environment
    run_id = os.environ["ZEALT_RUN_ID"]
    dataset_name = f"qa-eval-{run_id}"

    # Initialize the Langfuse client (picks up LANGFUSE_PUBLIC_KEY,
    # LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env)
    client = Langfuse()

    # Create the dataset
    client.create_dataset(
        name=dataset_name,
        description="QA evaluation dataset seeded by harbor-task",
        metadata={"source": "harbor-task"},
    )

    # Define three QA items
    items = [
        {
            "input": {"question": "What is the capital of France?"},
            "expected_output": {"answer": "Paris"},
            "metadata": {"source": "harbor-task", "difficulty": "easy"},
        },
        {
            "input": {"question": "What is the speed of light in vacuum?"},
            "expected_output": {"answer": "299,792,458 m/s"},
            "metadata": {"source": "harbor-task", "difficulty": "medium"},
        },
        {
            "input": {"question": "Who wrote 'The Art of War'?"},
            "expected_output": {"answer": "Sun Tzu"},
            "metadata": {"source": "harbor-task", "difficulty": "easy"},
        },
    ]

    # Create each dataset item
    for item in items:
        client.create_dataset_item(
            dataset_name=dataset_name,
            input=item["input"],
            expected_output=item["expected_output"],
            metadata=item["metadata"],
        )

    # Flush all pending events to ensure durability
    client.flush()

    # Write the dataset name to the log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "a") as log_file:
        log_file.write(f"Dataset name: {dataset_name}\n")

    print(f"Dataset '{dataset_name}' created with 3 items.")

if __name__ == "__main__":
    main()
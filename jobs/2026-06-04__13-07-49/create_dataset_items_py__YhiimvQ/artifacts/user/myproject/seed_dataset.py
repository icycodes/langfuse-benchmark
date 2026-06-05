import os
from langfuse import Langfuse

# Read run ID and construct dataset name
run_id = os.environ["ZEALT_RUN_ID"]
dataset_name = f"qa-eval-{run_id}"

# Initialise client (picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)
langfuse = Langfuse()

# Create the dataset
langfuse.create_dataset(
    name=dataset_name,
    description="QA evaluation dataset seeded by harbor-task",
    metadata={"created_by": "seed_dataset.py"},
)

# Three labelled QA pairs
items = [
    {
        "input": {"question": "What is the capital of France?"},
        "expected_output": {"answer": "Paris"},
        "metadata": {"source": "harbor-task", "difficulty": "easy"},
    },
    {
        "input": {"question": "What is the boiling point of water at sea level in Celsius?"},
        "expected_output": {"answer": "100"},
        "metadata": {"source": "harbor-task", "difficulty": "easy"},
    },
    {
        "input": {"question": "Who wrote the play Romeo and Juliet?"},
        "expected_output": {"answer": "William Shakespeare"},
        "metadata": {"source": "harbor-task", "difficulty": "medium"},
    },
]

for item in items:
    langfuse.create_dataset_item(
        dataset_name=dataset_name,
        input=item["input"],
        expected_output=item["expected_output"],
        metadata=item["metadata"],
    )

# Flush all pending events before exit
langfuse.flush()

# Write status line to log file
log_path = "/home/user/myproject/output.log"
with open(log_path, "a") as f:
    f.write(f"Dataset name: {dataset_name}\n")

print(f"Dataset name: {dataset_name}")
print("All three dataset items created and flushed successfully.")

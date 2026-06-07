"""
Create two score configurations in Langfuse:
- A NUMERIC score config named quality-<run-id>
- A CATEGORICAL score config named sentiment-<run-id>

Reads run-id from ZEALT_RUN_ID env var.
Writes resulting IDs to output.log.
"""

import os
from langfuse import get_client
from langfuse.api.commons.types.score_config_data_type import ScoreConfigDataType
from langfuse.api.commons.types.config_category import ConfigCategory

def main():
    # Read run-id from environment
    run_id = os.environ["ZEALT_RUN_ID"]

    # Initialize the Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)
    langfuse = get_client()

    # --- Create NUMERIC score config ---
    numeric_name = f"quality-{run_id}"
    numeric_config = langfuse.api.score_configs.create(
        name=numeric_name,
        data_type=ScoreConfigDataType.NUMERIC,
        description="Rates overall response quality on a bounded numeric scale.",
        min_value=0.0,
        max_value=10.0,
    )
    numeric_id = numeric_config.id
    print(f"Created NUMERIC score config '{numeric_name}' with ID: {numeric_id}")

    # --- Create CATEGORICAL score config ---
    categorical_name = f"sentiment-{run_id}"
    categories = [
        ConfigCategory(value=0.0, label="negative"),
        ConfigCategory(value=1.0, label="neutral"),
        ConfigCategory(value=2.0, label="positive"),
    ]
    categorical_config = langfuse.api.score_configs.create(
        name=categorical_name,
        data_type=ScoreConfigDataType.CATEGORICAL,
        description="Records the sentiment of a response as one of three buckets.",
        categories=categories,
    )
    categorical_id = categorical_config.id
    print(f"Created CATEGORICAL score config '{categorical_name}' with ID: {categorical_id}")

    # Flush any pending events
    langfuse.flush()

    # Write IDs to output.log
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
    with open(log_path, "w") as f:
        f.write(f"Numeric Score Config ID: {numeric_id}\n")
        f.write(f"Categorical Score Config ID: {categorical_id}\n")

    print(f"IDs written to {log_path}")


if __name__ == "__main__":
    main()

"""Create Langfuse score configs for quality (numeric) and sentiment (categorical)."""

import os
import sys

from langfuse import get_client
from langfuse.api.commons.types.score_config_data_type import ScoreConfigDataType
from langfuse.api.commons.types.config_category import ConfigCategory


def main() -> None:
    # Read run-id from environment
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set", file=sys.stderr)
        sys.exit(1)

    # Initialize the Langfuse client (reads LANGFUSE_PUBLIC_KEY,
    # LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env)
    langfuse = get_client()

    # --- Create NUMERIC score config: quality-{run_id} ---
    numeric_config = langfuse.api.score_configs.create(
        name=f"quality-{run_id}",
        data_type=ScoreConfigDataType.NUMERIC,
        description="Response quality rating on a bounded numeric scale.",
        min_value=0.0,
        max_value=5.0,
    )

    # --- Create CATEGORICAL score config: sentiment-{run_id} ---
    categorical_config = langfuse.api.score_configs.create(
        name=f"sentiment-{run_id}",
        data_type=ScoreConfigDataType.CATEGORICAL,
        description="Sentiment classification bucket.",
        categories=[
            ConfigCategory(value=1.0, label="positive"),
            ConfigCategory(value=0.0, label="neutral"),
            ConfigCategory(value=-1.0, label="negative"),
        ],
    )

    # Flush pending events
    langfuse.flush()

    # Write IDs to the log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Numeric Score Config ID: {numeric_config.id}\n")
        f.write(f"Categorical Score Config ID: {categorical_config.id}\n")

    print(f"Created numeric config: {numeric_config.id}")
    print(f"Created categorical config: {categorical_config.id}")
    print(f"Log written to {log_path}")


if __name__ == "__main__":
    main()
import os
import sys
from langfuse import get_client
from langfuse.api.commons.types.score_config_data_type import ScoreConfigDataType
from langfuse.api.commons.types.config_category import ConfigCategory

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    client = get_client()

    # Create NUMERIC score config
    numeric_name = f"quality-{run_id}"
    numeric_config = client.api.score_configs.create(
        name=numeric_name,
        data_type=ScoreConfigDataType.NUMERIC,
        description="Rating of response quality",
        min_value=0.0,
        max_value=1.0
    )

    # Create CATEGORICAL score config
    categorical_name = f"sentiment-{run_id}"
    categorical_config = client.api.score_configs.create(
        name=categorical_name,
        data_type=ScoreConfigDataType.CATEGORICAL,
        description="Sentiment of the response",
        categories=[
            ConfigCategory(value=1.0, label="Positive"),
            ConfigCategory(value=0.0, label="Neutral"),
            ConfigCategory(value=-1.0, label="Negative")
        ]
    )

    client.flush()

    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Numeric Score Config ID: {numeric_config.id}\n")
        f.write(f"Categorical Score Config ID: {categorical_config.id}\n")

if __name__ == "__main__":
    main()

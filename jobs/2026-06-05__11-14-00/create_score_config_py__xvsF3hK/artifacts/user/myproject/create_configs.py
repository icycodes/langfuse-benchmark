import os
from langfuse import get_client

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = os.environ.get("LANGFUSE_BASE_URL")

    if not all([run_id, public_key, secret_key, base_url]):
        print("Missing environment variables")
        return

    # Langfuse SDK expects LANGFUSE_HOST for the base URL when using get_client() or Langfuse()
    os.environ["LANGFUSE_HOST"] = base_url

    # Initialize SDK client with get_client as requested
    langfuse = get_client()

    # 1. Create NUMERIC score config
    # Range bounded (e.g., 0-10)
    numeric_config = langfuse.api.score_configs.create(
        name=f"quality-{run_id}",
        data_type="NUMERIC",
        description="Rate response quality",
        min_value=0.0,
        max_value=10.0
    )
    numeric_id = numeric_config.id

    # 2. Create CATEGORICAL score config
    # Three sentiment categories
    categorical_config = langfuse.api.score_configs.create(
        name=f"sentiment-{run_id}",
        data_type="CATEGORICAL",
        description="Record sentiment buckets",
        categories=[
            {"label": "Positive", "value": 1.0},
            {"label": "Neutral", "value": 0.0},
            {"label": "Negative", "value": -1.0}
        ]
    )
    categorical_id = categorical_config.id

    # Write IDs to log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Numeric Score Config ID: {numeric_id}\n")
        f.write(f"Categorical Score Config ID: {categorical_id}\n")
    
    langfuse.flush()

if __name__ == "__main__":
    main()

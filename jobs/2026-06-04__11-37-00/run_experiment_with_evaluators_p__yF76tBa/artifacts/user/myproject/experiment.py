"""
Langfuse Experiment: Sentiment Classification with Custom Evaluators
"""

import os
from langfuse import get_client, Evaluation
from langfuse.experiment import ExperimentItemResult

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
run_id = os.environ["ZEALT_RUN_ID"]
dataset_name = f"harbor-eval-{run_id}"
run_name = f"experiment-{run_id}"

langfuse = get_client()

# ---------------------------------------------------------------------------
# 1. Create dataset
# ---------------------------------------------------------------------------
langfuse.create_dataset(name=dataset_name)

# ---------------------------------------------------------------------------
# 2. Add 5 dataset items (at least 2 distinct labels)
# ---------------------------------------------------------------------------
items_data = [
    {
        "input": "I absolutely love this product, it works great!",
        "expected_output": "positive",
    },
    {
        "input": "This is the worst experience I have ever had.",
        "expected_output": "negative",
    },
    {
        "input": "The package arrived on time.",
        "expected_output": "neutral",
    },
    {
        "input": "Fantastic service, I am very happy with the results.",
        "expected_output": "positive",
    },
    {
        "input": "I hate how slow and buggy this software is.",
        "expected_output": "negative",
    },
]

for item in items_data:
    langfuse.create_dataset_item(
        dataset_name=dataset_name,
        input=item["input"],
        expected_output=item["expected_output"],
    )

# ---------------------------------------------------------------------------
# 3. Deterministic sentiment classifier (no external LLM)
# ---------------------------------------------------------------------------
POSITIVE_KEYWORDS = {
    "love", "great", "fantastic", "happy", "excellent", "wonderful",
    "amazing", "best", "good", "awesome", "enjoy", "like", "pleased",
    "satisfied", "superb", "brilliant", "perfect", "nice",
}
NEGATIVE_KEYWORDS = {
    "hate", "worst", "terrible", "awful", "horrible", "bad", "poor",
    "disappoint", "disappointing", "disappointed", "ugly", "slow",
    "buggy", "broken", "useless", "trash", "garbage", "never",
}


def classify_sentiment(text: str) -> str:
    """Rule-based, deterministic sentiment classifier."""
    lower = text.lower()
    words = set(lower.split())
    pos = len(words & POSITIVE_KEYWORDS)
    neg = len(words & NEGATIVE_KEYWORDS)

    # Also count substring matches for compound words / contractions
    for kw in POSITIVE_KEYWORDS:
        if kw in lower:
            pos += 1
    for kw in NEGATIVE_KEYWORDS:
        if kw in lower:
            neg += 1

    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# 4. Task function
# ---------------------------------------------------------------------------
def task(*, item, **kwargs):
    return classify_sentiment(item.input)


# ---------------------------------------------------------------------------
# 5. Item-level evaluator: accuracy
# ---------------------------------------------------------------------------
def accuracy_evaluator(*, output, expected_output, **kwargs) -> Evaluation:
    correct = str(output).lower().strip() == str(expected_output).lower().strip()
    return Evaluation(name="accuracy", value=1.0 if correct else 0.0)


# ---------------------------------------------------------------------------
# 6. Run-level evaluator: avg_accuracy
# ---------------------------------------------------------------------------
def avg_accuracy_evaluator(*, item_results, **kwargs) -> Evaluation:
    values = []
    for result in item_results:
        for ev in result.evaluations:
            if ev.name == "accuracy":
                values.append(float(ev.value))
    avg = sum(values) / len(values) if values else 0.0
    return Evaluation(name="avg_accuracy", value=avg)


# ---------------------------------------------------------------------------
# 7. Run experiment against the Langfuse-hosted dataset
# ---------------------------------------------------------------------------
dataset = langfuse.get_dataset(dataset_name)

result = langfuse.run_experiment(
    name=run_name,
    run_name=run_name,
    data=dataset.items,
    task=task,
    evaluators=[accuracy_evaluator],
    run_evaluators=[avg_accuracy_evaluator],
)

# ---------------------------------------------------------------------------
# 8. Flush so everything is persisted
# ---------------------------------------------------------------------------
langfuse.flush()

# ---------------------------------------------------------------------------
# 9. Write output log
# ---------------------------------------------------------------------------
# Compute mean accuracy from item results
accuracy_values = []
for item_result in result.item_results:
    for ev in item_result.evaluations:
        if ev.name == "accuracy":
            accuracy_values.append(float(ev.value))

mean_accuracy = sum(accuracy_values) / len(accuracy_values) if accuracy_values else 0.0

log_lines = [
    f"Dataset name: {dataset_name}",
    f"Dataset run name: {run_name}",
    f"Items: {len(result.item_results)}",
    f"Accuracy: {mean_accuracy:.2f}",
    "Status: OK",
]

log_path = "/home/user/myproject/output.log"
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, "w") as f:
    f.write("\n".join(log_lines) + "\n")

print("\n".join(log_lines))
print(f"\nDataset run URL: {result.dataset_run_url}")

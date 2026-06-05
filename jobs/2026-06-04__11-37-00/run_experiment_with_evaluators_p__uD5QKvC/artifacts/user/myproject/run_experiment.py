#!/usr/bin/env python3
"""Langfuse experiment with custom evaluators for sentiment classification."""

import os
from langfuse import get_client, Evaluation


def main():
    run_id = os.environ["ZEALT_RUN_ID"]
    dataset_name = f"harbor-eval-{run_id}"
    run_name = f"experiment-{run_id}"

    langfuse = get_client()

    # ── 1. Create dataset ────────────────────────────────────────────────
    dataset = langfuse.create_dataset(name=dataset_name)

    # ── 2. Add 5 dataset items covering positive, negative, neutral ──────
    items_data = [
        {"input": "I love this product, it is amazing!", "expected_output": "positive"},
        {"input": "This is the worst experience I have ever had.", "expected_output": "negative"},
        {"input": "The package arrived on Tuesday.", "expected_output": "neutral"},
        {"input": "What a wonderful and joyful day!", "expected_output": "positive"},
        {"input": "I am very disappointed with the service.", "expected_output": "negative"},
    ]

    for item in items_data:
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=item["input"],
            expected_output=item["expected_output"],
        )

    # ── 3. Deterministic sentiment classifier (no LLM) ──────────────────
    POSITIVE_WORDS = {
        "love", "loved", "loves", "amazing", "wonderful", "joyful", "great",
        "awesome", "fantastic", "excellent", "happy", "glad", "best",
    }
    NEGATIVE_WORDS = {
        "worst", "hate", "hated", "terrible", "awful", "horrible", "disappointed",
        "disappointing", "bad", "poor", "sad", "angry", "upset",
    }

    def classify_sentiment(*, item, **kwargs):
        text = item["input"] if isinstance(item, dict) else item.input
        words = set(text.lower().replace("!", "").replace(".", "").split())
        pos_hits = len(words & POSITIVE_WORDS)
        neg_hits = len(words & NEGATIVE_WORDS)
        if pos_hits > neg_hits:
            return "positive"
        elif neg_hits > pos_hits:
            return "negative"
        else:
            return "neutral"

    # ── 4. Item-level evaluator: accuracy ────────────────────────────────
    def accuracy(*, input, output, expected_output, **kwargs):
        if expected_output is None:
            return Evaluation(name="accuracy", value=0.0)
        match = output.strip().lower() == expected_output.strip().lower()
        return Evaluation(
            name="accuracy",
            value=1.0 if match else 0.0,
            comment="Correct" if match else "Incorrect",
        )

    # ── 5. Run-level evaluator: avg_accuracy ─────────────────────────────
    def avg_accuracy(*, item_results, **kwargs):
        accuracies = []
        for result in item_results:
            for ev in result.evaluations:
                if ev.name == "accuracy":
                    accuracies.append(float(ev.value))
        mean_val = sum(accuracies) / len(accuracies) if accuracies else 0.0
        return Evaluation(
            name="avg_accuracy",
            value=mean_val,
            comment=f"Mean accuracy across {len(accuracies)} items",
        )

    # ── 6. Fetch dataset and run experiment ─────────────────────────────
    dataset = langfuse.get_dataset(dataset_name)

    result = langfuse.run_experiment(
        name=f"Sentiment Experiment {run_id}",
        run_name=run_name,
        data=dataset.items,
        task=classify_sentiment,
        evaluators=[accuracy],
        run_evaluators=[avg_accuracy],
    )

    # ── 7. Flush to ensure everything is persisted ───────────────────────
    langfuse.flush()

    # ── 8. Compute accuracy for the log ──────────────────────────────────
    acc_values = []
    for ir in result.item_results:
        for ev in ir.evaluations:
            if ev.name == "accuracy":
                acc_values.append(float(ev.value))

    mean_accuracy = sum(acc_values) / len(acc_values) if acc_values else 0.0
    num_items = len(result.item_results)

    # ── 9. Write log file ────────────────────────────────────────────────
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Dataset name: {dataset_name}\n")
        f.write(f"Dataset run name: {run_name}\n")
        f.write(f"Items: {num_items}\n")
        f.write(f"Accuracy: {mean_accuracy:.2f}\n")
        f.write("Status: OK\n")

    print(f"Experiment complete. Log written to {log_path}")
    print(f"  Dataset name: {dataset_name}")
    print(f"  Dataset run name: {run_name}")
    print(f"  Items: {num_items}")
    print(f"  Accuracy: {mean_accuracy:.2f}")


if __name__ == "__main__":
    main()
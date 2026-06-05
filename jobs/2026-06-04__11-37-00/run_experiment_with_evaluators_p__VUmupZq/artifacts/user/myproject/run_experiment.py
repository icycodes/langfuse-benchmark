import os
from langfuse import Langfuse, Evaluation

def classify_sentiment(*, item, **kwargs):
    """Simple keyword-based sentiment classifier.
    Task function must accept 'item' as keyword argument.
    """
    input_str = item.input if hasattr(item, 'input') else item.get('input', '')
    input_lower = input_str.lower()
    if any(word in input_lower for word in ["good", "great", "happy", "excellent", "wonderful"]):
        return "positive"
    elif any(word in input_lower for word in ["bad", "sad", "awful", "terrible", "poor"]):
        return "negative"
    else:
        return "neutral"

def accuracy_evaluator(*, input, output, expected_output=None, **kwargs):
    """Item-level evaluator for accuracy."""
    is_correct = str(output).lower() == str(expected_output).lower()
    return Evaluation(name="accuracy", value=1.0 if is_correct else 0.0)

def avg_accuracy_evaluator(*, item_results, **kwargs):
    """Run-level evaluator for average accuracy."""
    accuracies = []
    for result in item_results:
        for evaluation in result.evaluations:
            if evaluation.name == "accuracy":
                accuracies.append(evaluation.value)
    
    avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0.0
    return Evaluation(name="avg_accuracy", value=avg_acc)

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "local")
    dataset_name = f"harbor-eval-{run_id}"
    experiment_run_name = f"experiment-{run_id}"
    
    langfuse = Langfuse()
    
    # 1. Create dataset
    try:
        langfuse.create_dataset(name=dataset_name)
    except Exception as e:
        print(f"Dataset might already exist: {e}")

    # 2. Add 5 items
    items_to_add = [
        {"input": "This is a great day!", "expected_output": "positive"},
        {"input": "I am feeling very sad.", "expected_output": "negative"},
        {"input": "The weather is okay today.", "expected_output": "neutral"},
        {"input": "What an excellent performance!", "expected_output": "positive"},
        {"input": "This service is terrible.", "expected_output": "negative"},
    ]
    
    for item in items_to_add:
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=item["input"],
            expected_output=item["expected_output"]
        )
    
    # 3. Run experiment
    dataset = langfuse.get_dataset(dataset_name)
    
    # Use the items from the dataset to run the experiment
    # run_experiment name is the experiment name (human readable)
    # run_name is the exact dataset run name
    langfuse.run_experiment(
        name=f"Experiment for {run_id}",
        run_name=experiment_run_name,
        data=dataset.items,
        task=classify_sentiment,
        evaluators=[accuracy_evaluator],
        run_evaluators=[avg_accuracy_evaluator]
    )
    
    # 4. Flush to ensure data is sent
    langfuse.flush()
    
    # 5. Calculate metrics for logging
    correct_count = 0
    for item in items_to_add:
        prediction = classify_sentiment(item={"input": item["input"]})
        if prediction.lower() == item["expected_output"].lower():
            correct_count += 1
    
    avg_acc = correct_count / len(items_to_add)
    
    # 6. Write output.log
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Dataset name: {dataset_name}\n")
        f.write(f"Dataset run name: {experiment_run_name}\n")
        f.write(f"Items: {len(items_to_add)}\n")
        f.write(f"Accuracy: {avg_acc:.2f}\n")
        f.write("Status: OK\n")

if __name__ == "__main__":
    main()

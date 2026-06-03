Langfuse datasets are collections of inputs and expected outputs used to benchmark LLM application performance and prevent regressions.

You need to write a script that reads an array of dictionaries representing Q&A pairs and uploads each item to initialize a new Langfuse evaluation dataset.

**Constraints:**
- Must use the `langfuse.create_dataset_item()` method for each entry in the array.
- The `dataset_name` parameter must be strictly set to `"v1-regression-tests"`.
- Both the `input` and `expected_output` properties must be populated for each created dataset item.
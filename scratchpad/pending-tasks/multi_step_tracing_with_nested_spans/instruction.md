Complex LLM applications like RAG require tracking multiple units of work (e.g., document retrieval followed by generation) under a single parent trace for accurate debugging.

You need to instrument a mock two-step Python RAG pipeline, ensuring that both the retrieval step and the generation step are captured accurately as child spans of a main observation.

**Constraints:**
- Must use the Langfuse context manager (`with langfuse.start_as_current_observation(...):`).
- The root parent span must be named exactly `"rag-pipeline"`.
- The nested child spans must be explicitly named `"document-retrieval"` and `"llm-generation"`.
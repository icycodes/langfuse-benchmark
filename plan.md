# Langfuse Benchmark Research Plan

## 1. Library Overview

*   **Description**: Langfuse is an open-source LLM engineering platform designed for observability, prompt management, evaluation, and dataset management. it helps teams debug, analyze, and iterate on LLM applications by providing a centralized dashboard for traces, scores, and prompts.
*   **Ecosystem Role**: It acts as the "observability and evaluation" layer in the AI stack, sitting between the application logic (Python/JS) and the LLM providers (OpenAI, Anthropic, etc.). It integrates deeply with frameworks like LangChain, LlamaIndex, and the Vercel AI SDK.
*   **Project Setup**:
    1.  **Account**: Sign up at [cloud.langfuse.com](https://cloud.langfuse.com) or self-host via Docker.
    2.  **API Keys**: Generate `Public Key`, `Secret Key`, and `Host` in project settings.
    3.  **Environment Variables**:
        ```bash
        LANGFUSE_PUBLIC_KEY="pk-lf-..."
        LANGFUSE_SECRET_KEY="sk-lf-..."
        LANGFUSE_BASE_URL="https://cloud.langfuse.com"
        ```
    4.  **Installation**:
        *   Python: `pip install langfuse`
        *   JS/TS: `npm install @langfuse/openai` (or `@langfuse/tracing @langfuse/otel @opentelemetry/sdk-node` for full tracing)

## 2. Core Primitives & APIs

*   **Traces & Spans**: The top-level container for a single request or execution. Spans represent nested units of work.
    *   [Python Context Manager](https://langfuse.com/docs/sdk/python/sdk-v3#context-manager): `with langfuse.start_as_current_observation(name="my-span") as span:`
*   **Generations**: Specialized spans for LLM calls, capturing prompts, completions, model parameters, and token usage.
    *   [OpenAI Wrapper (Python)](https://langfuse.com/docs/integrations/model-providers/openai-py): `from langfuse.openai import openai` (drop-in replacement).
*   **Prompt Management**: Centrally manage and version prompts.
    *   [Prompt Fetching](https://langfuse.com/docs/prompt-management/get-started): `prompt = langfuse.get_prompt("my-prompt")` and `compiled = prompt.compile(var="value")`.
*   **Scores**: Numerical or categorical evaluations attached to traces/observations (e.g., user feedback, LLM-as-a-judge).
    *   [Scores via SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk): `langfuse.score(trace_id=..., name="accuracy", value=0.9)`
*   **Datasets**: Collections of inputs and expected outputs for benchmarking.
    *   [Dataset API](https://langfuse.com/docs/evaluation/experiments/datasets): `langfuse.create_dataset_item(dataset_name="...", input=..., expected_output=...)`

## 3. Real-World Use Cases & Templates

*   **RAG Evaluation**: Using Langfuse to trace retrieval steps and LLM generations, then scoring them using RAGAS or custom LLM-as-a-judge evaluators. [RAG Cookbook](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge).
*   **Agent Observability**: Tracking complex multi-turn agentic workflows (e.g., LangGraph, CrewAI) to visualize tool usage and reasoning loops. [LangGraph Integration](https://langfuse.com/docs/integrations/frameworks/langchain).
*   **Prompt A/B Testing**: Deploying new prompt versions using "labels" (e.g., `production`, `staging`) and comparing performance metrics in the dashboard. [Prompt Versioning](https://langfuse.com/docs/prompt-management/features/prompt-version-control).

## 4. Developer Friction Points

*   **Async Context Loss**: In both Python and JS, maintaining trace context across async boundaries or multi-threaded executions can be tricky, leading to "orphaned" spans. [Troubleshooting Guide](https://langfuse.com/docs/observability/sdk/troubleshooting-and-faq).
*   **Missing `flush()`**: In short-lived scripts (e.g., Lambda, CLI tools), events are often lost because the process exits before the background exporter sends them. [FAQ on Background Processing](https://langfuse.com/docs/observability/data-model#background-processing).
*   **OpenTelemetry Complexity**: The JS/TS SDK relies on OpenTelemetry, which can conflict with existing OTEL setups or require complex configuration in Next.js/Serverless environments. [OTEL Middleware Issues](https://github.com/langfuse/langfuse/discussions/2544).

## 5. Evaluation Ideas

*   **Basic Tracing**: Instrument a simple OpenAI script and verify that traces appear with correct token counts and latency.
*   **Prompt Migration**: Move hardcoded prompts to Langfuse Prompt Management and implement dynamic fetching with caching.
*   **Custom Evaluator**: Create a Python script that fetches production traces via the SDK, runs a custom "toxicity" check, and pushes scores back to Langfuse.
*   **CI/CD Regression**: Set up a GitHub Action that runs a dataset evaluation on every PR and fails if the average "accuracy" score drops below a threshold.
*   **Agent Graph Trace**: Instrument a LangGraph agent with tool-use and ensure the UI correctly displays the graph structure and nested tool calls.
*   **Multi-Project Setup**: Configure an application to route traces to different Langfuse projects based on runtime metadata (e.g., tenant ID).

## 6. Sources

1.  [Langfuse llms.txt](https://langfuse.com/llms.txt) - Main entry point for LLM-friendly documentation.
2.  [Langfuse Docs Overview](https://langfuse.com/docs) - Core concepts and getting started guides.
3.  [Langfuse Integrations List](https://langfuse.com/llms-integrations.txt) - Comprehensive list of supported frameworks and providers.
4.  [Langfuse GitHub Issues](https://github.com/langfuse/langfuse/issues) - Source for common bugs and friction points.
5.  [Langfuse Python SDK Docs](https://langfuse.com/docs/sdk/python/sdk-v3) - Technical details for Python instrumentation.
6.  [Langfuse Prompt Management Guide](https://langfuse.com/docs/prompt-management/get-started) - Details on centralized prompt versioning.
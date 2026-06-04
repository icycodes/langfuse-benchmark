# Langfuse — Research Plan

## 1. Library Overview

* **Description**: [Langfuse](https://langfuse.com/) is an open-source AI engineering platform that helps teams collaboratively debug, analyze, and iterate on LLM applications. It provides three natively integrated product surfaces: **Observability/Tracing** (OpenTelemetry-based), **Prompt Management** (versioned prompts with labels & deployment), and **Evaluation** (datasets, scores, experiments, LLM-as-a-judge).
* **Ecosystem Role**: Sits between an LLM application/agent and the observability/eval workflow. It ingests OTel spans from your app (or from 50+ integrations like OpenAI SDK, LangChain, LlamaIndex, Vercel AI SDK) and exposes a UI, public REST API, SDKs (Python/JS-TS), an MCP server, and the [`langfuse-cli`](https://github.com/langfuse/langfuse-cli) for programmatic access.
* **Deployment Modes**: Langfuse Cloud (EU/US/JP/HIPAA regions) or self-hosted.

### Project Setup

#### a. Create credentials
1. Sign up at [https://cloud.langfuse.com](https://cloud.langfuse.com/) or self-host.
2. Create a project, then under **Project Settings → API Keys** issue a public/secret key pair.
3. Export them as environment variables:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"   # or your self-hosted URL
```

#### b. Install the Python SDK
```bash
pip install langfuse
```
Then in code:
```python
from langfuse import get_client
langfuse = get_client()  # reads env vars
```
Source: [Observability SDK Overview](https://langfuse.com/docs/observability/sdk/overview).

#### c. Install the TS/JS SDK (modular packages)
```bash
npm install @langfuse/tracing @langfuse/otel @langfuse/client @opentelemetry/sdk-node
```
Bootstrap OpenTelemetry once at process startup (inline or in an `instrumentation.ts` file):
```ts
// instrumentation.ts
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

const sdk = new NodeSDK({ spanProcessors: [new LangfuseSpanProcessor()] });
sdk.start();
```
Then `import "./instrumentation";` must be the **first** import in your entry file.
Source: [Get Started with Tracing](https://langfuse.com/docs/observability/get-started).

| Package | Purpose |
| --- | --- |
| `@langfuse/core` | Shared utilities/types |
| `@langfuse/client` | Client for prompts, datasets, scores, experiments |
| `@langfuse/tracing` | OTel-based `startObservation`, `startActiveObservation` |
| `@langfuse/otel` | `LangfuseSpanProcessor` exporter (Node ≥ 20) |
| `@langfuse/openai` | Auto-tracing wrapper around the OpenAI SDK |
| `@langfuse/langchain` | LangChain `CallbackHandler` |

#### d. Install the Langfuse CLI
The CLI wraps the entire public API. It reads the **same** env vars as the SDKs.
```bash
# One-off:
npx langfuse-cli api <resource> <action>

# Global:
npm i -g langfuse-cli
langfuse api <resource> <action>

# Discover everything:
langfuse api __schema
langfuse api traces --help
```
Source: [Langfuse CLI docs](https://langfuse.com/docs/api-and-data-platform/features/cli) and the [langfuse-cli GitHub repo](https://github.com/langfuse/langfuse-cli).

---

## 2. Core Primitives & APIs

The three concepts below are exposed across all three surfaces (TS/JS SDK, Python SDK, CLI). Per concept, exactly **one** primary-interface snippet is shown, with the official source linked immediately below it.

### 2.1 Telemetry / Tracing

Langfuse traces are OpenTelemetry traces. A *trace* contains nested *observations* (`span`, `generation`, `event`, tool-call, retrieval, …). The **primary interface** for custom tracing in the Python SDK is the `start_as_current_observation` context manager:

```python
from langfuse import get_client

langfuse = get_client()

# Create a span using a context manager
with langfuse.start_as_current_observation(as_type="span", name="process-request") as span:
    # Your processing logic here
    span.update(output="Processing complete")

    # Create a nested generation for an LLM call
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-response", model="gpt-3.5-turbo"
    ) as generation:
        # Your LLM call logic here
        generation.update(output="Generated response")

# Flush events in short-lived applications
langfuse.flush()
```
Source: [Get Started with Tracing — Python SDK](https://langfuse.com/docs/observability/get-started)

Equivalent surfaces:
* **TS/JS SDK**: `startActiveObservation` / `startObservation` from `@langfuse/tracing` (collected by `LangfuseSpanProcessor`).
* **CLI**: read-only access via `langfuse api traces list --limit 10`, `langfuse api traces get <trace-id>` — useful for verifying that a trace was actually delivered.

### 2.2 Prompt Management

Prompts in Langfuse are first-class versioned objects. They support text and chat formats, semantic version control via labels (`production`, `staging`, …), variables, and caching. The **primary runtime interface** is `prompt.get(...)` + `compile(...)`. From the TS/JS SDK:

```ts
import { LangfuseClient } from "@langfuse/client";

// Initialize the Langfuse client
const langfuse = new LangfuseClient();

// By default, the production version of a chat prompt is fetched.
const chatPrompt = await langfuse.prompt.get("movie-critic-chat", {
  type: "chat",
});

// Insert variables into chat prompt template
const compiledChatPrompt = chatPrompt.compile({
  criticlevel: "expert",
  movie: "Dune 2",
});
// -> [{"role": "system", "content": "You are an expert movie critic"},
//     {"role": "user",   "content": "Do you like Dune 2?"}]
```
Source: [Prompt Management — Get Started (JS/TS)](https://langfuse.com/docs/prompt-management/get-started)

Equivalent surfaces:
* **Python SDK**: `langfuse.get_prompt("movie-critic-chat", type="chat").compile(...)`.
* **CLI**: `langfuse api prompts list` / `langfuse api prompts get --name <name>` / `langfuse api prompts create ...` — the CLI dynamically wraps the OpenAPI spec so every prompt endpoint is available.

### 2.3 Evaluation (Datasets, Scores, Experiments)

Evaluation in Langfuse is built around three primitives:
* **Datasets** — versioned collections of `(input, expected_output, metadata)` items.
* **Scores** — numeric / boolean / categorical evaluations attached to traces, observations, sessions, or dataset runs.
* **Experiments** — programmatic runs of a *task function* over a dataset, with optional item-level and run-level *evaluators*.

The **primary interface** is `run_experiment` (Python) / `experiment.run` (JS) which couples all three:

```python
from langfuse import get_client, Evaluation
from langfuse.openai import OpenAI

langfuse = get_client()

# 1. Task: how a single dataset item is processed
def my_task(*, item, **kwargs):
    response = OpenAI().chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": item["input"]}],
    )
    return response.choices[0].message.content

# 2. Item-level evaluator -> emits a Score attached to each trace
def accuracy_evaluator(*, input, output, expected_output, **kwargs):
    correct = expected_output and expected_output.lower() in output.lower()
    return Evaluation(name="accuracy", value=1.0 if correct else 0.0)

# 3. Dataset (local list here; can also be a Langfuse-hosted dataset)
local_data = [
    {"input": "What is the capital of France?",  "expected_output": "Paris"},
    {"input": "What is the capital of Germany?", "expected_output": "Berlin"},
]

# 4. Experiment ties task + data + evaluators together
result = langfuse.run_experiment(
    name="Geography Quiz",
    description="Testing basic functionality",
    data=local_data,
    task=my_task,
    evaluators=[accuracy_evaluator],
)

print(result.format())
```
Source: [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)

Equivalent surfaces:
* **TS/JS SDK**: `langfuse.experiment.run({ name, data, task, evaluators })`, or `dataset.runExperiment(...)` when running against a Langfuse-hosted dataset.
* **CLI**: manage datasets, items, runs, and scores directly — e.g. `langfuse api datasets list`, `langfuse api dataset-items list --dataset-name my-dataset`, `langfuse api score-v2s get-scores --limit 20`.

---

## 3. Real-World Use Cases & Templates

* **OpenAI drop-in instrumentation** — `from langfuse.openai import openai` (Python) or `observeOpenAI(new OpenAI())` (JS) for zero-refactor tracing. [Docs](https://langfuse.com/integrations/model-providers/openai-py).
* **LangChain agents** — Initialize `CallbackHandler` from `langfuse.langchain` / `@langfuse/langchain` and pass it via `config={"callbacks": [handler]}`. [Docs](https://langfuse.com/integrations/frameworks/langchain).
* **Vercel AI SDK / Next.js** — Pair `LangfuseSpanProcessor` with `experimental_telemetry: { isEnabled: true }` for fully automatic tracing in serverless/edge runtimes. [Docs](https://langfuse.com/integrations/frameworks/vercel-ai-sdk).
* **Experiments in CI/CD** — Run `run_experiment` on a held-out dataset on each PR to catch regressions before merging. [Docs](https://langfuse.com/docs/evaluation/experiments/experiments-ci-cd).
* **Prompt promotion workflow** — Create prompt → test in Playground → label `staging` → run experiments → relabel `production`, all reproducible via the CLI for GitOps. [Docs](https://langfuse.com/docs/prompt-management/features/prompt-version-control).
* **Agent skills** — The [`langfuse/skills`](https://github.com/langfuse/skills) repo provides a turnkey skill that teaches coding agents (Cursor, Claude Code, etc.) how to instrument projects and drive the CLI.

---

## 4. Developer Friction Points

1. **OTel initialization order in JS/TS.** `LangfuseSpanProcessor` must be started *before* any module that emits spans is imported. Common with Next.js / bundlers where users put the SDK init at the bottom of the entry file and see "no traces" — Langfuse documents an `instrumentation.ts` pattern as the fix. ([Get Started](https://langfuse.com/docs/observability/get-started), [Missing traces FAQ](https://langfuse.com/faq/all/missing-traces)).
2. **Prompt caching staleness.** `prompt.get()` ships with TTL caching to keep latency low; users updating prompts in the UI sometimes don't see the new version immediately. Tuning `cache_ttl_seconds` or invalidating the cache is non-obvious. ([Prompt caching](https://langfuse.com/docs/prompt-management/data-model#prompt-caching)).
3. **Flushing in short-lived processes.** Scripts, serverless functions, and CI tasks must call `langfuse.flush()` (Python) or `await otelSdk.shutdown()` (JS) before exit or traces/scores are silently dropped. ([Background processing](https://langfuse.com/docs/observability/data-model#background-processing)).
4. **SDK v3 → v4 migration.** The legacy Python `item.run()` context-manager was removed in v4 in favor of `dataset.run_experiment()` with attribute propagation; users porting old experiment scripts hit subtle behavior changes. ([Python v3 → v4 migration](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4)).

---

## 5. Evaluation Ideas

1. Instrument an existing OpenAI-based script with the Python SDK so a parent trace plus a nested generation appear in Langfuse.
2. Add a Vercel-AI-SDK or Next.js project to Langfuse using `instrumentation.ts` and `LangfuseSpanProcessor`.
3. Create a versioned chat prompt with two labels (`staging`, `production`) and fetch the right version at runtime.
4. Attach custom numeric, boolean, and categorical scores to a trace via the SDK and verify them via the CLI.
5. Build a Langfuse-hosted dataset, upload items, and run `run_experiment` with an item-level accuracy evaluator.
6. Wire a CI step that runs an experiment on every PR and fails the build if the run-level evaluator drops below a threshold.
7. Use the CLI to script a prompt promotion workflow that copies the highest-scoring version into the `production` label.
8. Diagnose a "missing traces" scenario by adjusting OTel init order and ensuring `flush()` / `shutdown()` is called.

---

## 6. Sources

1. [Langfuse `llms.txt`](https://langfuse.com/llms.txt) — dense single-file index of the docs.
2. [Langfuse Docs Overview](https://langfuse.com/docs) — high-level product map (observability, prompts, eval).
3. [Observability SDK Overview](https://langfuse.com/docs/observability/sdk/overview) — SDK install matrix and OTel mapping.
4. [Get Started with Tracing](https://langfuse.com/docs/observability/get-started) — manual install paths for Python and JS/TS, OTel setup.
5. [Prompt Management — Get Started](https://langfuse.com/docs/prompt-management/get-started) — runtime fetch + `compile` snippets across SDKs.
6. [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) — `run_experiment` / `experiment.run` reference with evaluators.
7. [Scores via API/SDK](https://langfuse.com/docs/evaluation/evaluation-methods/custom-scores) — how to attach custom scores.
8. [Langfuse CLI docs](https://langfuse.com/docs/api-and-data-platform/features/cli) — CLI overview and configuration.
9. [langfuse-cli GitHub repo](https://github.com/langfuse/langfuse-cli) — install, env vars, usage commands.
10. [Langfuse Public API Reference](https://api.reference.langfuse.com/) — endpoints surfaced by the CLI.
11. [langfuse/skills repository](https://github.com/langfuse/skills) — official agent skill for instrumentation workflows.

---

## Integration

The following environment variables will be provided:
* LANGFUSE_PUBLIC_KEY
* LANGFUSE_PRIVATE_KEY
* LANGFUSE_BASE_URL

## Important notes for Task Generation

* Carefully write the final `pytest` test code. When using the Langfuse Platform API to verify task side effects, you must use `webFetch` to retrieve the API reference documentation, double-check that the endpoint actually exists, and ensure the request and response match the documentation.


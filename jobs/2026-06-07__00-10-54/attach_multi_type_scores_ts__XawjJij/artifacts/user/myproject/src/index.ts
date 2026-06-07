import { writeFile } from "node:fs/promises";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { startActiveObservation } from "@langfuse/tracing";
import { LangfuseClient } from "@langfuse/client";

const outputLogPath = "/home/user/myproject/output.log";

function requireEnv(name: string): string {
  const value = process.env[name];

  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value;
}

const runId = requireEnv("ZEALT_RUN_ID");
const traceName = `multi-score-demo-${runId}`;

const otelSdk = new NodeSDK({
  spanProcessors: [
    new LangfuseSpanProcessor({
      // Short-lived scripts should export spans immediately to avoid losing data
      // if the process exits soon after the trace ends.
      exportMode: "immediate",
    }),
  ],
});

const langfuse = new LangfuseClient();

async function main(): Promise<void> {
  otelSdk.start();

  const traceId = startActiveObservation(traceName, (trace) => {
    const generation = trace.startObservation(
      "llm-call",
      {
        input: [{ role: "user", content: "Say hello." }],
        output: { role: "assistant", content: "Hello!" },
        model: "demo-model",
      },
      { asType: "generation" },
    );

    generation.end();

    return trace.traceId;
  });

  langfuse.score.create({
    traceId,
    name: "correctness",
    dataType: "NUMERIC",
    value: 0.92,
  });

  langfuse.score.create({
    traceId,
    name: "sentiment",
    dataType: "CATEGORICAL",
    value: "positive",
  });

  langfuse.score.create({
    traceId,
    name: "helpfulness",
    dataType: "BOOLEAN",
    value: 1,
  });

  await langfuse.flush();
  await otelSdk.shutdown();

  await writeFile(outputLogPath, `Trace ID: ${traceId}\n`, "utf8");

  console.log(`Created Langfuse trace ${traceName}`);
  console.log(`Trace ID: ${traceId}`);
}

main().catch(async (error) => {
  console.error("Failed to create Langfuse trace and scores:", error);

  await Promise.allSettled([langfuse.flush(), otelSdk.shutdown()]);

  process.exitCode = 1;
});

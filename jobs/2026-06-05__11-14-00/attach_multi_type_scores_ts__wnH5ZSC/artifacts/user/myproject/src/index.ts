import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import {
  startObservation,
  getActiveTraceId,
} from "@langfuse/tracing";
import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is required");
  }

  const traceName = `multi-score-demo-${runId}`;

  // 1. Initialize the OTel SDK with LangfuseSpanProcessor
  const spanProcessor = new LangfuseSpanProcessor({
    exportMode: "immediate",
  });

  const otelSdk = new NodeSDK({
    spanProcessors: [spanProcessor],
  });

  otelSdk.start();

  // 2. Create a trace (root span)
  const traceSpan = startObservation(traceName);

  // 3. Create a nested generation observation named "llm-call"
  const generation = traceSpan.startObservation("llm-call", {}, { asType: "generation" });

  // End the generation
  generation.end();

  // Get the trace ID before ending the root span
  const traceId = traceSpan.traceId;

  // End the trace span
  traceSpan.end();

  // 4. Flush the OTel SDK to ensure spans are sent
  await otelSdk.shutdown();

  // 5. Create LangfuseClient and attach scores to the trace
  const langfuse = new LangfuseClient();

  // Score: correctness — NUMERIC — value 0.92
  langfuse.score.create({
    traceId,
    name: "correctness",
    value: 0.92,
    dataType: "NUMERIC",
  });

  // Score: sentiment — CATEGORICAL — value "positive"
  langfuse.score.create({
    traceId,
    name: "sentiment",
    value: "positive",
    dataType: "CATEGORICAL",
  });

  // Score: helpfulness — BOOLEAN — value 1
  langfuse.score.create({
    traceId,
    name: "helpfulness",
    value: 1,
    dataType: "BOOLEAN",
  });

  // 6. Flush the Langfuse client
  await langfuse.flush();

  // 7. Write trace ID to output.log
  const logPath = path.resolve("/home/user/myproject/output.log");
  fs.writeFileSync(logPath, `Trace ID: ${traceId}\n`);

  console.log(`Trace ID: ${traceId}`);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
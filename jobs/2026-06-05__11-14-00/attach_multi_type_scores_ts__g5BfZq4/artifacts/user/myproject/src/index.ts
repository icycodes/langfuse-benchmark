import * as fs from "fs";
import * as path from "path";

import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import {
  startActiveObservation,
  getActiveTraceId,
} from "@langfuse/tracing";
import { LangfuseClient } from "@langfuse/client";

async function main() {
  // Read the run ID from the environment
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const traceName = `multi-score-demo-${runId}`;

  // Initialise the OTel Node SDK with the Langfuse span processor BEFORE any traced code
  const otelSdk = new NodeSDK({
    spanProcessors: [new LangfuseSpanProcessor()],
  });
  otelSdk.start();

  // Initialise the Langfuse client (reads credentials from env automatically)
  const langfuse = new LangfuseClient();

  let traceId: string | undefined;

  // Create the trace-level span, then a nested generation inside it
  await startActiveObservation(traceName, async (traceSpan) => {
    // Capture the Langfuse trace ID while we are inside the active trace span
    traceId = getActiveTraceId();

    // Create the nested generation observation
    traceSpan.startObservation("llm-call", {}, { asType: "generation" }).end();
  });

  if (!traceId) {
    throw new Error("Failed to capture trace ID from active span");
  }

  console.log(`Trace created with ID: ${traceId}`);

  // Attach three scores to the trace
  langfuse.score.create({
    traceId,
    name: "correctness",
    value: 0.92,
    dataType: "NUMERIC",
  });

  langfuse.score.create({
    traceId,
    name: "sentiment",
    value: "positive",
    dataType: "CATEGORICAL",
  });

  langfuse.score.create({
    traceId,
    name: "helpfulness",
    value: 1,
    dataType: "BOOLEAN",
  });

  // Flush both the OTel SDK and the Langfuse client so all data is delivered
  await otelSdk.shutdown();
  await langfuse.flush();

  // Write the trace ID to the log file
  const logPath = path.join("/home/user/myproject", "output.log");
  fs.writeFileSync(logPath, `Trace ID: ${traceId}\n`, "utf-8");
  console.log(`Trace ID written to ${logPath}`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});

import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { startActiveObservation, getActiveTraceId } from "@langfuse/tracing";
import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";

async function main() {
  console.log("Starting script...");
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is required");
  }
  console.log("Run ID:", runId);

  const otelSdk = new NodeSDK({
    spanProcessors: [new LangfuseSpanProcessor()],
  });
  otelSdk.start();
  console.log("OTel started");

  const langfuse = new LangfuseClient();

  const traceName = `multi-score-demo-${runId}`;
  let traceId: string = "";

  console.log("Starting observation...");
  await startActiveObservation(traceName, async (traceSpan) => {
    traceId = getActiveTraceId() || "";
    console.log("Trace ID inside callback:", traceId);

    await startActiveObservation("llm-call", async (genSpan) => {
      console.log("Inside nested generation");
    }, { asType: "generation" });
  });

  console.log("Observation done, traceId:", traceId);

  if (!traceId) {
    throw new Error("Failed to get traceId");
  }

  console.log("Attaching scores...");
  await langfuse.score.create({
    traceId,
    name: "correctness",
    value: 0.92,
    dataType: "NUMERIC"
  });

  await langfuse.score.create({
    traceId,
    name: "sentiment",
    value: "positive",
    dataType: "CATEGORICAL"
  });

  await langfuse.score.create({
    traceId,
    name: "helpfulness",
    value: 1,
    dataType: "BOOLEAN"
  });

  console.log("Flushing langfuse...");
  await langfuse.flush();
  console.log("Shutting down OTel...");
  await otelSdk.shutdown();

  console.log("Writing output log...");
  fs.writeFileSync("/home/user/myproject/output.log", `Trace ID: ${traceId}\n`);
  console.log("Done.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

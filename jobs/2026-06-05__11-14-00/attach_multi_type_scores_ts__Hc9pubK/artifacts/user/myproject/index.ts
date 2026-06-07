import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { LangfuseClient } from "@langfuse/client";
import * as opentelemetry from "@opentelemetry/api";
import * as fs from "fs";

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    console.error("ZEALT_RUN_ID environment variable is not set");
    process.exit(1);
  }

  // Initialize LangfuseSpanProcessor
  const langfuseSpanProcessor = new LangfuseSpanProcessor();

  // Initialize OpenTelemetry SDK
  const sdk = new NodeSDK({
    spanProcessor: langfuseSpanProcessor,
  });

  sdk.start();

  // Initialize Langfuse Client for scoring
  const langfuseClient = new LangfuseClient({
    publicKey: process.env.LANGFUSE_PUBLIC_KEY || "dummy",
    secretKey: process.env.LANGFUSE_SECRET_KEY || "dummy",
    baseUrl: process.env.LANGFUSE_BASE_URL || "https://cloud.langfuse.com",
  });

  const tracer = opentelemetry.trace.getTracer("multi-score-demo");

  try {
    // Create a trace (span)
    await tracer.startActiveSpan(`multi-score-demo-${runId}`, async (traceSpan) => {
      const traceId = traceSpan.spanContext().traceId;
      console.log(`Trace ID: ${traceId}`);

      // Create a nested generation observation
      // In Langfuse OTel, we use attributes to specify the type
      await tracer.startActiveSpan("llm-call", async (generationSpan) => {
        generationSpan.setAttribute("langfuse.type", "generation");
        
        // Simulate some LLM work
        generationSpan.setAttribute("gen_ai.system", "openai");
        generationSpan.setAttribute("gen_ai.request.model", "gpt-3.5-turbo");
        console.log("LLM call observation created");
        
        generationSpan.end();
      });

      // Attach scores to the trace
      console.log("Attaching scores...");
      await Promise.all([
        langfuseClient.score.create({
          traceId: traceId,
          name: "correctness",
          value: 0.92,
          dataType: "NUMERIC",
        }),
        langfuseClient.score.create({
          traceId: traceId,
          name: "sentiment",
          value: "positive",
          dataType: "CATEGORICAL",
        }),
        langfuseClient.score.create({
          traceId: traceId,
          name: "helpfulness",
          value: 1,
          dataType: "BOOLEAN",
        }),
      ]);

      // Write trace ID to log file
      const logFilePath = "/home/user/myproject/output.log";
      fs.writeFileSync(logFilePath, `Trace ID: ${traceId}\n`);
      console.log(`Trace ID written to ${logFilePath}`);
      
      traceSpan.end();
    });
  } catch (error) {
    console.error("Error during execution:", error);
  } finally {
    // Flush and shutdown
    await langfuseClient.flush();
    await sdk.shutdown();
    console.log("SDK shutdown and Langfuse client flushed");
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});

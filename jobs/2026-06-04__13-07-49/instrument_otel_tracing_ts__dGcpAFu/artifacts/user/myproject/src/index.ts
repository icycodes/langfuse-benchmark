// OTel SDK must be initialized before any spans are created.
// We set up and start the SDK first, then use the Langfuse tracing API.

import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

// --- Step 1: Initialize and start the OTel SDK with LangfuseSpanProcessor ---
const spanProcessor = new LangfuseSpanProcessor({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL || process.env.LANGFUSE_BASEURL,
  exportMode: "immediate", // best for short-lived processes
});

const sdk = new NodeSDK({
  spanProcessors: [spanProcessor],
});

sdk.start();

// --- Step 2: Import tracing functions after SDK is started ---
import {
  startActiveObservation,
  startObservation,
  getActiveTraceId,
} from "@langfuse/tracing";

// --- Step 3: Read run-id from environment ---
const runId = process.env.ZEALT_RUN_ID || "default";

async function main() {
  let traceId: string | undefined;

  // Create the root observation (span) representing the user request
  await startActiveObservation(
    `weather-assistant-${runId}`,
    async (rootObservation) => {
      // Set input/output on the root observation
      rootObservation.update({
        input: { query: "What's the weather in Paris?" },
      });

      // Create a nested generation observation for the simulated LLM call
      const llmCall = rootObservation.startObservation(
        "llm-call",
        {
          model: "gpt-4o-simulated",
          input: {
            messages: [
              { role: "system", content: "You are a weather assistant." },
              { role: "user", content: "What's the weather in Paris?" },
            ],
          },
        },
        { asType: "generation" }
      );

      // Simulate LLM output
      llmCall.update({
        output: {
          role: "assistant",
          content: "The weather in Paris is currently sunny with a temperature of 22°C.",
        },
      });

      // End the generation observation
      llmCall.end();

      // Set output on the root observation
      rootObservation.update({
        output: {
          response: "The weather in Paris is currently sunny with a temperature of 22°C.",
        },
      });

      // Get the trace ID while inside the active observation context
      traceId = getActiveTraceId();

      // The root observation will be ended automatically by startActiveObservation
      // (endOnExit defaults to true)
    }
  );

  // --- Step 4: Flush spans before exiting ---
  await sdk.shutdown();

  // --- Step 5: Print trace ID to stdout and log file ---
  if (traceId) {
    const logLine = `Trace ID: ${traceId}\n`;
    console.log(logLine.trimEnd());
    const fs = await import("fs");
    const path = await import("path");
    const logPath = path.resolve(process.cwd(), "output.log");
    fs.writeFileSync(logPath, logLine);
  } else {
    console.error("Error: Could not retrieve trace ID");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Script failed:", err);
  process.exit(1);
});
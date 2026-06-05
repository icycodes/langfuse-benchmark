// IMPORTANT: OTel SDK must be initialized BEFORE importing any tracing modules
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

sdk.start();

// Now import tracing utilities (after SDK is started)
import {
  startActiveObservation,
  startObservation,
  getActiveTraceId,
} from "@langfuse/tracing";

import * as fs from "fs";
import * as path from "path";

const LOG_FILE = path.join(__dirname, "..", "output.log");

async function main() {
  const runId = process.env.ZEALT_RUN_ID ?? "default";
  const traceName = `weather-assistant-${runId}`;

  // Simulate user asking about weather
  const userInput = { role: "user", content: "What is the weather in Berlin?" };
  const simulatedOutput = {
    role: "assistant",
    content:
      "The weather in Berlin is currently 18°C with partly cloudy skies.",
  };

  await startActiveObservation(
    traceName,
    async (rootSpan) => {
      // Set input on the root (parent) observation
      rootSpan.update({ input: userInput });

      // Retrieve trace ID while inside the active observation context
      const traceId = getActiveTraceId();

      // Create the nested generation observation (LLM call simulation)
      const generation = rootSpan.startObservation(
        "llm-call",
        {
          input: [userInput],
          model: "gpt-4o-mini",
        },
        { asType: "generation" }
      );

      // Simulate LLM processing delay
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Update generation with model output
      generation.update({
        output: simulatedOutput,
        model: "gpt-4o-mini",
      });

      // End the generation span
      generation.end();

      // Set output on the root observation
      rootSpan.update({ output: simulatedOutput });

      // Log trace ID to stdout and to log file
      const traceIdLine = `Trace ID: ${traceId}`;
      console.log(traceIdLine);
      console.log(`Trace name: ${traceName}`);
      console.log(`Run ID: ${runId}`);

      fs.writeFileSync(LOG_FILE, traceIdLine + "\n", { flag: "w" });
    },
    { asType: "span" }
  );
}

main()
  .then(async () => {
    // Flush and shut down the OTel SDK so spans are exported before process exits
    await sdk.shutdown();
    console.log("SDK shutdown complete. Spans flushed.");
  })
  .catch(async (err) => {
    console.error("Error running weather assistant:", err);
    await sdk.shutdown();
    process.exit(1);
  });

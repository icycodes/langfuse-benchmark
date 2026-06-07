import { NodeSDK } from '@opentelemetry/sdk-node';
import { LangfuseSpanProcessor } from '@langfuse/otel';
import * as fs from 'fs';

// Initialize the OpenTelemetry Node SDK with the Langfuse Span Processor
const sdk = new NodeSDK({
  spanProcessor: new LangfuseSpanProcessor(),
});

sdk.start();

// Import Langfuse tracing after SDK start
import { startActiveObservation, startObservation, getActiveTraceId } from '@langfuse/tracing';

async function main() {
  const runId = process.env.ZEALT_RUN_ID || 'manual-run';
  const logFile = '/home/user/myproject/output.log';

  // Ensure log file directory exists and clear it
  fs.writeFileSync(logFile, '');

  await startActiveObservation(
    `weather-assistant-${runId}`,
    async (rootSpan) => {
      const traceId = getActiveTraceId();
      console.log(`Trace ID: ${traceId}`);
      fs.appendFileSync(logFile, `Trace ID: ${traceId}\n`);

      rootSpan.update({
        input: { userQuery: "What is the weather in London?" },
      });

      // Create a nested generation observation
      // startObservation takes: name, attributes, options
      const generation = startObservation("llm-call", {
        input: { 
          model: "gpt-3.5-turbo",
          messages: [{ role: "user", content: "What is the weather in London?" }]
        },
        model: "gpt-3.5-turbo",
      }, { asType: "generation" });

      // Simulate LLM response
      const simulatedOutput = "The weather in London is currently 18°C and partly cloudy.";
      
      // Update generation with output
      generation.update({
        output: { 
          completion: simulatedOutput,
        },
        usageDetails: { promptTokens: 10, completionTokens: 15, totalTokens: 25 }
      });
      generation.end();

      // Update root span with output
      rootSpan.update({
        output: { 
          finalAnswer: simulatedOutput 
        },
      });
    }
  );

  // Ensure spans are reliably flushed before the process exits
  await sdk.shutdown();
  console.log("SDK shutdown complete. Spans flushed.");
}

main().catch(async (err) => {
  console.error("Error in main:", err);
  try {
    await sdk.shutdown();
  } catch (shutdownErr) {
    console.error("Error during SDK shutdown:", shutdownErr);
  }
  process.exit(1);
});

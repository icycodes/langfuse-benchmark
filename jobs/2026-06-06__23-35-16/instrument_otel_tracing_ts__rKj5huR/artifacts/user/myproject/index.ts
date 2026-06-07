import { NodeSDK } from '@opentelemetry/sdk-node';
import { LangfuseSpanProcessor } from '@langfuse/otel';
import { startActiveObservation, startObservation, getActiveTraceId } from '@langfuse/tracing';
import * as fs from 'fs';
import * as path from 'path';

console.log("Starting SDK...");
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});
sdk.start();
console.log("SDK started.");

const runId = process.env.ZEALT_RUN_ID || 'default-run';

async function main() {
  console.log("Starting observation...");
  await startActiveObservation(
    `weather-assistant-${runId}`,
    async (span) => {
      console.log("Inside observation...");
      span.update({
        input: { query: 'What is the weather like today?' }
      });

      const traceId = getActiveTraceId();
      console.log("Trace ID is", traceId);
      
      const generation = startObservation(
        'llm-call',
        {
          input: { prompt: 'What is the weather like today?' },
          model: 'gpt-4',
        },
        {
          asType: 'generation'
        }
      );
      
      // simulate delay
      await new Promise((resolve) => setTimeout(resolve, 100));
      
      const output = 'The weather is sunny and 75°F.';
      
      generation.update({
        output: { result: output },
      });
      generation.end();
      
      span.update({
        output: { result: output },
      });
      
      const logLine = `Trace ID: ${traceId}\n`;
      console.log(`Trace ID: ${traceId}`);
      fs.writeFileSync(path.join(__dirname, 'output.log'), logLine);
    }
  );
  
  console.log("Shutting down SDK...");
  await sdk.shutdown();
  console.log("SDK shut down.");
}

main().catch(err => {
  console.error("Error:", err);
});

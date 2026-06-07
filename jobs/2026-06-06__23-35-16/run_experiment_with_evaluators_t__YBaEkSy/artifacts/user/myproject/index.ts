import { LangfuseClient } from '@langfuse/client';
import { LangfuseSpanProcessor } from '@langfuse/otel';
import { NodeSDK } from '@opentelemetry/sdk-node';
import * as fs from 'fs';

const ZEALT_RUN_ID = process.env.ZEALT_RUN_ID || 'test';
const experimentName = `harbor-experiment-${ZEALT_RUN_ID}`;

console.log('Starting SDK...');
// Initialize OpenTelemetry
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

sdk.start();
console.log('SDK started.');

const langfuse = new LangfuseClient();

async function main() {
  console.log('Running experiment...');
  const dataset = [
    { input: 'hello', expectedOutput: 'HELLO' },
    { input: 'world', expectedOutput: 'WORLD' },
    { input: 'foo', expectedOutput: 'BAR' }, // accuracy 0
  ];

  const result = await langfuse.experiment.run({
    name: experimentName,
    data: dataset,
    task: async (item: any) => {
      return item.input.toUpperCase();
    },
    evaluators: [
      async ({ output, expectedOutput }: any) => {
        return {
          name: 'accuracy',
          value: output === expectedOutput ? 1 : 0,
        };
      },
      async ({ output }: any) => {
        return {
          name: 'response_length',
          value: output.length,
        };
      },
    ],
  });

  console.log('Experiment completed. Writing log file...');
  // Write log file
  const logLines = [];
  logLines.push(`Experiment name: ${experimentName}`);
  
  for (const itemResult of result.itemResults) {
    logLines.push(`Trace ID: ${itemResult.traceId}`);
  }

  fs.writeFileSync('/home/user/myproject/output.log', logLines.join('\n') + '\n');
  console.log('Done writing log file.');
}

main()
  .then(() => {
    console.log('Shutting down SDK...');
    return sdk.shutdown();
  })
  .then(() => console.log('Shutdown complete.'))
  .catch((err) => {
    console.error(err);
    sdk.shutdown();
    process.exit(1);
  });

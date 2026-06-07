import { LangfuseClient } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { writeFileSync } from "fs";
import { join } from "path";

// 1. Initialize OpenTelemetry with LangfuseSpanProcessor BEFORE running the experiment
const spanProcessor = new LangfuseSpanProcessor({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL,
  exportMode: "immediate",
});

const otelSdk = new NodeSDK({
  spanProcessors: [spanProcessor],
});

otelSdk.start();

// 2. Create Langfuse client
const langfuse = new LangfuseClient({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL,
});

// 3. Define local dataset of exactly 3 items
const dataset = [
  { input: "hello", expectedOutput: "HELLO" },
  { input: "world", expectedOutput: "WORLD" },
  { input: "langfuse", expectedOutput: "LANGFUSE" },
];

// 4. Define task function: returns uppercase of input
const task = async ({ input }: { input: string }) => {
  return input.toUpperCase();
};

// 5. Define item-level evaluators
const accuracyEvaluator = async ({
  output,
  expectedOutput,
}: {
  output: string;
  expectedOutput: string;
}) => {
  return {
    name: "accuracy" as const,
    value: output === expectedOutput ? 1 : 0,
  };
};

const responseLengthEvaluator = async ({ output }: { output: string }) => {
  return {
    name: "response_length" as const,
    value: output.length,
  };
};

// 6. Run the experiment
const experimentName = `harbor-experiment-${process.env.ZEALT_RUN_ID}`;

async function main() {
  const result = await langfuse.experiment.run({
    name: experimentName,
    data: dataset,
    task,
    evaluators: [accuracyEvaluator, responseLengthEvaluator],
  });

  // 7. Flush Langfuse client
  await langfuse.flush();

  // 8. Shutdown OTel SDK to ensure all spans are delivered
  await otelSdk.shutdown();

  // 9. Write the log file
  const lines: string[] = [];
  lines.push(`Experiment name: ${experimentName}`);

  for (const itemResult of result.itemResults) {
    lines.push(`Trace ID: ${itemResult.traceId}`);
  }

  const logContent = lines.join("\n");
  writeFileSync(join("/home/user/myproject", "output.log"), logContent);

  console.log("Experiment completed successfully!");
  console.log(logContent);
}

main().catch(async (err) => {
  console.error("Experiment failed:", err);
  await langfuse.flush();
  await otelSdk.shutdown();
  process.exit(1);
});
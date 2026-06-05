import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  // Read environment variables
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const experimentName = `harbor-experiment-${runId}`;

  // Initialize OpenTelemetry with LangfuseSpanProcessor BEFORE running the experiment
  const otelSdk = new NodeSDK({
    spanProcessors: [new LangfuseSpanProcessor()],
  });
  otelSdk.start();

  // Initialize Langfuse client
  // Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env automatically
  const langfuse = new LangfuseClient();

  // Define local dataset of exactly 3 items
  const dataset = [
    { input: "hello world", expectedOutput: "HELLO WORLD" },
    { input: "langfuse experiment", expectedOutput: "LANGFUSE EXPERIMENT" },
    { input: "typescript sdk", expectedOutput: "TYPESCRIPT SDK" },
  ];

  // Run the experiment
  const result = await langfuse.experiment.run({
    name: experimentName,
    data: dataset,

    // Task function: returns uppercase form of input (no external LLM calls)
    task: async ({ input }) => {
      return input.toUpperCase();
    },

    // Two item-level evaluators
    evaluators: [
      // accuracy: 1 when output exactly equals expectedOutput, 0 otherwise
      async ({ output, expectedOutput }) => ({
        name: "accuracy",
        value: output === expectedOutput ? 1 : 0,
      }),

      // response_length: number of characters in the output
      async ({ output }) => ({
        name: "response_length",
        value: typeof output === "string" ? output.length : 0,
      }),
    ],
  });

  // Flush all spans to Langfuse by shutting down the OTel SDK
  await otelSdk.shutdown();

  // Write the output log file
  const logLines: string[] = [];
  logLines.push(`Experiment name: ${experimentName}`);

  for (const itemResult of result.itemResults) {
    const traceId = itemResult.traceId ?? "";
    logLines.push(`Trace ID: ${traceId}`);
  }

  const logContent = logLines.join("\n") + "\n";
  const logPath = path.join(__dirname, "..", "output.log");
  fs.writeFileSync(logPath, logContent, "utf8");

  console.log("Experiment complete!");
  console.log(logContent);
}

main().catch((err) => {
  console.error("Error running experiment:", err);
  process.exit(1);
});

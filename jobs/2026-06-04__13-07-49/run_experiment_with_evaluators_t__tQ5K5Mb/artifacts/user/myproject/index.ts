import { LangfuseClient } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import * as fs from "fs";

async function main() {
  const ZEALT_RUN_ID = process.env.ZEALT_RUN_ID || "default-run-id";
  const experimentName = `harbor-experiment-${ZEALT_RUN_ID}`;

  // Initialize OpenTelemetry
  const langfuseSpanProcessor = new LangfuseSpanProcessor();
  const sdk = new NodeSDK({
    spanProcessor: langfuseSpanProcessor,
  });

  sdk.start();

  const langfuse = new LangfuseClient();

  const dataset = [
    { input: "hello", expectedOutput: "HELLO" },
    { input: "world", expectedOutput: "WORLD" },
    { input: "langfuse", expectedOutput: "LANGFUSE" },
  ];

  try {
    const result = await langfuse.experiment.run({
      name: experimentName,
      data: dataset,
      task: async (item: any) => {
        return item.input.toUpperCase();
      },
      evaluators: [
        async (params: any) => ({
          name: "accuracy",
          value: params.output === params.expectedOutput ? 1 : 0,
        }),
        async (params: any) => ({
          name: "response_length",
          value: params.output.length,
        }),
      ],
    });

    // Ensure all spans are delivered
    await sdk.shutdown();
    await langfuse.shutdown(); // Use shutdown instead of flush

    // Write log file
    const logLines = [
      `Experiment name: ${experimentName}`,
      ...result.itemResults.map((res: any) => `Trace ID: ${res.traceId}`),
    ];

    fs.writeFileSync("/home/user/myproject/output.log", logLines.join("\n") + "\n");
    console.log("Experiment completed and log file written.");
  } catch (error) {
    console.error("Experiment failed:", error);
    process.exit(1);
  }
}

main();

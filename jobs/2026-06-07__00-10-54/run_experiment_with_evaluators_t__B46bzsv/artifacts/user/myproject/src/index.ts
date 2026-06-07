import { writeFile } from "node:fs/promises";

import { LangfuseClient, type ExperimentItem } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

const otelSdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

// The Langfuse OpenTelemetry span processor must be registered before the
// experiment starts so every experiment item execution is exported as a trace.
otelSdk.start();

const langfuse = new LangfuseClient();

type LocalExperimentItem = ExperimentItem<string, string>;

const data: LocalExperimentItem[] = [
  { input: "harbor", expectedOutput: "HARBOR" },
  { input: "signal", expectedOutput: "SIGNAL" },
  { input: "anchor", expectedOutput: "ANCHOR" },
];

async function main() {
  const runId = process.env.ZEALT_RUN_ID;

  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is required");
  }

  const experimentName = `harbor-experiment-${runId}`;

  const result = await langfuse.experiment.run<string, string>({
    name: experimentName,
    data,
    maxConcurrency: 1,
    task: async ({ input }) => {
      if (typeof input !== "string") {
        throw new Error("Experiment item input must be a string");
      }

      return input.toUpperCase();
    },
    evaluators: [
      async ({ output, expectedOutput }) => ({
        name: "accuracy",
        value: output === expectedOutput ? 1 : 0,
      }),
      async ({ output }) => ({
        name: "response_length",
        value: String(output).length,
      }),
    ],
  });

  const traceIds = result.itemResults.map((itemResult, index) => {
    if (!itemResult.traceId) {
      throw new Error(`Missing trace ID for item at index ${index}`);
    }

    return itemResult.traceId;
  });

  // Flush Langfuse score events and then shut down OpenTelemetry to export all
  // item traces before writing the run summary requested by the task.
  await langfuse.shutdown();
  await otelSdk.shutdown();

  const logLines = [
    `Experiment name: ${experimentName}`,
    ...traceIds.map((traceId) => `Trace ID: ${traceId}`),
  ];

  await writeFile("output.log", `${logLines.join("\n")}\n`, "utf8");
}

main().catch(async (error: unknown) => {
  try {
    await langfuse.shutdown();
  } catch (shutdownError) {
    console.error("Failed to shut down Langfuse client", shutdownError);
  }

  try {
    await otelSdk.shutdown();
  } catch (shutdownError) {
    console.error("Failed to shut down OpenTelemetry SDK", shutdownError);
  }

  console.error(error);
  process.exitCode = 1;
});

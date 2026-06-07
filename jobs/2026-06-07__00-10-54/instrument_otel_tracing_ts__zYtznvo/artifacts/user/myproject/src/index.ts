import { appendFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

if (process.env.LANGFUSE_BASEURL && !process.env.LANGFUSE_BASE_URL) {
  process.env.LANGFUSE_BASE_URL = process.env.LANGFUSE_BASEURL;
}

const sdk = new NodeSDK({
  spanProcessors: [
    new LangfuseSpanProcessor({
      exportMode: "immediate",
    }),
  ],
});

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const outputLogPath = join(__dirname, "..", "output.log");

const runId = process.env.ZEALT_RUN_ID?.trim() || "local-run";
const traceAndRootName = `weather-assistant-${runId}`;

const userInput = {
  role: "user",
  content: "What is the weather in Berlin today?",
  location: "Berlin",
  units: "celsius",
  runId,
};

const simulatedLlmInput = [
  {
    role: "system",
    content:
      "You are a concise weather assistant. Use the supplied simulated weather data and do not call external tools.",
  },
  userInput,
];

const simulatedWeather = {
  location: "Berlin",
  temperatureCelsius: 18,
  condition: "partly cloudy",
  windKph: 11,
};

const simulatedLlmOutput = {
  role: "assistant",
  content:
    "It is currently 18°C and partly cloudy in Berlin, with light wind around 11 km/h.",
  weather: simulatedWeather,
};

async function main() {
  await writeFile(outputLogPath, "", "utf8");

  sdk.start();

  try {
    const {
      getActiveTraceId,
      startActiveObservation,
      startObservation,
      updateActiveTrace,
    } = await import("@langfuse/tracing");

    const traceId = await startActiveObservation(
      traceAndRootName,
      async (rootSpan) => {
        rootSpan.update({
          input: userInput,
          metadata: {
            runId,
            requestType: "weather-question",
          },
        });

        updateActiveTrace({
          name: traceAndRootName,
          input: userInput,
          output: simulatedLlmOutput,
          metadata: {
            runId,
            script: "weather-assistant",
          },
          tags: ["weather-assistant", `run-id:${runId}`],
        });

        const activeTraceId = getActiveTraceId() ?? rootSpan.traceId;

        const generation = startObservation(
          "llm-call",
          {
            input: simulatedLlmInput,
            model: "simulated-weather-llm-v1",
            modelParameters: {
              temperature: 0.2,
              maxTokens: 128,
            },
            metadata: {
              runId,
              simulated: true,
            },
          },
          {
            asType: "generation",
            parentSpanContext: rootSpan.otelSpan.spanContext(),
          },
        );

        generation.update({
          output: simulatedLlmOutput,
          usageDetails: {
            input: 54,
            output: 22,
            total: 76,
          },
        });
        generation.end();

        rootSpan.update({
          output: {
            answer: simulatedLlmOutput.content,
            traceId: activeTraceId,
            runId,
          },
          metadata: {
            runId,
            completed: true,
          },
        });

        return activeTraceId;
      },
      {
        asType: "span",
      },
    );

    const traceLine = `Trace ID: ${traceId}`;
    console.log(traceLine);
    await appendFile(outputLogPath, `${traceLine}\n`, "utf8");
  } finally {
    await sdk.shutdown();
  }
}

main().catch(async (error: unknown) => {
  const message = error instanceof Error ? error.stack || error.message : String(error);
  await appendFile(outputLogPath, `Error: ${message}\n`, "utf8").catch(() => undefined);
  console.error(message);
  process.exitCode = 1;
});

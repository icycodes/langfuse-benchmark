const { NodeSDK } = require("@opentelemetry/sdk-node");
const { LangfuseSpanProcessor } = require("@langfuse/otel");
const {
  startActiveObservation,
  getActiveTraceId,
  setActiveTraceAsPublic,
  setActiveTraceIO,
  propagateAttributes,
  LangfuseOtelSpanAttributes,
} = require("@langfuse/tracing");
const fs = require("fs");
const path = require("path");

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  console.error("ZEALT_RUN_ID environment variable is not set");
  process.exit(1);
}

const traceName = `release-test-${runId}`;
const sessionId = `session-${runId}`;
const userId = `user-${runId}`;
const tags = [`staging`, `run-${runId}`];
const release = "v1.2.3";
const version = "v1.0.0";

// Initialize OpenTelemetry SDK with LangfuseSpanProcessor
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

sdk.start();

async function main() {
  try {
    // Use propagateAttributes to set trace-level attributes and then
    // use startActiveObservation inside the propagated context
    const result = propagateAttributes(
      {
        traceName,
        userId,
        sessionId,
        version,
        tags,
      },
      () => {
        return startActiveObservation(
          traceName,
          (observation) => {
            // Set release on the active span
            const activeSpan =
              require("@opentelemetry/api").trace.getActiveSpan();
            if (activeSpan) {
              activeSpan.setAttribute(
                LangfuseOtelSpanAttributes.RELEASE,
                release
              );
            }

            // Set public visibility
            setActiveTraceAsPublic();

            // Set input/output
            setActiveTraceIO({
              input: { prompt: "hello-world" },
              output: { response: "greeting-complete" },
            });

            // Get the trace ID
            const traceId = getActiveTraceId();

            // Write trace ID to log file
            const logPath = path.join(__dirname, "output.log");
            fs.appendFileSync(logPath, `Trace ID: ${traceId}\n`);

            console.log(`Trace ID: ${traceId}`);
          },
          { asType: "span" }
        );
      }
    );

    return result;
  } finally {
    // Shutdown the OTel SDK to flush pending spans
    await sdk.shutdown();
  }
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
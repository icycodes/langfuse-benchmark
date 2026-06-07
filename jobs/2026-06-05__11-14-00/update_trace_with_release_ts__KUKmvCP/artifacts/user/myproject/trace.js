"use strict";

const { NodeSDK } = require("@opentelemetry/sdk-node");
const { LangfuseSpanProcessor } = require("@langfuse/otel");
const {
  startActiveObservation,
  getActiveTraceId,
  LangfuseOtelSpanAttributes,
} = require("@langfuse/tracing");
const fs = require("fs");
const path = require("path");

async function main() {
  const runId = process.env.ZEALT_RUN_ID || "default";
  const logFile = path.join(__dirname, "output.log");

  // Initialize OTel SDK with LangfuseSpanProcessor BEFORE any traced code runs
  const sdk = new NodeSDK({
    spanProcessors: [new LangfuseSpanProcessor()],
  });
  sdk.start();

  try {
    await startActiveObservation(`release-test-${runId}`, async (obs) => {
      // obs.otelSpan is the underlying OTel span — use it to set all trace-level attributes
      const span = obs.otelSpan;

      span.setAttributes({
        // Trace-level fields
        [LangfuseOtelSpanAttributes.TRACE_NAME]: `release-test-${runId}`,
        [LangfuseOtelSpanAttributes.TRACE_USER_ID]: `user-${runId}`,
        [LangfuseOtelSpanAttributes.TRACE_SESSION_ID]: `session-${runId}`,
        [LangfuseOtelSpanAttributes.TRACE_COMPAT_USER_ID]: `user-${runId}`,
        [LangfuseOtelSpanAttributes.TRACE_COMPAT_SESSION_ID]: `session-${runId}`,
        [LangfuseOtelSpanAttributes.TRACE_TAGS]: JSON.stringify([
          "staging",
          `run-${runId}`,
        ]),
        [LangfuseOtelSpanAttributes.RELEASE]: "v1.2.3",
        [LangfuseOtelSpanAttributes.VERSION]: "v1.0.0",
        [LangfuseOtelSpanAttributes.TRACE_PUBLIC]: true,
        [LangfuseOtelSpanAttributes.TRACE_INPUT]: JSON.stringify({
          prompt: "What is the capital of France?",
        }),
        [LangfuseOtelSpanAttributes.TRACE_OUTPUT]: JSON.stringify({
          answer: "The capital of France is Paris.",
        }),
        // Mark this as the root/app-root span so Langfuse treats it as the trace root
        [LangfuseOtelSpanAttributes.AS_ROOT]: true,
        [LangfuseOtelSpanAttributes.IS_APP_ROOT]: true,
      });

      // Retrieve the active OTel trace ID — this is the Langfuse trace ID
      const traceId = getActiveTraceId();
      console.log(`Trace ID: ${traceId}`);

      // Write trace ID to log file
      fs.appendFileSync(logFile, `Trace ID: ${traceId}\n`, "utf8");
    });
  } finally {
    // Shut down the OTel SDK to flush and deliver the span before the process exits
    await sdk.shutdown();
  }
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});

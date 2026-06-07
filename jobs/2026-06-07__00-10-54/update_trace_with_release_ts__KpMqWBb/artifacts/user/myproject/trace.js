const fs = require("node:fs/promises");
const path = require("node:path");
const { trace } = require("@opentelemetry/api");
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { LangfuseSpanProcessor } = require("@langfuse/otel");
const {
  LangfuseOtelSpanAttributes,
  createTraceAttributes,
  propagateAttributes,
  setActiveTraceAsPublic,
  startActiveObservation,
} = require("@langfuse/tracing");

const runId = process.env.ZEALT_RUN_ID;
if (!runId) {
  throw new Error("ZEALT_RUN_ID environment variable is required");
}

const traceName = `release-test-${runId}`;
const sessionId = `session-${runId}`;
const userId = `user-${runId}`;
const tags = ["staging", `run-${runId}`];
const release = "v1.2.3";
const version = "v1.0.0";
const logFile = path.join(__dirname, "output.log");

const sdk = new NodeSDK({
  spanProcessors: [
    new LangfuseSpanProcessor({
      release,
      exportMode: "immediate",
    }),
  ],
});

function updateActiveTrace(attributes) {
  const activeSpan = trace.getActiveSpan();
  if (!activeSpan) {
    throw new Error("No active OpenTelemetry span is available");
  }

  const otelAttributes = {
    [LangfuseOtelSpanAttributes.TRACE_NAME]: attributes.name,
    [LangfuseOtelSpanAttributes.TRACE_SESSION_ID]: attributes.sessionId,
    [LangfuseOtelSpanAttributes.TRACE_USER_ID]: attributes.userId,
    [LangfuseOtelSpanAttributes.TRACE_TAGS]: attributes.tags,
    [LangfuseOtelSpanAttributes.RELEASE]: attributes.release,
    [LangfuseOtelSpanAttributes.VERSION]: attributes.version,
    [LangfuseOtelSpanAttributes.TRACE_PUBLIC]: attributes.public,
    ...createTraceAttributes({ input: attributes.input, output: attributes.output }),
  };

  activeSpan.setAttributes(
    Object.fromEntries(Object.entries(otelAttributes).filter(([, value]) => value !== undefined))
  );
}

async function main() {
  sdk.start();

  try {
    const traceId = await startActiveObservation(traceName, async () => {
      return propagateAttributes(
        {
          traceName,
          sessionId,
          userId,
          tags,
          version,
        },
        async () => {
          const activeSpan = trace.getActiveSpan();
          if (!activeSpan) {
            throw new Error("No active OpenTelemetry span found inside Langfuse observation");
          }

          const currentTraceId = activeSpan.spanContext().traceId;
          if (!/^[0-9a-f]{32}$/.test(currentTraceId)) {
            throw new Error(`Unexpected trace ID format: ${currentTraceId}`);
          }

          updateActiveTrace({
            name: traceName,
            sessionId,
            userId,
            tags,
            release,
            version,
            public: true,
            input: {
              runId,
              prompt: "Tag a Langfuse trace with release, session, user, and tags",
            },
            output: {
              status: "trace-created",
              runId,
            },
          });
          setActiveTraceAsPublic();

          await fs.appendFile(logFile, `Trace ID: ${currentTraceId}\n`, "utf8");
          return currentTraceId;
        }
      );
    });

    console.log(`Trace ID: ${traceId}`);
  } finally {
    await sdk.shutdown();
  }
}

main().catch(async (error) => {
  console.error(error);
  try {
    await sdk.shutdown();
  } catch (_) {
    // Ignore shutdown errors while reporting the original failure.
  }
  process.exitCode = 1;
});

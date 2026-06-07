import { NodeSDK } from '@opentelemetry/sdk-node';
import { LangfuseSpanProcessor } from '@langfuse/otel';
import { startActiveObservation, LangfuseOtelSpanAttributes } from '@langfuse/tracing';
import { trace } from '@opentelemetry/api';
import * as fs from 'fs';

const runId = process.env.ZEALT_RUN_ID || 'default-run-id';

function updateActiveTrace(attributes: any) {
  const span = trace.getActiveSpan();
  if (!span) return;
  if (attributes.name) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_NAME, attributes.name);
  if (attributes.sessionId) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_SESSION_ID, attributes.sessionId);
  if (attributes.userId) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_USER_ID, attributes.userId);
  if (attributes.tags) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_TAGS, attributes.tags);
  if (attributes.release) span.setAttribute(LangfuseOtelSpanAttributes.RELEASE, attributes.release);
  if (attributes.version) span.setAttribute(LangfuseOtelSpanAttributes.VERSION, attributes.version);
  if (attributes.public !== undefined) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_PUBLIC, attributes.public);
  if (attributes.input) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_INPUT, JSON.stringify(attributes.input));
  if (attributes.output) span.setAttribute(LangfuseOtelSpanAttributes.TRACE_OUTPUT, JSON.stringify(attributes.output));
}

async function main() {
  const langfuseProcessor = new LangfuseSpanProcessor();
  const sdk = new NodeSDK({
    spanProcessors: [langfuseProcessor],
  });

  sdk.start();

  try {
    await startActiveObservation(`release-test-${runId}`, async () => {
      updateActiveTrace({
        name: `release-test-${runId}`,
        sessionId: `session-${runId}`,
        userId: `user-${runId}`,
        tags: ['staging', `run-${runId}`],
        release: 'v1.2.3',
        version: 'v1.0.0',
        public: true,
        input: { key: 'input-value' },
        output: { key: 'output-value' },
      });

      const activeSpan = trace.getActiveSpan();
      if (activeSpan) {
        const traceId = activeSpan.spanContext().traceId;
        fs.appendFileSync('/home/user/myproject/output.log', `Trace ID: ${traceId}\n`);
        console.log(`Trace ID: ${traceId}`);
      }
    });
  } finally {
    await sdk.shutdown();
  }
}

main().catch(console.error);

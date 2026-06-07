import { NodeSDK } from '@opentelemetry/sdk-node';
import { LangfuseSpanProcessor } from '@langfuse/otel';
import { trace } from '@opentelemetry/api';
import * as fs from 'fs';
import * as path from 'path';

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    console.error('ZEALT_RUN_ID environment variable is not set');
    process.exit(1);
  }

  const sdk = new NodeSDK({
    spanProcessor: new LangfuseSpanProcessor({
      exportMode: 'immediate',
    }),
  });

  sdk.start();

  try {
    const tracer = trace.getTracer('langfuse-sdk');
    await tracer.startActiveSpan(`release-test-${runId}`, async (span) => {
      span.setAttribute('langfuse.trace.name', `release-test-${runId}`);
      span.setAttribute('langfuse.session.id', `session-${runId}`);
      span.setAttribute('langfuse.user.id', `user-${runId}`);
      span.setAttribute('langfuse.trace.tags', JSON.stringify(['staging', `run-${runId}`]));
      span.setAttribute('langfuse.release', 'v1.2.3');
      span.setAttribute('langfuse.version', 'v1.0.0');
      span.setAttribute('langfuse.trace.public', 'true');
      span.setAttribute('langfuse.trace.input', JSON.stringify({ message: 'Hello Langfuse', runId }));
      span.setAttribute('langfuse.trace.output', JSON.stringify({ message: 'Success', status: 200 }));

      const traceId = span.spanContext().traceId;
      if (traceId) {
        const logPath = path.join('/home/user/myproject', 'output.log');
        fs.appendFileSync(logPath, `Trace ID: ${traceId}\n`);
      }
      
      span.end();
    });
  } catch (error) {
    console.error('Error during trace execution:', error);
  } finally {
    await sdk.shutdown();
  }
}

main().catch(console.error);

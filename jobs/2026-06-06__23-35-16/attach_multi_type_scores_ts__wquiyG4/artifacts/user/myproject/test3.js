const { startActiveObservation, getActiveTraceId } = require('@langfuse/tracing');
const { NodeSDK } = require('@opentelemetry/sdk-node');

const sdk = new NodeSDK();
sdk.start();

async function main() {
    startActiveObservation("my-trace", (span) => {
        console.log("Trace ID:", getActiveTraceId());
        console.log("Span traceId:", span.traceId);
        
        startActiveObservation("llm-call", (genSpan) => {
            console.log("Gen Span traceId:", genSpan.traceId);
        }, { asType: "generation" });
    });
}
main().then(() => sdk.shutdown());

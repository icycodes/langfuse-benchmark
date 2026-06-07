"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const sdk_node_1 = require("@opentelemetry/sdk-node");
const otel_1 = require("@langfuse/otel");
const tracing_1 = require("@langfuse/tracing");
const api_1 = require("@opentelemetry/api");
const fs = __importStar(require("fs"));
const runId = process.env.ZEALT_RUN_ID || 'default-run-id';
function updateActiveTrace(attributes) {
    const span = api_1.trace.getActiveSpan();
    if (!span)
        return;
    if (attributes.name)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_NAME, attributes.name);
    if (attributes.sessionId)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_SESSION_ID, attributes.sessionId);
    if (attributes.userId)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_USER_ID, attributes.userId);
    if (attributes.tags)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_TAGS, attributes.tags);
    if (attributes.release)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.RELEASE, attributes.release);
    if (attributes.version)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.VERSION, attributes.version);
    if (attributes.public !== undefined)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_PUBLIC, attributes.public);
    if (attributes.input)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_INPUT, JSON.stringify(attributes.input));
    if (attributes.output)
        span.setAttribute(tracing_1.LangfuseOtelSpanAttributes.TRACE_OUTPUT, JSON.stringify(attributes.output));
}
async function main() {
    const langfuseProcessor = new otel_1.LangfuseSpanProcessor();
    const sdk = new sdk_node_1.NodeSDK({
        spanProcessors: [langfuseProcessor],
    });
    sdk.start();
    try {
        await (0, tracing_1.startActiveObservation)(`release-test-${runId}`, async () => {
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
            const activeSpan = api_1.trace.getActiveSpan();
            if (activeSpan) {
                const traceId = activeSpan.spanContext().traceId;
                fs.appendFileSync('/home/user/myproject/output.log', `Trace ID: ${traceId}\n`);
                console.log(`Trace ID: ${traceId}`);
            }
        });
    }
    finally {
        await sdk.shutdown();
    }
}
main().catch(console.error);

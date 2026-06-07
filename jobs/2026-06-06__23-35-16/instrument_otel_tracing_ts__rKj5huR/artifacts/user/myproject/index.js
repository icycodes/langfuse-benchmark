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
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
console.log("Starting SDK...");
const sdk = new sdk_node_1.NodeSDK({
    spanProcessors: [new otel_1.LangfuseSpanProcessor()],
});
sdk.start();
console.log("SDK started.");
const runId = process.env.ZEALT_RUN_ID || 'default-run';
async function main() {
    console.log("Starting observation...");
    await (0, tracing_1.startActiveObservation)(`weather-assistant-${runId}`, async (span) => {
        console.log("Inside observation...");
        span.update({
            input: { query: 'What is the weather like today?' }
        });
        const traceId = (0, tracing_1.getActiveTraceId)();
        console.log("Trace ID is", traceId);
        const generation = (0, tracing_1.startObservation)('llm-call', {
            input: { prompt: 'What is the weather like today?' },
            model: 'gpt-4',
        }, {
            asType: 'generation'
        });
        // simulate delay
        await new Promise((resolve) => setTimeout(resolve, 100));
        const output = 'The weather is sunny and 75°F.';
        generation.update({
            output: { result: output },
        });
        generation.end();
        span.update({
            output: { result: output },
        });
        const logLine = `Trace ID: ${traceId}\n`;
        console.log(`Trace ID: ${traceId}`);
        fs.writeFileSync(path.join(__dirname, 'output.log'), logLine);
    });
    console.log("Shutting down SDK...");
    await sdk.shutdown();
    console.log("SDK shut down.");
}
main().catch(err => {
    console.error("Error:", err);
});

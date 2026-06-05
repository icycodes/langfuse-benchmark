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
// IMPORTANT: OTel SDK must be initialized BEFORE importing any tracing modules
const sdk_node_1 = require("@opentelemetry/sdk-node");
const otel_1 = require("@langfuse/otel");
const sdk = new sdk_node_1.NodeSDK({
    spanProcessors: [new otel_1.LangfuseSpanProcessor()],
});
sdk.start();
// Now import tracing utilities (after SDK is started)
const tracing_1 = require("@langfuse/tracing");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const LOG_FILE = path.join(__dirname, "..", "output.log");
async function main() {
    const runId = process.env.ZEALT_RUN_ID ?? "default";
    const traceName = `weather-assistant-${runId}`;
    // Simulate user asking about weather
    const userInput = { role: "user", content: "What is the weather in Berlin?" };
    const simulatedOutput = {
        role: "assistant",
        content: "The weather in Berlin is currently 18°C with partly cloudy skies.",
    };
    await (0, tracing_1.startActiveObservation)(traceName, async (rootSpan) => {
        // Set input on the root (parent) observation
        rootSpan.update({ input: userInput });
        // Retrieve trace ID while inside the active observation context
        const traceId = (0, tracing_1.getActiveTraceId)();
        // Create the nested generation observation (LLM call simulation)
        const generation = rootSpan.startObservation("llm-call", {
            input: [userInput],
            model: "gpt-4o-mini",
        }, { asType: "generation" });
        // Simulate LLM processing delay
        await new Promise((resolve) => setTimeout(resolve, 100));
        // Update generation with model output
        generation.update({
            output: simulatedOutput,
            model: "gpt-4o-mini",
        });
        // End the generation span
        generation.end();
        // Set output on the root observation
        rootSpan.update({ output: simulatedOutput });
        // Log trace ID to stdout and to log file
        const traceIdLine = `Trace ID: ${traceId}`;
        console.log(traceIdLine);
        console.log(`Trace name: ${traceName}`);
        console.log(`Run ID: ${runId}`);
        fs.writeFileSync(LOG_FILE, traceIdLine + "\n", { flag: "w" });
    }, { asType: "span" });
}
main()
    .then(async () => {
    // Flush and shut down the OTel SDK so spans are exported before process exits
    await sdk.shutdown();
    console.log("SDK shutdown complete. Spans flushed.");
})
    .catch(async (err) => {
    console.error("Error running weather assistant:", err);
    await sdk.shutdown();
    process.exit(1);
});

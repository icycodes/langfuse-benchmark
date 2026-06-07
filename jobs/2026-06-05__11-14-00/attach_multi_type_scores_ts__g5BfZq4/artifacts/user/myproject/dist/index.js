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
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const sdk_node_1 = require("@opentelemetry/sdk-node");
const otel_1 = require("@langfuse/otel");
const tracing_1 = require("@langfuse/tracing");
const client_1 = require("@langfuse/client");
async function main() {
    // Read the run ID from the environment
    const runId = process.env.ZEALT_RUN_ID;
    if (!runId) {
        throw new Error("ZEALT_RUN_ID environment variable is not set");
    }
    const traceName = `multi-score-demo-${runId}`;
    // Initialise the OTel Node SDK with the Langfuse span processor BEFORE any traced code
    const otelSdk = new sdk_node_1.NodeSDK({
        spanProcessors: [new otel_1.LangfuseSpanProcessor()],
    });
    otelSdk.start();
    // Initialise the Langfuse client (reads credentials from env automatically)
    const langfuse = new client_1.LangfuseClient();
    let traceId;
    // Create the trace-level span, then a nested generation inside it
    await (0, tracing_1.startActiveObservation)(traceName, async (traceSpan) => {
        // Capture the Langfuse trace ID while we are inside the active trace span
        traceId = (0, tracing_1.getActiveTraceId)();
        // Create the nested generation observation
        traceSpan.startObservation("llm-call", {}, { asType: "generation" }).end();
    });
    if (!traceId) {
        throw new Error("Failed to capture trace ID from active span");
    }
    console.log(`Trace created with ID: ${traceId}`);
    // Attach three scores to the trace
    langfuse.score.create({
        traceId,
        name: "correctness",
        value: 0.92,
        dataType: "NUMERIC",
    });
    langfuse.score.create({
        traceId,
        name: "sentiment",
        value: "positive",
        dataType: "CATEGORICAL",
    });
    langfuse.score.create({
        traceId,
        name: "helpfulness",
        value: 1,
        dataType: "BOOLEAN",
    });
    // Flush both the OTel SDK and the Langfuse client so all data is delivered
    await otelSdk.shutdown();
    await langfuse.flush();
    // Write the trace ID to the log file
    const logPath = path.join("/home/user/myproject", "output.log");
    fs.writeFileSync(logPath, `Trace ID: ${traceId}\n`, "utf-8");
    console.log(`Trace ID written to ${logPath}`);
}
main().catch((err) => {
    console.error("Fatal error:", err);
    process.exit(1);
});

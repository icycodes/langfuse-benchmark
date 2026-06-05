import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const promptName = `movie-critic-text-${runId}`;

  // Initialize the Langfuse client — it picks up LANGFUSE_PUBLIC_KEY,
  // LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL from the environment.
  const langfuse = new LangfuseClient();

  // ── Version 1: baseline template, labeled "staging" ──────────────────
  const v1 = await langfuse.prompt.create({
    name: promptName,
    type: "text",
    prompt:
      "You are a {{criticlevel}} movie critic. Please provide a thoughtful review of {{movie}}.",
    labels: ["staging"],
  });

  console.log(`Created prompt v${v1.version} with labels: staging`);

  // ── Version 2: improved template, labeled "production" ──────────────
  //  Passing labels: ["production"] will automatically move the "production"
  //  label off any older version, so v1 keeps only "staging".
  const v2 = await langfuse.prompt.create({
    name: promptName,
    type: "text",
    prompt:
      "You are an {{criticlevel}} movie critic. Write a detailed, insightful review of {{movie}} that covers plot, direction, and cinematography.",
    labels: ["production"],
  });

  console.log(`Created prompt v${v2.version} with labels: production`);

  // ── Fetch the production version and compile it ──────────────────────
  const productionPrompt = await langfuse.prompt.get(promptName, {
    label: "production",
    type: "text",
  });

  const compiled = productionPrompt.compile({
    criticlevel: "expert",
    movie: "Dune 2",
  });

  console.log(`Compiled prompt: ${compiled}`);

  // ── Write the log file ──────────────────────────────────────────────
  const logLines = [
    `Prompt name: ${promptName}`,
    `Staging version: ${v1.version}`,
    `Production version: ${v2.version}`,
    `Compiled prompt: ${compiled}`,
  ];

  const logPath = path.resolve(__dirname, "..", "output.log");
  fs.writeFileSync(logPath, logLines.join("\n") + "\n", "utf-8");
  console.log(`Log written to ${logPath}`);

  // Graceful shutdown
  await langfuse.shutdown();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  // Read the run ID from environment
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const promptName = `movie-critic-text-${runId}`;

  // Initialise the Langfuse client – picks up credentials from env vars:
  //   LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
  const langfuse = new LangfuseClient();

  console.log(`Creating prompt: ${promptName}`);

  // ── Version 1 ─ baseline template, labeled "staging" ─────────────────────
  const v1 = await langfuse.prompt.create({
    name: promptName,
    type: "text",
    prompt:
      "You are a {{criticlevel}} movie critic. " +
      "Write a short review (3-5 sentences) of the movie {{movie}}. " +
      "Focus on the plot, acting, and overall experience.",
    labels: ["staging"],
  });

  console.log(`Created version ${v1.version} with labels: ${v1.labels}`);

  // ── Version 2 – improved template, labeled "production" ──────────────────
  const v2 = await langfuse.prompt.create({
    name: promptName,
    type: "text",
    prompt:
      "You are a {{criticlevel}} movie critic with decades of experience. " +
      "Provide a detailed critique of the movie {{movie}}, covering: " +
      "1) Narrative and plot structure, " +
      "2) Performances and casting, " +
      "3) Cinematography and visual style, " +
      "4) Your overall verdict and star rating out of 5. " +
      "Be insightful and specific.",
    labels: ["production"],
  });

  console.log(`Created version ${v2.version} with labels: ${v2.labels}`);

  // ── Fetch the production version and compile it ───────────────────────────
  const productionPrompt = await langfuse.prompt.get(promptName, {
    label: "production",
    type: "text",
    cacheTtlSeconds: 0, // disable cache so we get the freshly created version
  });

  console.log(
    `Fetched production prompt (version ${productionPrompt.version})`
  );

  const compiled = productionPrompt.compile({
    criticlevel: "expert",
    movie: "Dune 2",
  });

  console.log(`Compiled prompt: ${compiled}`);

  // ── Validate the compiled output ──────────────────────────────────────────
  if (!compiled.includes("expert")) {
    throw new Error('Compiled prompt does not contain "expert"');
  }
  if (!compiled.includes("Dune 2")) {
    throw new Error('Compiled prompt does not contain "Dune 2"');
  }
  if (compiled.includes("{{") || compiled.includes("}}")) {
    throw new Error("Compiled prompt still contains unrendered placeholders");
  }

  // ── Write the log file ────────────────────────────────────────────────────
  const logLines = [
    `Prompt name: ${promptName}`,
    `Staging version: ${v1.version}`,
    `Production version: ${v2.version}`,
    `Compiled prompt: ${compiled}`,
  ];

  const logPath = path.join("/home/user/myproject", "output.log");
  fs.writeFileSync(logPath, logLines.join("\n") + "\n", "utf8");

  console.log(`Log written to ${logPath}`);
  console.log("--- Log contents ---");
  console.log(logLines.join("\n"));

  // Graceful shutdown
  await langfuse.shutdown();
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});

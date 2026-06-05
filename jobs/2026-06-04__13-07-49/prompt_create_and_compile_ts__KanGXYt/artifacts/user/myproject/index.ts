import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";

async function main() {
  const langfuse = new LangfuseClient();

  const zealtRunId = process.env.ZEALT_RUN_ID;
  if (!zealtRunId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const promptName = `movie-critic-text-${zealtRunId}`;

  console.log(`Creating prompt: ${promptName}`);

  // 1. Create Version 1 (baseline) labeled 'staging'
  const promptV1 = await langfuse.prompt.create({
    name: promptName,
    prompt: "I am a movie critic. As an {{criticlevel}}, I think the movie {{movie}} is...",
    type: "text",
    labels: ["staging"],
  });
  const stagingVersion = promptV1.version;
  console.log(`Created version ${stagingVersion} with label 'staging'`);

  // 2. Create Version 2 (improved) labeled 'production'
  const promptV2 = await langfuse.prompt.create({
    name: promptName,
    prompt: "Welcome to the cinema. As a movie {{criticlevel}}, my professional opinion on {{movie}} is that it's a masterpiece.",
    type: "text",
    labels: ["production"],
  });
  const productionVersion = promptV2.version;
  console.log(`Created version ${productionVersion} with label 'production'`);

  // 3. Fetch the production version
  const productionPrompt = await langfuse.prompt.get(promptName, {
    label: "production",
    type: "text",
  });

  // 4. Compile it
  const compiledPrompt = productionPrompt.compile({
    criticlevel: "expert",
    movie: "Dune 2",
  });

  console.log(`Compiled prompt: ${compiledPrompt}`);

  // 5. Write to log file
  const logContent = [
    `Prompt name: ${promptName}`,
    `Staging version: ${stagingVersion}`,
    `Production version: ${productionVersion}`,
    `Compiled prompt: ${compiledPrompt}`,
  ].join("\n");

  const logFilePath = "/home/user/myproject/output.log";
  fs.writeFileSync(logFilePath, logContent);
  console.log(`Log written to ${logFilePath}`);

  await langfuse.shutdown();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

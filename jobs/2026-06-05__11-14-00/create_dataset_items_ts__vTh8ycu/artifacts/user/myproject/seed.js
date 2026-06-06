"use strict";

const { LangfuseClient } = require("@langfuse/client");
const fs = require("fs");
const path = require("path");

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is not set");
  }

  const datasetName = `qa-dataset-${runId}`;

  const langfuse = new LangfuseClient();

  // Create the dataset
  const dataset = await langfuse.api.datasets.create({
    name: datasetName,
    description: "Geography QA seeded by TS SDK",
    metadata: { language: "typescript" },
  });

  console.log(`Created dataset: ${dataset.name} (id: ${dataset.id})`);

  // Define the three QA items
  const items = [
    {
      input: { question: "What is the capital of France?" },
      expectedOutput: { answer: "Paris" },
    },
    {
      input: { question: "What is the capital of Germany?" },
      expectedOutput: { answer: "Berlin" },
    },
    {
      input: { question: "What is the capital of Japan?" },
      expectedOutput: { answer: "Tokyo" },
    },
  ];

  // Create each dataset item
  for (const item of items) {
    await langfuse.api.datasetItems.create({
      datasetName: datasetName,
      input: item.input,
      expectedOutput: item.expectedOutput,
    });
    console.log(`Created item: ${item.input.question}`);
  }

  // Write the log file
  const logPath = path.join(__dirname, "output.log");
  const logContent = [
    `Dataset name: ${dataset.name}`,
    `Dataset ID: ${dataset.id}`,
    `Items created: 3`,
  ].join("\n") + "\n";

  fs.writeFileSync(logPath, logContent, "utf8");
  console.log(`Log written to ${logPath}`);
  console.log(logContent.trim());
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});

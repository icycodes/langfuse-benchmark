import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    throw new Error("ZEALT_RUN_ID environment variable is required");
  }

  const datasetName = `qa-dataset-${runId}`;

  // LangfuseClient picks up LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env
  const langfuse = new LangfuseClient();

  // Create the dataset
  const dataset = await langfuse.api.datasets.create({
    name: datasetName,
    description: "Geography QA seeded by TS SDK",
    metadata: { language: "typescript" },
  });

  console.log(`Created dataset: ${dataset.name} (id: ${dataset.id})`);

  // Define the three items
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

  // Create dataset items
  const createdItems = [];
  for (const item of items) {
    const created = await langfuse.api.datasetItems.create({
      datasetName: dataset.name,
      input: item.input,
      expectedOutput: item.expectedOutput,
    });
    createdItems.push(created);
    console.log(`Created item: ${JSON.stringify(created.input)}`);
  }

  // Write the log file
  const logContent = [
    `Dataset name: ${dataset.name}`,
    `Dataset ID: ${dataset.id}`,
    `Items created: ${createdItems.length}`,
  ].join("\n");

  const logPath = path.join(__dirname, "output.log");
  fs.writeFileSync(logPath, logContent + "\n");
  console.log(`Log written to ${logPath}`);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
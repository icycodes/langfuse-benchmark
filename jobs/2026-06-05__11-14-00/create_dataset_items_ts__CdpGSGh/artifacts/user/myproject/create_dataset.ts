import { LangfuseClient } from "@langfuse/client";
import * as fs from "fs";

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  if (!runId) {
    console.error("ZEALT_RUN_ID environment variable is not set");
    process.exit(1);
  }

  const datasetName = `qa-dataset-${runId}`;
  
  // Authenticate using environment variables automatically
  const langfuse = new LangfuseClient();

  try {
    // Create dataset using langfuse.api as hinted
    const dataset = await langfuse.api.datasets.create({
      name: datasetName,
      description: "Geography QA seeded by TS SDK",
      metadata: { language: "typescript" },
    });

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

    for (const item of items) {
      await langfuse.api.datasetItems.create({
        datasetName: datasetName,
        input: item.input,
        expectedOutput: item.expectedOutput,
      });
    }

    const logContent = [
      `Dataset name: ${datasetName}`,
      `Dataset ID: ${dataset.id}`,
      `Items created: ${items.length}`,
    ].join("\n") + "\n";

    fs.writeFileSync("/home/user/myproject/output.log", logContent);
    console.log("Dataset and items created successfully.");
  } catch (error) {
    console.error("Error creating dataset or items:", error);
    process.exit(1);
  } finally {
    // Ensure all data is sent before exiting
    await langfuse.shutdown();
  }
}

main();

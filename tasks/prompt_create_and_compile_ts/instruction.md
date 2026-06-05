# Create and Compile a Text Prompt with the Langfuse TypeScript SDK

## Background
You are integrating [Langfuse](https://langfuse.com/) prompt management into a small Node.js TypeScript service that asks an LLM movie-related questions. The service must store its prompt template centrally in Langfuse (so non-engineers can edit it) and pull a labelled version at runtime. Your job is to use the **Langfuse JS/TS SDK** (`@langfuse/client`) to create a versioned **text** prompt, then fetch the `production` version, compile it with concrete variables, and persist both the metadata and the compiled rendering to a log file the team can grep.

The environment already has Node.js (v20+) and TypeScript available. The following environment variables are already exported and must be used by the SDK to talk to Langfuse:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL`

The `ZEALT_RUN_ID` environment variable contains a unique run identifier that you **must** use when naming the Langfuse prompt so concurrent task runs do not collide.

## Requirements
- Build a Node.js + TypeScript project under `/home/user/myproject`.
- Use the `@langfuse/client` package to create a **text** prompt (not chat) with two versions on the Langfuse server:
  - Version 1 (created first) is a baseline template that must be labeled `staging`.
  - Version 2 (created second) is an improved template that must be labeled `production`. (This automatically becomes the default version served when no label is specified.)
- Both versions must reference Langfuse template variables using the double-curly-brace syntax (e.g. `{{criticlevel}}`, `{{movie}}`).
- The prompt name must be `movie-critic-text-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- After creating both versions, fetch the `production` version using the SDK (`langfuse.prompt.get(...)`) and `compile` it with the variables `criticlevel = "expert"` and `movie = "Dune 2"`.
- The compiled (rendered) string must reference `"expert"` and `"Dune 2"` and must **not** contain any remaining unrendered `{{` or `}}` placeholder markers.
- The TypeScript program must be runnable via `npm run start` from the project root.
- Write a log file at `/home/user/myproject/output.log` summarising the result.

## Implementation Hints
- Install the `@langfuse/client` package (>= 4.x) plus `typescript` and `tsx` (or `ts-node`) so `npm run start` can execute the TypeScript entrypoint without a separate compile step.
- Initialise the client with `new LangfuseClient()` — it picks up `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` from the process environment, so do **not** hardcode credentials.
- Create prompts via `langfuse.prompt.create({ name, type: "text", prompt, labels })`. Pass `labels: ["production"]` on the second creation — Langfuse will automatically move that label off the older version.
- Fetch with `langfuse.prompt.get(name, { label: "production", type: "text" })` and call `.compile({ ... })` on the returned object to render variables.
- The returned prompt objects expose a `.version` (integer) property — capture these so you can write them to the log file.
- Remember that `prompt.get` employs an in-process cache; for a short-lived script that creates the prompt and then immediately reads it, simply fetch with the `production` label (Langfuse will return the freshly created v2).
- For graceful shutdown of any background workers, you can call `await langfuse.shutdown()` (or rely on `process.exit(0)`) so the script exits cleanly.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the script is executed end-to-end so the prompt versions actually exist on the Langfuse server. Do **not** mock the Langfuse client.
- The script must be runnable from the project root with `npm run start`.
- The project's `package.json` must declare `@langfuse/client` as a dependency.
- Log file: `/home/user/myproject/output.log`
- The Langfuse prompt name must be `movie-critic-text-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- Two versions of the prompt must exist on the Langfuse server.
- Version 1 must carry the label `staging` and must NOT carry the label `production`.
- Version 2 must carry the label `production`.
- Both versions must be of type `text` (not `chat`) and must contain Langfuse template variables in `{{variable}}` syntax.
- The version 1 prompt body must reference at least `{{criticlevel}}` and `{{movie}}`.
- The version 2 prompt body must reference at least `{{criticlevel}}` and `{{movie}}`.
- Fetching the prompt with no label (default `production`) via the Langfuse API must return version 2.
- The log file must contain the following lines (one per line, in any order, additional content allowed elsewhere in the file):
  - `Prompt name: <prompt_name>`
  - `Staging version: <integer>`
  - `Production version: <integer>`
  - `Compiled prompt: <rendered text>`
- The `Compiled prompt:` line must contain both the substring `expert` and the substring `Dune 2`, and must NOT contain `{{` or `}}` (no unrendered placeholders).


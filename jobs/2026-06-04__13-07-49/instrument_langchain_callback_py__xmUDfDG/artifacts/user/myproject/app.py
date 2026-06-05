import os
import time
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse

# Read ZEALT_RUN_ID from environment
run_id = os.environ["ZEALT_RUN_ID"]

# Build the chain components
fake_model = FakeListChatModel(responses=["Langfuse is an open-source observability platform for LLM applications."])
prompt = ChatPromptTemplate.from_messages([("human", "Tell me a fact about {topic}")])
chain = prompt | fake_model

# Initialize the Langfuse callback handler (picks up credentials from env vars)
handler = CallbackHandler()

# Trace-level attributes passed through metadata
metadata = {
    "langfuse_user_id": f"lc-user-{run_id}",
    "langfuse_session_id": f"lc-session-{run_id}",
    "langfuse_tags": [f"harbor-langchain", f"run-{run_id}"],
}

# Invoke the chain with callback handler, metadata, and run_name
result = chain.invoke(
    {"topic": "langfuse"},
    config={
        "callbacks": [handler],
        "metadata": metadata,
        "run_name": f"langchain-fact-{run_id}",
    },
)

# Capture the trace ID
trace_id = handler.last_trace_id
print(f"Trace ID: {trace_id}")

# Flush Langfuse to ensure all spans are delivered
langfuse = Langfuse()
langfuse.flush()

# Small delay to allow async ingestion
time.sleep(3)

# Write the output log
log_lines = [
    f"Trace ID: {trace_id}",
    f"Trace name: langchain-fact-{run_id}",
    f"User ID: lc-user-{run_id}",
    f"Session ID: lc-session-{run_id}",
    f"Status: OK",
]

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
with open(log_path, "w") as f:
    f.write("\n".join(log_lines) + "\n")

print(f"Log written to {log_path}")
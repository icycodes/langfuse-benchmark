"""
LangChain + Langfuse observability demo.

Builds a small LCEL chain (ChatPromptTemplate → FakeListChatModel) and
instruments it with the Langfuse CallbackHandler.  Trace-level attributes
(user_id, session_id, tags) and run_name are set dynamically per invocation
so concurrent task runs never collide.
"""

import os
import time
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.fake import FakeListChatModel
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

logging.basicConfig(level=logging.WARNING)

# ── Environment ──────────────────────────────────────────────────────────────
RUN_ID = os.environ["ZEALT_RUN_ID"]
LOG_FILE = "/home/user/myproject/output.log"

# ── Langfuse client & callback handler ───────────────────────────────────────
# Credentials / base URL are picked up automatically from the environment:
#   LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
langfuse = Langfuse()
handler = CallbackHandler()

# ── Chain definition ─────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that shares interesting facts."),
    ("human", "Tell me a fact about {topic}."),
])

fake_model = FakeListChatModel(responses=[
    f"Langfuse is an open-source LLM observability platform (run {RUN_ID})."
])

chain = prompt | fake_model

# ── Dynamic per-invocation trace attributes ───────────────────────────────────
run_name = f"langchain-fact-{RUN_ID}"

config = {
    "run_name": run_name,          # sets the Langfuse trace name
    "callbacks": [handler],
    "metadata": {
        "langfuse_user_id":    f"lc-user-{RUN_ID}",
        "langfuse_session_id": f"lc-session-{RUN_ID}",
        "langfuse_tags":       ["harbor-langchain", f"run-{RUN_ID}"],
    },
}

# ── Invoke ────────────────────────────────────────────────────────────────────
print(f"Invoking chain with run_name={run_name!r} …")
result = chain.invoke({"topic": "langfuse"}, config=config)
print(f"Chain output: {result.content!r}")

# ── Retrieve trace ID ─────────────────────────────────────────────────────────
trace_id = handler.last_trace_id
print(f"Trace ID: {trace_id}")

# ── Flush – ingestion is asynchronous ─────────────────────────────────────────
langfuse.flush()
print("Langfuse client flushed.")

# Give the server a moment to become consistent before we write the log.
time.sleep(3)

# ── Write log file ────────────────────────────────────────────────────────────
lines = [
    f"Trace ID: {trace_id}",
    f"Trace name: {run_name}",
    f"User ID: lc-user-{RUN_ID}",
    f"Session ID: lc-session-{RUN_ID}",
    "Status: OK",
]

with open(LOG_FILE, "w") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"Log written to {LOG_FILE}")
for line in lines:
    print(f"  {line}")

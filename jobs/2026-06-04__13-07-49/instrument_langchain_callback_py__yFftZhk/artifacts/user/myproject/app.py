import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.fake import FakeListChatModel
from langfuse.langchain import CallbackHandler

def main():
    zealt_run_id = os.environ.get("ZEALT_RUN_ID")
    if not zealt_run_id:
        # For local testing if ZEALT_RUN_ID is not set, but in the target env it should be there.
        zealt_run_id = "test-run"
    
    # Initialize the Langfuse CallbackHandler
    # It picks up credentials from environment variables:
    # LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
    handler = CallbackHandler()
    
    # Construct the LangChain chain
    # 1. ChatPromptTemplate that takes a single variable 'topic'
    prompt = ChatPromptTemplate.from_template("Tell me a fact about {topic}")
    
    # 2. Fake chat model that returns a deterministic answer
    model = FakeListChatModel(responses=["Langfuse provides open-source observability for LLM applications, including tracing, prompt management, and evaluation."])
    
    # Combine into a chain using LCEL
    chain = prompt | model
    
    # Define trace-level attributes
    user_id = f"lc-user-{zealt_run_id}"
    session_id = f"lc-session-{zealt_run_id}"
    tags = ["harbor-langchain", f"run-{zealt_run_id}"]
    run_name = f"langchain-fact-{zealt_run_id}"
    
    # Invoke the chain
    # metadata keys: langfuse_user_id, langfuse_session_id, langfuse_tags
    # run_name: sets the trace name
    chain.invoke(
        {"topic": "langfuse"},
        config={
            "callbacks": [handler],
            "metadata": {
                "langfuse_user_id": user_id,
                "langfuse_session_id": session_id,
                "langfuse_tags": tags
            },
            "run_name": run_name
        }
    )
    
    # Capture the resulting Langfuse trace ID
    trace_id = handler.last_trace_id
    
    # Flush the Langfuse client to ensure all data is sent before exiting
    if hasattr(handler, 'flush'):
        handler.flush()
    elif hasattr(handler, 'langfuse') and hasattr(handler.langfuse, 'flush'):
        handler.langfuse.flush()
    
    # Persist results to log file
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
        f.write(f"Trace name: {run_name}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Status: OK\n")

if __name__ == "__main__":
    main()

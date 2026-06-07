import os
from langfuse import Langfuse

langfuse = Langfuse()

trace_id = open("/home/user/myproject/output.log").read().strip().split(": ")[1]

trace = langfuse.get_trace(trace_id)
print("Trace name:", trace.name)

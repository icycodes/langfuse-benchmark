import os
import re
from langfuse import Langfuse

def mask_pii(data):
    if isinstance(data, str):
        # Credit card (13-19 digits, optionally separated by spaces or dashes)
        data = re.sub(r'\b(?:\d[ -]*){12,18}\d\b', '[REDACTED CREDIT CARD]', data)
        
        # Phone number NNN-NNN-NNNN (with -, ., or space)
        data = re.sub(r'\b\d{3}[- .]\d{3}[- .]\d{4}\b', '[REDACTED PHONE]', data)
        
        # Email
        data = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED EMAIL]', data)
        return data
    elif isinstance(data, dict):
        return {k: mask_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_pii(v) for v in data]
    return data

def main():
    langfuse = Langfuse(mask=mask_pii)
    
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    trace_name = f"mask-demo-{run_id}"
    
    root_input = "Contact test@example.com or 123-456-7890. Payment: 1234-5678-9012-3456."
    root_output = "Processed test@example.com, 123-456-7890, 1234-5678-9012-3456."

    trace_id = None
    
    with langfuse.start_as_current_observation(
        name=trace_name,
        input=root_input,
        output=root_output
    ) as root_span:
        trace_id = langfuse.get_current_trace_id()
        
        # Set trace IO directly as well for legacy compatibility
        root_span.set_trace_io(input=root_input, output=root_output)
        
        with root_span.start_as_current_observation(
            name="child-generation",
            as_type="generation",
            input="Child input: another@example.com",
            output="Child output: 987.654.3210"
        ) as generation:
            pass
            
    langfuse.flush()
    
    with open("/home/user/myproject/output.log", "w") as f:
        f.write(f"Trace ID: {trace_id}\n")

if __name__ == "__main__":
    main()

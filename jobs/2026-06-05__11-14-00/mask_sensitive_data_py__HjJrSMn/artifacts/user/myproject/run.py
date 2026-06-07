import os
import re
import logging
import time
from langfuse import Langfuse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mask_pii(data):
    """
    Recursively mask PII in string, list, or dict data.
    """
    if isinstance(data, str):
        # 1. Email addresses
        # Simple regex for email: characters@characters.domain
        data = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED EMAIL]', data)
        
        # 2. North American phone numbers: NNN-NNN-NNNN (with -, ., or space)
        # Matches 555-555-5555, 555.555.5555, 555 555 5555
        data = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', '[REDACTED PHONE]', data)
        
        # 3. 13-19 digit credit-card numbers (groups optionally separated by spaces or dashes)
        # We'll look for sequences of digits and separators that total 13-19 digits.
        def cc_replacer(match):
            full_match = match.group(0)
            # Remove separators to count digits
            digits_only = re.sub(r'[-.\s]', '', full_match)
            if 13 <= len(digits_only) <= 19:
                return '[REDACTED CREDIT CARD]'
            return full_match

        # Matches sequences of digits potentially separated by - or space
        # Ensuring it starts and ends with a digit and has enough digits.
        data = re.sub(r'\b(?:\d[-.\s]?){12,18}\d\b', cc_replacer, data)
        
        return data
    elif isinstance(data, list):
        return [mask_pii(item) for item in data]
    elif isinstance(data, dict):
        return {k: mask_pii(v) for k, v in data.items()}
    else:
        return data

def main():
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    trace_name = f"mask-demo-{run_id}"
    
    # Initialize Langfuse with custom mask function
    langfuse = Langfuse(
        public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
        host=os.environ.get("LANGFUSE_BASE_URL"),
        mask=mask_pii
    )

    # PII Data
    email = "customer@example.com"
    phone = "555-019-9999"
    cc = "1234-5678-9012-3456"
    
    # Requirements: input and output contain at least one email address, one phone number, and one credit-card number
    input_pii = f"Contact me at {email} or {phone}. My CC is {cc}."
    output_pii = f"Acknowledged. We have {email}, {phone}, and {cc} on file."

    # Using the context manager approach
    # Root observation (span)
    with langfuse.start_as_current_observation(
        name=trace_name,
        as_type="span",
        input=input_pii,
        output=output_pii,
    ):
        # Get Trace ID
        trace_id = langfuse.get_current_trace_id()
        
        # Child generation
        # Requirement: its input and output must also contain at least one of the PII types above
        with langfuse.start_as_current_observation(
            name="pii-generation",
            as_type="generation",
            input={"user_message": f"Help with {email}"},
            output={"response": f"Sent update to {email} and verified phone {phone}"},
        ):
            pass

    # Flush events to ensure data is persisted server-side
    langfuse.flush()
    
    # Write to log file in exact format: Trace ID: <trace_id>
    log_path = "/home/user/myproject/output.log"
    with open(log_path, "w") as f:
        f.write(f"Trace ID: {trace_id}\n")
    
    print(f"Successfully recorded trace {trace_id}")

if __name__ == "__main__":
    main()

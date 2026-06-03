Langfuse allows teams to centrally manage and version prompts outside of the application codebase to enable rapid iteration.

You need to write a Python function that retrieves a production prompt template named `"customer-support"` from Langfuse, injects runtime variables, and returns the final compiled prompt string.

**Constraints:**
- Must fetch the prompt using the `langfuse.get_prompt("customer-support")` method.
- Must use the prompt object's `.compile()` method to inject a runtime variable named `user_issue`.
- Do NOT hardcode any prompt template text within the Python file itself.
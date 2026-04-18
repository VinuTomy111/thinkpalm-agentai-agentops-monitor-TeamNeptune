import logging
import json
from typing import Any, Dict
from groq import AsyncGroq

from .base_agent import BaseAgent
from core.config import get_settings

logger = logging.getLogger(__name__)

class CodeReviewAgent(BaseAgent):
    """
    An agent that reviews code using Groq-hosted models.
    It integrates a mock lint tool and returns a specialized code review block.
    """
    def __init__(self, name: str = "CodeReviewAgent", model_name: str = "llama-3.1-8b-instant"):
        super().__init__(name)
        settings = get_settings()
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
        api_key = settings.GROQ_API_KEY.strip()
        logger.info(
            "Agent '%s': Initializing Groq client with key prefix '%s' (len=%d).",
            self.name,
            api_key[:8],
            len(api_key),
        )
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = model_name

    def _mock_lint_tool(self, code: str) -> str:
        """A simple mock linter for tool integration demonstration."""
        if "print" in code:
            return "Linter Warning: Found 'print' statements. Consider using logging module for production code."
        elif "TODO" in code or "FIXME" in code:
            return "Linter Warning: Code contains unresolved TODO or FIXME comments."
        return "Linter passing: No obvious static issues detected."

    async def _execute(self, code: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes the code review process.
        """
        # Requirement: Log start
        logger.info(f"Agent '{self.name}': Starting code review for the provided code limit...")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "lint_code",
                    "description": "Lint the code to find static code analysis warnings. Note: use this before finalizing the review.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The python code string to lint"
                            }
                        },
                        "required": ["code"],
                    },
                }
            }
        ]

        messages = [
            {
                "role": "system",
                "content": """You are an expert Python Code Review Agent. 
You will review the user's code, ALWAYS call the 'lint_code' tool to identify static analysis warnings if possible, and provide a final review. 
Your final response MUST be a JSON object strictly following this structure:
{
    "issues": ["list of identified issues..."],
    "suggestions": ["list of improvement suggestions..."]
}"""
            },
            {"role": "user", "content": f"Please review the following code:\n\n{code}"}
        ]

        # First LLM call, letting it decide whether to invoke tools
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        final_content = response_message.content

        internal_trace = []
        # Handle tool calls if any
        if response_message.tool_calls:
            # Append the assistant's action to messages
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "lint_code":
                    # Requirement: Log tool usage
                    logger.info(f"Agent '{self.name}': Using tool '{tool_call.function.name}'")
                    internal_trace.append(f"Tool Invoked: {tool_call.function.name}")
                    
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        lint_result = self._mock_lint_tool(arguments.get("code", ""))
                        logger.info(f"Agent '{self.name}': Tool '{tool_call.function.name}' returned: {lint_result}")
                    except Exception as e:
                        lint_result = f"Error running lint_code tool: {e}"
                        logger.warning(f"Agent '{self.name}': {lint_result}")
                        internal_trace.append(f"Tool Fault: {str(e)[:20]}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": lint_result
                    })

            # Second LLM call to get final JSON output after tools executed
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"}
            )
            final_content = response.choices[0].message.content

        # Requirement: Log output
        logger.info(f"Agent '{self.name}': Code review completed. Raw generation output: {final_content}")
        
        # Parse and return JSON coupled tightly with trace data
        try:
            return {"data": json.loads(final_content), "trace": internal_trace}
        except json.JSONDecodeError:
            logger.error(f"Agent '{self.name}': Failed to parse LLM output as JSON.")
            return {"data": {"issues": ["Error formatting response as JSON."], "suggestions": ["Consider reviewing agent logs."]}, "trace": internal_trace}

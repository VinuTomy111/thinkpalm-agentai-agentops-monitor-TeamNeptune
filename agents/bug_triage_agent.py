import logging
import json
from typing import Any, Dict
from groq import AsyncGroq
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class BugTriageAgent(BaseAgent):
    """
    An agent that analyzes bug descriptions using an LLM.
    It returns a structured JSON response identifying root cause, severity, and a possible fix.
    """
    def __init__(self, name: str = "BugTriageAgent", model_name: str = "llama-3.1-8b-instant"):
        super().__init__(name)
        # Assumes GROQ_API_KEY is available in the environment variables
        self.client = AsyncGroq() 
        self.model_name = model_name

    async def _execute(self, bug_description: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes the bug triage process.
        """
        logger.info(f"Agent '{self.name}': Starting bug triage for provided description...")

        messages = [
            {
                "role": "system",
                "content": """You are an expert technical Bug Triage Agent.
You will analyze the user's bug description and determine its root cause, severity, and propose a viable fix.
Your response MUST be a valid JSON object strictly adhering to this structure:
{
    "root_cause": "A concise explanation of the underlying problem creating the bug",
    "severity": "LOW, MEDIUM, HIGH, or CRITICAL",
    "possible_fix": "A conceptual explanation or code snippet illustrating how to resolve the issue"
}"""
            },
            {"role": "user", "content": f"Please triage this bug report:\n\n{bug_description}"}
        ]

        logger.info(f"Agent '{self.name}': Requesting inference from the LLM...")
        
        # Call LLM and enforce structured JSON out
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        final_content = response.choices[0].message.content
        logger.info(f"Agent '{self.name}': Triage analysis completed. Raw generated output: {final_content}")
        
        # Parse output securely
        try:
            return json.loads(final_content)
        except json.JSONDecodeError as e:
            logger.error(f"Agent '{self.name}': Failed to parse LLM output as JSON. Error: {e}")
            return {
                "root_cause": "Failed to parse generation from LLM.",
                "severity": "UNKNOWN",
                "possible_fix": "Consider reviewing agent execution logs."
            }

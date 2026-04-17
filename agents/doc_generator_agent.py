import logging
import json
from typing import Any, Dict
from groq import AsyncGroq
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DocGeneratorAgent(BaseAgent):
    """
    An agent that generates code documentation using an LLM.
    It returns a structured JSON response including a concise function description, parameter definitions, and a usage example.
    """
    def __init__(self, name: str = "DocGeneratorAgent", model_name: str = "llama-3.1-8b-instant"):
        super().__init__(name)
        # Assumes GROQ_API_KEY is available in the environment variables
        self.client = AsyncGroq() 
        self.model_name = model_name

    async def _execute(self, code_snippet: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes the documentation generation process on the provided code block.
        """
        logger.info(f"Agent '{self.name}': Starting documentation generation for the provided code...")

        messages = [
            {
                "role": "system",
                "content": """You are an expert technical Documentation Generator Agent.
You will analyze the user's software code snippet and generate clear, detailed documentation for it.
Your response MUST be a valid JSON object strictly adhering to this structure:
{
    "function_description": "A clear, concise summary of what the code or core function operates to achieve",
    "parameters": [
        {"name": "param_name", "type": "param type if known", "description": "What this param is used for"}
    ],
    "usage_example": "A short, distinct Python string block illustrating exactly how to use the function or code block"
}"""
            },
            {"role": "user", "content": f"Please explicitly generate standard documentation for this code:\n\n{code_snippet}"}
        ]

        logger.info(f"Agent '{self.name}': Requesting inference and structural mapping from the LLM...")
        
        # Call LLM and securely enforce structured JSON rendering
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        final_content = response.choices[0].message.content
        logger.info(f"Agent '{self.name}': Documentation analysis completed. Raw generated output: {final_content}")
        
        # Parse output properly 
        try:
            return json.loads(final_content)
        except json.JSONDecodeError as e:
            logger.error(f"Agent '{self.name}': Failed to cleanly parse LLM response payload as JSON. Exception: {e}")
            return {
                "function_description": "Failed to parse generation from LLM safely.",
                "parameters": [],
                "usage_example": "Error parsing output; view agent system logs."
            }

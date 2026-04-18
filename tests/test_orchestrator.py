import asyncio
import logging
from dotenv import load_dotenv
import os
import pytest

# Set up standard format logging to standard out
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load variables
load_dotenv()

from agents.coordinator_agent import CoordinatorAgent

@pytest.mark.asyncio
async def test_agent_flows():
    print(f"Groq Key Present: {bool(os.getenv('GROQ_API_KEY'))}")
    
    # Initialize our Coordinator that wraps LangGraph and the sub-agents
    coordinator = CoordinatorAgent()

    print("\n" + "="*50)
    print("TEST 1: Demonstrating the Code Flow logic")
    print("="*50)
    
    code_prompt = """
Please review this code and generate documentation.
```python
def sum_numbers(a, b):
    # TODO: Add validation
    print('Calculating...')
    return a + b
```
"""
    result_code = await coordinator.run(code_prompt)
    
    print("\n--- TEST 1 FINAL TRACE ---")
    print(result_code.get("execution_trace"))
    print("\n--- TEST 1 RESULTS ARRAY ---")
    import json
    print(json.dumps(result_code.get("results", {}), indent=2))
    

    print("\n" + "="*50)
    print("TEST 2: Demonstrating the Bug Triage logic")
    print("="*50)
    
    bug_prompt = "There is a critical bug where the database connection drops silently without attempting to reconnect."
    result_bug = await coordinator.run(bug_prompt)
    
    print("\n--- TEST 2 FINAL TRACE ---")
    print(result_bug.get("execution_trace"))
    print("\n--- TEST 2 RESULTS ARRAY ---")
    print(json.dumps(result_bug.get("results", {}), indent=2))

if __name__ == "__main__":
    asyncio.run(test_agent_flows())

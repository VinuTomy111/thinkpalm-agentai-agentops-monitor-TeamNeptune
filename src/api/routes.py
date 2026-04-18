from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from services.agent_service import AgentService

# Instantiate a single service instance so the underlying MemoryStore dictionary 
# properly maintains state cache globally throughout the uvicorn runtime lifecycle.
agent_service = AgentService()

router = APIRouter()

# --- Pydantic Data Models ---

class CodeAnalyzeRequest(BaseModel):
    code: str

class BugAnalyzeRequest(BaseModel):
    bug_description: str

# --- API Endpoints ---

@router.post("/analyze-code", summary="Analyze Python code via Agents")
async def analyze_code_endpoint(request: CodeAnalyzeRequest):
    """
    Ingests python code, forces a targeted 'code' routing keyword, and 
    invokes the orchestration framework returning linting, bug fixes, and documentation parameters.
    """
    # Injecting the keyword 'code' to ensure the CoordinatorAgent's Router node maps correctly
    input_payload = f"Please explicitly analyze this code block:\n\n{request.code}"
    
    result = await agent_service.process_request(input_payload)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error_detail"))
        
    return result

@router.post("/analyze-bug", summary="Triage an abstract software bug")
async def analyze_bug_endpoint(request: BugAnalyzeRequest):
    """
    Maps incoming structured JSON payload fields into a text string forcing the 'bug'
    routing sequence onto the primary LLM pipeline array logic.
    """
    # Injecting the keyword 'bug' to securely map execution states downstream
    input_payload = f"Please analyze this logic bug explicitly:\n\n{request.bug_description}"
    
    result = await agent_service.process_request(input_payload)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error_detail"))
        
    return result

@router.get("/history", summary="Retrieve complete agent logic inference history")
async def get_history_endpoint():
    """
    Direct passthrough endpoint bypassing LLM reasoning logic entirely to map
    against the dictionary memory abstraction node. 
    """
    try:
        # Fetches the array from the internal memory store attached to our singleton
        records = agent_service.memory.get_all()
        return {
            "status": "success",
            "total_records": len(records),
            "history": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetching crash encountered mapping history sequence: {e}")

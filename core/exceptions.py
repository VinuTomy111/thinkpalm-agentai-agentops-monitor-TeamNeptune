from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

class AgentOpsBaseException(Exception):
    """Base exception for all AgentOps application errors."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.metadata = metadata or {}
        self.status_code = status_code

class AgentException(AgentOpsBaseException):
    """Raised when an error occurs during Agent execution or orchestration."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, metadata=metadata, status_code=500)

class ToolException(AgentOpsBaseException):
    """Raised when an external or internal tool fails to execute properly."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, metadata=metadata, status_code=400)

def format_error_response(exc: Exception) -> Dict[str, Any]:
    """
    Helper function to format an exception into a standardized error response dictionary.
    
    Args:
        exc (Exception): The exception to format.
        
    Returns:
        Dict[str, Any]: Formatted error response payload.
    """
    if isinstance(exc, AgentOpsBaseException):
        response = {
            "error": exc.__class__.__name__,
            "message": exc.message,
        }
        # Only inject metadata if truthy to keep responses clean
        if exc.metadata:
            response["metadata"] = exc.metadata
        return response
    
    # Fallback for standard Python exceptions and unexpected faults
    return {
        "error": "InternalServerError",
        "message": str(exc),
        "metadata": {}
    }

async def agentops_exception_handler(request: Request, exc: AgentOpsBaseException) -> JSONResponse:
    """
    FastAPI handler to catch AgentOpsBaseException subtypes and return them over HTTP.
    """
    payload = format_error_response(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=payload
    )

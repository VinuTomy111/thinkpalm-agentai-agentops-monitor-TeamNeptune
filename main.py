"""
Main FastAPI application setup and entry point.
"""

import sys
import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings
from core.logging import get_logger
from core.exceptions import AgentOpsBaseException, agentops_exception_handler

from api.routes import router as api_router

# Initialize settings and logging bindings
settings = get_settings()
logger = get_logger(__name__)

# --- Middlewares ---

class RequestIDLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects a distinct UUID into every HTTP request sequence
    to seamlessly log inputs, processing duration, and final completion states.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Cache ID into the request sequence state
        request.state.request_id = request_id
        
        start_time = time.time()
        logger.info(f"Req [{request_id}] INIT: {request.method} {request.url.path}")
        
        try:
            # Shift processing downstream
            response = await call_next(request)
            
            # Attach to headers natively allowing external platforms to trace issues natively
            response.headers["X-Request-ID"] = request_id
            
            process_time = time.time() - start_time
            logger.info(f"Req [{request_id}] DONE: Executed in {process_time:.4f}s with HttpCode {response.status_code}")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Req [{request_id}] FAIL: Fatal chain crash after {process_time:.4f}s. Err: {e}", exc_info=True)
            # We raise so it falls downward into the Exception Handlers.
            raise e


# --- Application Application Factory ---

def create_app() -> FastAPI:
    """
    Application factory mapping routing definitions, middlewares, and exception bindings onto FastAPI.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend API for AgentOps Monitor mapped to explicit LLM LangGraph routers.",
    )

    # 1. Bind structural Middlewares
    app.add_middleware(RequestIDLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Global and Specific exception handlers
    app.add_exception_handler(AgentOpsBaseException, agentops_exception_handler)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global handler catching absolute generic application logic failures securely mapping 500s.
        """
        request_id = getattr(request.state, "request_id", "unknown_fault")
        logger.critical(f"Unhandled Global Fault (Req: {request_id}): {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "request_id": request_id,
                "detail": "An internal system fault occurred preventing resolution."
            }
        )

    # 3. Mount basic system operations
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Service Boot: Spinning up {settings.APP_NAME}.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"Service Terminate: Closing {settings.APP_NAME}.")

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "healthy", "service": settings.APP_NAME}

    # 4. Integrate API logic mapping layers
    app.include_router(api_router, prefix="/api/v1", tags=["Inference Engine"])

    return app

# Expose app module
app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Execute webserver interface
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

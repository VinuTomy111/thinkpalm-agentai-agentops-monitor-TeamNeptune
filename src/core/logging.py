import logging
import sys
import uuid
from contextvars import ContextVar
from core.config import get_settings

# Context variable to store and manage the request ID across async tasks
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestContextFilter(logging.Filter):
    """
    Logging filter that injects the current request_id into every log record.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True

def _setup_logging() -> None:
    """
    Initializes the root configuration for structured logging.
    This sets up formatting and handlers.
    """
    settings = get_settings()
    root_logger = logging.getLogger()
    
    # Prevent duplicate handlers if called multiple times
    if root_logger.hasHandlers():
        return
        
    # Dynamically set level based on config
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Structured format including timestamp, log level, module name, and request_id
    log_format = "%(asctime)s | %(levelname)-8s | req_id:%(request_id)s | [%(name)s] | %(message)s"
    formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())

    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a configured logger instance reusable across the application.
    
    Args:
        name (str): Typically the __name__ of the module requesting the logger.
        
    Returns:
        logging.Logger: The configured logger instance.
    """
    _setup_logging()
    return logging.getLogger(name)

# --- Example Usage ---
if __name__ == "__main__":
    # Simulate a web request by generating a correlation/request ID
    simulated_req_id = str(uuid.uuid4())
    request_id_var.set(simulated_req_id)
    
    # Instantiate logger specific to this module context
    logger = get_logger(__name__)
    
    logger.info("Started processing a new request")
    logger.debug("This payload will be visible if LOG_LEVEL is DEBUG")
    logger.warning("Resource limits are nearing threshold")
    logger.error("Failed to connect to the external LLM provider")

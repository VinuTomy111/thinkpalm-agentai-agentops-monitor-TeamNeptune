import os
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Application settings loaded via python-dotenv.
    """
    APP_NAME: str = os.getenv("APP_NAME", "AgentOps Monitor")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (Singleton pattern utilizing lru_cache).
    """
    return Settings()

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file.
# override=True ensures the project .env key is used even if a stale system/user env var exists.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

class Settings:
    """
    Application settings loaded via python-dotenv.
    """
    APP_NAME: str = os.getenv("APP_NAME", "AgentOps Monitor")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (Singleton pattern utilizing lru_cache).
    """
    return Settings()

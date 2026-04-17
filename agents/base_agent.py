import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents. Designed to be extended by specific agent implementations.
    """
    def __init__(self, name: str):
        self.name = name

    async def run(self, *args, **kwargs) -> Any:
        """
        The main execution wrapper for the agent.
        Includes common logging, error handling logic, and robust execution retries.
        Delegates the actual work to the abstract `_execute` method.
        """
        max_retries = kwargs.pop("max_retries", 2)
        base_delay = 2  # seconds

        logger.info(f"Agent '{self.name}' started running with up to {max_retries} retries permitted.")
        
        import asyncio

        for attempt in range(max_retries + 1):
            try:
                result = await self._execute(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Agent '{self.name}' recovered and finished successfully on retry attempt {attempt}.")
                else:
                    logger.info(f"Agent '{self.name}' finished running successfully.")
                return result
            
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Agent '{self.name}' encountered error (Attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {base_delay}s...")
                    await asyncio.sleep(base_delay)
                else:
                    logger.error(f"Agent '{self.name}' ultimately failed after {max_retries + 1} attempts. Escalating trace: {e}", exc_info=True)
                    raise
    @abstractmethod
    async def _execute(self, *args, **kwargs) -> Any:
        """
        Subclasses must implement this method to define their specific execution logic.
        """
        pass

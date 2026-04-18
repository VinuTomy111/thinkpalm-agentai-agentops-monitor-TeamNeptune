import logging
from typing import Dict, Any

from agents.coordinator_agent import CoordinatorAgent
from memory.memory_store import MemoryStore

logger = logging.getLogger(__name__)

class AgentService:
    """
    Core service abstraction to marry the orchestration router (LangGraph)
    and output storage database architectures safely away from root API logic.
    """
    def __init__(self):
        # Initialize internal state modules
        self.coordinator = CoordinatorAgent()
        
        # Instantiate memory node singleton relative to this service instance
        self.memory = MemoryStore()
        
        logger.info("[AgentService] Service logic layer safely instantiated.")

    async def process_request(self, input_text: str) -> Dict[str, Any]:
        """
        Validates the initial string structure, bridges to the agent executor, 
        maintains persistence over failures or success arrays, and maps final return blocks.
        """
        logger.info(f"[AgentService] Ingesting request payload explicitly: '{input_text[:60]}...'")
        
        try:
            # 1. Invoke deep logic workflow (Coordinator wraps -> LangGraph routes -> BaseAgent wraps LLM)
            result_state = await self.coordinator.run(input_text)
            
            execution_trace = result_state.get('execution_trace', [])
            payload_results = result_state.get('results', {})
            
            # 2. Persist safe execution output states actively onto memory node ID layer
            memory_id = self.memory.save(input_data=input_text, output_data={
                "execution_trace": execution_trace,
                "results": payload_results
            })
            
            logger.info(f"[AgentService] Processing successfully completed. Trace mapped to ID: {memory_id}.")
            
            # 3. Format and return to presentation layer 
            return {
                "status": "success",
                "memory_id": memory_id,
                "execution_trace": execution_trace,
                "results": payload_results
            }

        except Exception as e:
            # Actively capture cascading issues failing through orchestration
            error_message = f"Orchestration failure encountered: {e}"
            logger.error(f"[AgentService] {error_message}", exc_info=True)
            
            # Construct partial retention object for audit logging later if tracing crashes
            crashed_memory_id = self.memory.save(input_data=input_text, output_data={"error": error_message})
            
            return {
                "status": "error",
                "memory_id": crashed_memory_id,
                "error_detail": error_message,
                "execution_trace": ["crashed_execution_state"]
            }

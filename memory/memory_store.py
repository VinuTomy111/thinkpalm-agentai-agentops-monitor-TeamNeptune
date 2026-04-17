import logging
import difflib
import uuid
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MemoryStore:
    """
    A lightweight, strictly in-memory data store utilized to retain and index
    inputs and outputs from various agent inference executions and tool uses.
    """
    def __init__(self):
        # Dictionary structure offers fast ID lookups
        self._store: Dict[str, Dict[str, Any]] = {}
        logger.info("[MemoryStore] Initialized fresh in-memory data storage index.")

    def save(self, input_data: str, output_data: Any) -> str:
        """
        Stores an input/output payload array and issues a unique lookup string identifier.
        """
        record_id = str(uuid.uuid4())
        self._store[record_id] = {
            "id": record_id,
            "input": input_data,
            "output": output_data
        }
        logger.info(f"[MemoryStore] Captured and secured new memory layer record under ID: {record_id}")
        return record_id

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Fetches the complete linear history array of the agent orchestration session.
        """
        logger.info(f"[MemoryStore] Fulfilling get_all lookup. Total memory node records: {len(self._store)}.")
        return list(self._store.values())

    def search_similar(self, query: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Cross-checks stored memory nodes against the new textual input utilizing python's 
        native lexical sequence matcher configuration for similarity abstraction. 
        """
        logger.info(f"[MemoryStore] Initiating structural similarity abstraction search across database. Match threshold: {threshold}.")
        
        results = []
        for record in self._store.values():
            stored_input_str = str(record.get("input", ""))
            
            # Using SequenceMatcher to get a rough native percentage mapping (0.0 to 1.0)
            ratio = difflib.SequenceMatcher(None, query.lower(), stored_input_str.lower()).ratio()
            
            if ratio >= threshold:
                results.append({
                    "record": record, 
                    "score": ratio
                })
        
        # Sort structurally by the closest contextual match ratio first
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"[MemoryStore] Similarity search successfully extracted {len(results)} mapping matches.")
        
        # Cleanly unpack sorted array list dynamically
        return [res["record"] for res in results]

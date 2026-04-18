import logging
import operator
from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END

from .base_agent import BaseAgent
from .code_review_agent import CodeReviewAgent
from .doc_generator_agent import DocGeneratorAgent
from .bug_triage_agent import BugTriageAgent

logger = logging.getLogger(__name__)

def dict_merge(left: dict, right: dict) -> dict:
    if not left: left = {}
    if not right: right = {}
    return {**left, **right}

# TypedDict manages the structure of the data flowing across graph nodes
class GraphState(TypedDict):
    input_text: str
    results: Annotated[Dict[str, Any], dict_merge]
    # operator.add informs LangGraph to continuously append to this list automatically
    execution_trace: Annotated[List[str], operator.add]

class CoordinatorAgent(BaseAgent):
    """
    Coordinator agent orchestrating specialized sub-agents based on the keyword input.
    """
    def __init__(self, name: str = "CoordinatorAgent"):
        super().__init__(name)
        # Initialize specialized sub-agents
        self.code_review_agent = CodeReviewAgent()
        self.doc_generator_agent = DocGeneratorAgent()
        self.bug_triage_agent = BugTriageAgent()
        
        # Compile runtime graph
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the directed StateGraph for conditionally routing executions."""
        workflow = StateGraph(GraphState)

        # Register nodes (discrete action steps in the graph)
        workflow.add_node("router_node", self._router_node)
        workflow.add_node("code_flow_splitter", self._code_flow_splitter_node)
        workflow.add_node("code_review_node", self._code_review_node)
        workflow.add_node("doc_generator_node", self._doc_generator_node)
        workflow.add_node("bug_triage_node", self._bug_triage_node)

        # The workflow start
        workflow.set_entry_point("router_node")

        # 1. Routing decision edges
        workflow.add_conditional_edges(
            "router_node",
            self._decide_routing,
            {
                "code_flow": "code_flow_splitter",
                "bug_flow": "bug_triage_node",
                "unknown": END
            }
        )

        # 2. Parallel fan-out for code path
        workflow.add_edge("code_flow_splitter", "code_review_node")
        workflow.add_edge("code_flow_splitter", "doc_generator_node")
        
        # Terminate code nodes natively mapped in parallel
        workflow.add_edge("code_review_node", END)
        workflow.add_edge("doc_generator_node", END)

        # 3. Hard links for bug triage logic
        workflow.add_edge("bug_triage_node", END)

        return workflow.compile()

    # --- Langgraph Route Decision & Node logic ---

    async def _router_node(self, state: GraphState):
        """Analyzes input implicitly and adds to trace before edges move on."""
        return {"execution_trace": ["router_analyzed"]}

    def _decide_routing(self, state: GraphState) -> str:
        """Determines flow based exclusively on input logic text."""
        input_text = state.get("input_text", "").lower()
        
        if "code" in input_text:
            logger.info(f"[{self.name}] Routing Check: Keyword 'code' detected -> Forwarding to parallel code branching.")
            return "code_flow"
        elif "bug" in input_text:
            logger.info(f"[{self.name}] Routing Check: Keyword 'bug' detected -> Forwarding to bug sequence.")
            return "bug_flow"
        
        logger.warning(f"[{self.name}] Routing Check: No keywords recognized. Ending execution flow.")
        return "unknown"

    async def _code_flow_splitter_node(self, state: GraphState):
        """
        Intermediary node enforcing LangGraph execution environments to natively split 
        downstream edges concurrently without blocking constraints.
        """
        logger.info(f"[{self.name}] Splitting workflow path into concurrent independent agent node executions.")
        return {"execution_trace": ["parallel_fan_out_initiated"]}

    async def _code_review_node(self, state: GraphState):
        logger.info(f"[{self.name}] Invoking sub-agent CodeReviewAgent.")
        result = await self.code_review_agent.run(state["input_text"])
        
        node_trace = ["CodeReviewAgent: started"]
        if isinstance(result, dict) and "trace" in result:
            node_trace.extend([f"CodeReviewAgent: {t}" for t in result["trace"]])
            data = result.get("data", result)
        else:
            data = result
        node_trace.append("CodeReviewAgent: completed")
        
        return {
            "results": {"code_review": data}, 
            "execution_trace": node_trace
        }

    async def _doc_generator_node(self, state: GraphState):
        logger.info(f"[{self.name}] Invoking sub-agent DocGeneratorAgent.")
        result = await self.doc_generator_agent.run(state["input_text"])
        
        node_trace = ["DocGeneratorAgent: started"]
        if isinstance(result, dict) and "trace" in result:
            node_trace.extend([f"DocGeneratorAgent: {t}" for t in result["trace"]])
            data = result.get("data", result)
        else:
            data = result
        node_trace.append("DocGeneratorAgent: completed")
        
        return {
            "results": {"doc_generator": data},
            "execution_trace": node_trace
        }

    async def _bug_triage_node(self, state: GraphState):
        logger.info(f"[{self.name}] Invoking sub-agent BugTriageAgent.")
        result = await self.bug_triage_agent.run(state["input_text"])
        
        node_trace = ["BugTriageAgent: started"]
        if isinstance(result, dict) and "trace" in result:
            node_trace.extend([f"BugTriageAgent: {t}" for t in result["trace"]])
            data = result.get("data", result)
        else:
            data = result
        node_trace.append("BugTriageAgent: completed")
        
        return {
            "results": {"bug_triage": data},
            "execution_trace": node_trace
        }

    # --- Core Subclass Execution Wrapper --- 

    async def _execute(self, input_text: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Manages state entry parameters explicitly configured for graph routing.
        """
        logger.info(f"[{self.name}] Orchestrating inference across the pipeline...")
        
        initial_state = {
            "input_text": input_text,
            "results": {},
            "execution_trace": ["execution_started"]
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        logger.info(f"[{self.name}] Final graph execution trace: {final_state.get('execution_trace')}.")
        
        return {
            "execution_trace": final_state.get("execution_trace", []),
            "results": final_state.get("results", {})
        }

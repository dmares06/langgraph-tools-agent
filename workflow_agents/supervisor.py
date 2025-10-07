# workflow_agents/supervisor.py
"""
Supervisor Agent - Routes requests to specialized workflow agents.
"""

import logging
from typing import Literal
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from workflow_agents.config import config
from workflow_agents.constants import SUPERVISOR_PROMPT
from workflow_agents.state import WorkflowAgentState
from workflow_agents.agents.builder import invoke_builder_agent
from workflow_agents.agents.validator import invoke_validator_agent
from workflow_agents.agents.explainer import invoke_explainer_agent
from workflow_agents.agents.data_mapper import invoke_data_mapper_agent

logger = logging.getLogger(__name__)


# MOVE THIS OUTSIDE - at module level
def route_to_agent(state: WorkflowAgentState) -> Literal["builder", "validator", "explainer", "data_mapper", "end"]:
    """
    Determine which agent should handle the request.
    
    Args:
        state: Current state
        
    Returns:
        Agent name to route to
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # Handle both dict and Message object formats
    if hasattr(last_message, 'content'):
        content = last_message.content
        if isinstance(content, list):
            content = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ])
        content = str(content).lower()
    elif isinstance(last_message, dict):
        content = last_message.get("content", "")
        if isinstance(content, list):
            content = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ])
        content = str(content).lower()
    else:
        content = str(last_message).lower()
    
    # Check for explicit routing hints in state
    if state.get("current_agent"):
        return state["current_agent"]
    
    # Route based on keywords
    if any(word in content for word in [
        "create", "build", "make", "add", "edit", "modify", "update",
        "set up", "new workflow", "automation", "trigger", "action"
    ]):
        return "builder"
    
    if any(word in content for word in [
        "validate", "check", "test", "ready", "activate",
        "errors", "issues", "problems", "fix", "dry run"
    ]):
        return "validator"
    
    if any(word in content for word in [
        "why", "what happened", "explain", "debug", "error",
        "didn't run", "failed", "logs", "history"
    ]):
        return "explainer"
    
    if any(word in content for word in [
        "map", "match", "contact", "find", "lookup",
        "email", "address", "entity"
    ]):
        return "data_mapper"
    
    return "builder"


def create_supervisor_graph():
    """
    Create the Supervisor graph that routes to specialist agents.
    
    Returns:
        Compiled StateGraph
    """
    
    # Initialize supervisor LLM
    supervisor_model = init_chat_model(
        config.model_name,
        temperature=0.3,
        max_tokens=2000
    )
    
    # Supervisor node
    async def supervisor_node(state: WorkflowAgentState):
        """Supervisor analyzes request and routes appropriately."""
        messages = state.get("messages", [])
        
        if not messages:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "Hi! I'm your workflow automation assistant. I can help you create, validate, and debug workflows. What would you like to do?"
                }]
            }
        
        # Get routing decision
        next_agent = route_to_agent(state)
        
        # Track agent history
        agent_history = state.get("agent_history", [])
        agent_history.append(next_agent)
        
        logger.info(f"Supervisor routing to: {next_agent}")
        
        # Update state with routing decision
        return {
            "current_agent": next_agent,
            "agent_history": agent_history
        }
    
    # Build the graph
    workflow = StateGraph(WorkflowAgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("builder", invoke_builder_agent)
    workflow.add_node("validator", invoke_validator_agent)
    workflow.add_node("explainer", invoke_explainer_agent)
    workflow.add_node("data_mapper", invoke_data_mapper_agent)
    
    # Add edges
    workflow.add_edge(START, "supervisor")
    
    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,  # Now this is defined at module level
        {
            "builder": "builder",
            "validator": "validator",
            "explainer": "explainer",
            "data_mapper": "data_mapper",
            "end": END
        }
    )
    
    # All agents return to END
    workflow.add_edge("builder", END)
    workflow.add_edge("validator", END)
    workflow.add_edge("explainer", END)
    workflow.add_edge("data_mapper", END)
    
    # Compile
    graph = workflow.compile()
    
    logger.info("Workflow Supervisor graph compiled")
    
    return graph


# Pre-compiled supervisor instance
workflow_supervisor = create_supervisor_graph()


async def invoke_workflow_supervisor(
    messages: list[dict],
    user_id: str,
    workflow_type: str = "automation",
    flow_id: str | None = None,
    config: dict | None = None
) -> dict:
    """
    Invoke the workflow supervisor with a user request.
    
    Args:
        messages: Conversation messages
        user_id: User UUID
        workflow_type: Type of workflow (automation or pipeline)
        flow_id: Optional workflow ID for context
        config: Optional runtime configuration
        
    Returns:
        Agent response
    """
    # Prepare state
    state = {
        "messages": messages,
        "workflow_type": workflow_type,
        "flow_id": flow_id,
        "user_id": user_id,
        "agent_history": []
    }
    
    # Prepare config
    run_config = config or {}
    if "configurable" not in run_config:
        run_config["configurable"] = {}
    run_config["configurable"]["user_id"] = user_id
    
    try:
        # Invoke supervisor
        result = await workflow_supervisor.ainvoke(state, run_config)
        
        logger.info(f"Supervisor completed. Agent path: {result.get('agent_history')}")
        
        return {
            "success": True,
            "messages": result.get("messages", []),
            "agent_used": result.get("current_agent"),
            "agent_history": result.get("agent_history", [])
        }
        
    except Exception as e:
        logger.error(f"Error in workflow supervisor: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "messages": messages + [{
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}"
            }]
        }
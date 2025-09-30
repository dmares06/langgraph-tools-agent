# tools_agent/utils/integrations/langsmith.py
"""
Complete LangSmith integration for agent observability and tracking.
"""

import os
from typing import Optional, Dict, Any
from langchain.callbacks.manager import CallbackManager
from langsmith import Client
from langchain.callbacks import LangChainTracer

def setup_langsmith() -> Optional[CallbackManager]:
    """
    Set up LangSmith tracing for observability.
    
    Required environment variables:
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=your_langsmith_api_key
    LANGCHAIN_PROJECT=suitecre-agents
    
    Returns:
        CallbackManager with LangSmith tracing or None if not configured
    """
    
    # Check if LangSmith is configured
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("Warning: LANGCHAIN_API_KEY not found. LangSmith tracing disabled.")
        return None
    
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        print("Warning: LANGCHAIN_TRACING_V2 not enabled. Set to 'true' to enable tracing.")
        return None
    
    try:
        # Set up the tracer
        tracer = LangChainTracer(
            project_name=os.getenv("LANGCHAIN_PROJECT", "suitecre-agents")
        )
        
        callback_manager = CallbackManager([tracer])
        
        print(f"LangSmith tracing enabled for project: {os.getenv('LANGCHAIN_PROJECT', 'suitecre-agents')}")
        return callback_manager
        
    except Exception as e:
        print(f"Warning: Failed to set up LangSmith tracing: {str(e)}")
        return None

def create_run_metadata(
    agent_type: str, 
    broker_id: str = None,
    session_id: str = None,
    additional_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create metadata for LangSmith runs to track agent performance.
    
    Args:
        agent_type: Type of agent (chat_copilot, lead_generation, etc.)
        broker_id: ID of the broker using the agent
        session_id: Session identifier for grouping related interactions
        additional_metadata: Additional custom metadata
    
    Returns:
        Dictionary with run metadata
    """
    metadata = {
        "agent_type": agent_type,
        "broker_id": broker_id,
        "session_id": session_id,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0",
        "framework": "langgraph",
        "platform": "suitecre"
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return metadata

def log_agent_interaction(
    agent_type: str,
    interaction_type: str,
    success: bool,
    metadata: Dict[str, Any] = None
):
    """
    Log agent interactions for analytics.
    
    Args:
        agent_type: Type of agent (chat_copilot, lead_generation)
        interaction_type: Type of interaction (tool_call, query_response, etc.)
        success: Whether the interaction was successful
        metadata: Additional metadata to log
    """
    try:
        client = Client()
        
        log_data = {
            "agent_type": agent_type,
            "interaction_type": interaction_type,
            "success": success,
            "timestamp": os.getenv("LANGCHAIN_PROJECT", "suitecre-agents"),
            **(metadata or {})
        }
        
        # This would integrate with LangSmith's logging API
        # For now, just print for debugging
        print(f"Agent Interaction Logged: {log_data}")
        
    except Exception as e:
        print(f"Warning: Failed to log agent interaction: {str(e)}")

# Integration functions for agent.py
def get_langsmith_config() -> Dict[str, Any]:
    """
    Get LangSmith configuration for agent initialization.
    
    Returns:
        Configuration dictionary for LangSmith integration
    """
    return {
        "callbacks": setup_langsmith(),
        "tags": ["suitecre", "commercial-real-estate", "multi-agent"],
        "metadata": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0"
        }
    }

def track_tool_usage(tool_name: str, agent_type: str, execution_time: float, success: bool):
    """
    Track tool usage statistics for performance monitoring.
    
    Args:
        tool_name: Name of the tool that was executed
        agent_type: Type of agent that used the tool
        execution_time: Time taken to execute the tool (in seconds)
        success: Whether the tool execution was successful
    """
    try:
        metadata = {
            "tool_name": tool_name,
            "agent_type": agent_type, 
            "execution_time_seconds": execution_time,
            "success": success
        }
        
        log_agent_interaction(
            agent_type=agent_type,
            interaction_type="tool_execution",
            success=success,
            metadata=metadata
        )
        
    except Exception as e:
        print(f"Warning: Failed to track tool usage: {str(e)}")

def track_agent_performance(
    agent_type: str,
    query_type: str, 
    response_time: float,
    user_satisfaction: Optional[int] = None
):
    """
    Track overall agent performance metrics.
    
    Args:
        agent_type: Type of agent (chat_copilot, lead_generation)
        query_type: Type of query handled (crm_query, document_search, lead_generation)
        response_time: Total response time in seconds
        user_satisfaction: Optional satisfaction score (1-5)
    """
    try:
        metadata = {
            "query_type": query_type,
            "response_time_seconds": response_time,
            "user_satisfaction": user_satisfaction
        }
        
        log_agent_interaction(
            agent_type=agent_type,
            interaction_type="query_response",
            success=True,  # Assume success if we're tracking performance
            metadata=metadata
        )
        
    except Exception as e:
        print(f"Warning: Failed to track agent performance: {str(e)}")

# Example usage patterns for integration:
"""
# In agent.py, when creating agents:
langsmith_config = get_langsmith_config()

agent = create_react_agent(
    prompt=prompt,
    model=model,
    tools=tools,
    callbacks=langsmith_config["callbacks"]
)

# When tracking tool usage:
import time

start_time = time.time()
try:
    result = tool.invoke(args)
    execution_time = time.time() - start_time
    track_tool_usage(tool.name, "chat_copilot", execution_time, True)
except Exception as e:
    execution_time = time.time() - start_time  
    track_tool_usage(tool.name, "chat_copilot", execution_time, False)
"""